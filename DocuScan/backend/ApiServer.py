from flask import Flask,render_template, request, redirect, url_for,jsonify
from flask_cors import CORS, cross_origin
from AzServiceApiLogic import AzServiceApiLogic
from flask_socketio import SocketIO,emit
import asyncio
from semantic_kernel.agents import ChatCompletionAgent
from semantic_kernel.connectors.ai.open_ai import AzureChatCompletion
from azure.core.credentials import AzureKeyCredential
from azure.ai.documentintelligence import DocumentIntelligenceClient
from azure.ai.documentintelligence.models import AnalyzeDocumentRequest
from azure.ai.documentintelligence.models import DocumentAnalysisFeature, AnalyzeResult
from azure.ai.textanalytics import TextAnalyticsClient
from semantic_kernel import Kernel
from semantic_kernel.utils.logging import setup_logging
from semantic_kernel.functions import kernel_function
from semantic_kernel.connectors.ai.open_ai import AzureChatCompletion
from semantic_kernel.connectors.ai.open_ai import OpenAIChatCompletion
from semantic_kernel.data.vector import VectorStoreField, vectorstoremodel
from semantic_kernel.connectors.in_memory import InMemoryCollection
from semantic_kernel.connectors.ai.open_ai import OpenAITextEmbedding
from semantic_kernel.connectors.ai.function_choice_behavior import FunctionChoiceBehavior
from semantic_kernel.connectors.ai.chat_completion_client_base import ChatCompletionClientBase
from semantic_kernel.contents.chat_history import ChatHistory
from semantic_kernel.functions.kernel_arguments import KernelArguments
from agent_framework_foundry_local import FoundryLocalClient
from azure.keyvault.secrets import SecretClient
from azure.identity import DefaultAzureCredential
import requests
import openai
from foundry_local import FoundryLocalManager
from asgiref.sync import async_to_sync
import json
import os

app = Flask(__name__)
app.config['SECRET_KEY'] = 'secret!'
CORS(app,resources={r"/*":{"origins":"*"}})
socketio = SocketIO(app,cors_allowed_origins="*")

@app.route('/api/process-pdf', methods=['POST'])
@cross_origin(origin='*')
def get_data():
    print("Function is called and file is being processed...")
    upload_file = request.files['file']
    print(f"----file with name upload #{upload_file.filename}----")
    json_data = analyze_doc_from_file_using_ocr_send_to_llm(upload_file)
    return json_data

@socketio.on("send_message")
def connected():
    """event listener when client connects to the server"""
    print(request.sid)
    print("client has connected")
    emit("connect",{"data":f"id: {request.sid} is connected"})
    
@socketio.on('data')
def handle_message(data):
    """event listener when client types a message"""
    print("data from the front end: ",str(data))
    emit("data",{'data':data,'id':request.sid},broadcast=True)
    
def analyze_doc_from_file_using_ocr_send_to_llm(filepath):
    # Set your endpoint and key from Key Vault
    endpoint = "http://localhost:5010"
    docIntellkey = retrieve_secret_from_keyvault("DocIntellKey")
    document_intelligence_client = DocumentIntelligenceClient(
        endpoint=endpoint, credential=AzureKeyCredential(key=docIntellkey)
    )
    print(f"----file with name upload #{filepath.filename}----")
    print("Function analyze_doc_from_file_using_ocr_send_to_llm is called and file is being processed...")
   
    #Prepare the API request body
    poller = document_intelligence_client.begin_analyze_document(
        "prebuilt-layout", AnalyzeDocumentRequest(bytes_source=filepath.read()), 
        features=[DocumentAnalysisFeature.KEY_VALUE_PAIRS],
        output_content_format="markdown"
    )
    result = poller.result()
    
    if result.key_value_pairs:
        print("----Key-value pairs found in document----")
        for kv_pair in result.key_value_pairs:
            if kv_pair.key:
                print(f"Key '{kv_pair.key.content}' found within " f"'{kv_pair.key.bounding_regions}' bounding regions")
            if kv_pair.value:
                print(
                    f"Value '{kv_pair.value.content}' found within "
                    f"'{kv_pair.value.bounding_regions}' bounding regions\n"
                )
    table_offsets = []
    full_table_text =""
    if result.tables:
        for table in result.tables:
            table_data = []
            for region in table.bounding_regions:
                page_number = region.page_number
                for cell in table.cells:
                    for span in cell.spans:
                        table_offsets.append(span.offset)
                    table_data.append(f"Cell [{cell.row_index}, {cell.column_index}]: {cell.content}")
                    full_table_text = " ".join(table_data)
    # Process the analysis result for each page
    page_content = []
    for page in result.pages:
        for word in page.words:
           # if  word.span.offset not in table_offsets:
                page_content.append(word.content)
                full_page_text = " ".join(page_content)
                
    print(f"----OCR is Done Countent from pages #{full_page_text}----")
    text_blocks=full_page_text 
    
    #send the extracted text to LLM for analysis and extraction of key-value pairs          
    #json_data = analyze_text_from_doc_llm(text_blocks)
    json_data=agent_framework_analyze_text_from_doc_using_llm(text_blocks)
    print("----------------------------------------")
    return json_data

def analyze_text_from_doc_using_llm(text_block):
        # By using an alias, the most suitable model will be downloaded
        # to your end-user's device.
        print(f"----Countent from pages #{text_block}----")
        alias = "phi-3.5-mini"

        # Create a FoundryLocalManager instance. This will start the Foundry
        # Local service if it is not already running and load the specified model.
        manager = FoundryLocalManager(alias)

        # The remaining code uses the OpenAI Python SDK to interact with the local model.

        # Configure the client to use the local Foundry service
        client = openai.OpenAI(
                base_url=manager.endpoint,
                api_key=manager.api_key  # API key is not required for local usage
                    )

        # Set the model to use and generate a streaming response
        prompt = f"""Hier ist ein Textblock:

        {text_block}

       Extrahiere Entitäten auschließlich nur aus diesem Textblock und gib sie als key-value pair in vollständigJSON-Objekt zurück.
       verwende die folgenden labels: Name der Vertragsparteien-beteiligte, Name der Notar, Adresse der Vertragsparteien-beteiligte, Adresse der Notar, Kaufdatum, UVZ-Nr, Fläche,  Posteingangsdatum. 
       Bitte alle labels vollstädig schreiben. Falls ein label nicht im Textblock gefunden wird, soll es mit einem leeren String als value zurückgegeben werden.
       Kein Doppelungen von labels, falls ein label mehrfach im Textblock gefunden wird, soll es nur einmal im JSON-Objekt auftauchen. Falls label Fläche nicht gefunden wird, soll es mit einem leeren String als value zurückgegeben werden. 
       Bitte gib die Fläche nur in Quadratmetern zurück und verwende dafür die Einheit "m²". Falls die Fläche in einer anderen Einheit angegeben ist, rechne sie bitte in Quadratmeter um. Bitte gib die Fläche als reine Zahl zurück, ohne die Einheit. 
       Alle labels muss in doppelten Anführungszeichen geschrieben werden.Bitte verwenden nur Labels, die ich dir gegeben habe, und keine anderen. Gibt nur das JSON-Objekt zurück und keinen anderen Text oder nummer. Hier ist ein Beispiel, wie das JSON-Objekt aussehen soll:
       {{"Name der Vertragsparteien": "Max Mustermann und Erika Musterfrau", "Name der Notar": "Dr. Manuel Ladiges", "Adresse der Vertragsparteien": "Musterstraße 1, 12345 Musterstadt", "Adresse der Notar": "Notarstraße 2, 54321 Notarstadt", "Kaufdatum": "01.12.2025", "UVZ-Nr": "1465/2025", "Fläche": "150",  "Posteingangsdatum": "16.12.2025"}}"""

        stream = client.chat.completions.create(
            model=manager.get_model_info(alias).id,
            messages=[{"role": "user", "content": prompt }],
            stream=True
        )
        text=""
        # Print the streaming response
        for chunk in stream:
         if chunk.choices[0].delta.content is not None:
           text += chunk.choices[0].delta.content
       
       
        print(text)     
        left_index = text.find('{')
        right_index = text.rfind('}')
        try:
           json_string = text[left_index:right_index+1]
           json_data = json.loads(json_string)
          
        except IndexError:
            print("No json found!")    
        
            print("----------------------------------------")
            return json_data
    
def semnatic_kernel_analyze_text_from_doc_using_llm(text_block):
          # By using an alias, the most suitable model will be downloaded
        # to your end-user's device.
        print(f"----Countent from pages #{text_block}----")
        alias = "phi-3.5-mini"

        # Create a FoundryLocalManager instance. This will start the Foundry
        # Local service if it is not already running and load the specified model.
        manager = FoundryLocalManager(alias)  
        
        kernel = Kernel()
        kernel.register_chat_service( 
            "azure", OpenAIChatCompletion(
                ai_model_id="phi-3.5-mini",
                service_id="phi-3.5-mini",
                api_key=manager.api_key,
                endpoint=manager.endpoint
            )
        )
       
        chat_history = ChatHistory()
        chat_history.add_user_message(text_block)
        response = kernel.chat("azure", chat_history)
        print(response)  
@async_to_sync
async def agent_framework_analyze_text_from_doc_using_llm(text_block):
        # By using an alias, the most suitable model will be downloaded
        # to your end-user's device.
        print(f"----Countent from pages #{text_block}----")
        alias = "phi-3.5-mini"

        # FoundryLocalClient handles service start, model download, and loading
        client = FoundryLocalClient(model=alias)
      

        # Create an agent with system instructions
        agent = client.as_agent(
        name="Data Extraction Agent",
        instructions=(
            "Du bist ein Datenextraktionsagent. "
            f"""Extrahiere Entitäten auschließlich nur aus ein vorgegebenen Textblock und gib sie als key-value pair in vollständig JSON-Objekt mit klammern zurück. 
       verwende die folgenden labels: Name der Vertragsparteien-beteiligte, Name der Notar, Adresse der Vertragsparteien-beteiligte, Adresse der Notar, Kaufdatum, UVZ-Nr, Fläche,  Posteingangsdatum. 
       Bitte alle labels vollstädig schreiben. Falls ein label nicht im Textblock gefunden wird, soll es mit einem leeren String als value zurückgegeben werden.
       Kein Doppelungen von labels, falls ein label mehrfach im Textblock gefunden wird, soll es nur einmal im JSON-Objekt auftauchen.   
       Alle labels muss in doppelten Anführungszeichen geschrieben werden. Bitte verwenden nur Labels, die ich dir gegeben habe, und keine anderen. Gibt nur das JSON-Objekt zurück und keinen anderen Text oder nummer. Hier ist ein Beispiel, wie das JSON-Objekt aussehen soll:"
        {{"Name der Vertragsparteien": "Max Mustermann und Erika Musterfrau", "Name der Notar": "Dr. Manuel Ladiges", "Adresse der Vertragsparteien": "Musterstraße 1, 12345 Musterstadt", "Adresse der Notar": "Notarstraße 2, 54321 Notarstadt", "Kaufdatum": "01.12.2025", "UVZ-Nr": "1465/2025", "Fläche": "150",  "Posteingangsdatum": "16.12.2025"}}"""
        ),
        )
         
        
        # Non-streaming: get the complete response at once
         # result = await agent.run(text_block)
         #result = result.to_json()
        # Streaming: process the response as it arrives
        result = ""
        async for chunk in agent.run(text_block, stream=True):
            if chunk.text:
                result += chunk.text
                #print(chunk.text, end="", flush=True)
        #print("Raw:", result)
        left_index = result.find('{')
        right_index = result.rfind('}')
        try:
            json_string = result[left_index:right_index+1]
            json_data = json.loads(json_string)
          
        except IndexError:
            print("Agent did not return valid JSON - try refining the instructions.")    
        
        print("--------------------------------------------------------")
        print(json_data)
        print("--------------------------------------------------------")
        return json_data

      
def retrieve_secret_from_keyvault(secret_name):
    keyVaultName = os.getenv("KEY_VAULT_NAME")
    key_vault_url =  f"https://{keyVaultName}.vault.azure.net"
    credential = DefaultAzureCredential()
    secret_client = SecretClient(vault_url=key_vault_url, credential=credential)
    secret = secret_client.get_secret(secret_name)
    return secret.value 
# Running app
if __name__ == '__main__':
    socketio.run(app, debug=True, port=8080)