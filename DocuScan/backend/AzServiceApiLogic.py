import base64
import os
from urllib import response
from azure.core.credentials import AzureKeyCredential
from azure.ai.documentintelligence import DocumentIntelligenceClient
from azure.ai.documentintelligence.models import AnalyzeDocumentRequest
from azure.ai.documentintelligence.models import DocumentAnalysisFeature, AnalyzeResult
from azure.ai.textanalytics import TextAnalyticsClient
import openai
from foundry_local import FoundryLocalManager
import json
from threading import Lock
class AzServiceApiLogic(object):
   
    def analyze_doc_from_file_ocr(self, filepath):
       # Set your endpoint and key from environment variables
        endpoint = "http://localhost:5010"
        key = "BsxukPSVqD7EkQsHhDgPyCVVJ3JHWw4c3RewnQjhxSSZ9SGlRe7i"
        document_intelligence_client = DocumentIntelligenceClient(
            endpoint=endpoint, credential=AzureKeyCredential(key)
        )
        print(f"----file with name upload #{filepath.filename}----")
        print("Function analyze_doc_from_file_ocr is called and file is being processed...")
        # Analyze a sample document layout using its URL
        #filepath = "C:\\Azure_AI\\schuetzm_260119-101215.pdf"
        with open(filepath, "rb") as file:
            # Prepare the API request body
         poller = document_intelligence_client.begin_analyze_document(
                "prebuilt-layout", AnalyzeDocumentRequest(bytes_source=file.read()), 
                features=[DocumentAnalysisFeature.KEY_VALUE_PAIRS],
                output_content_format="markdown"
            )
        result = poller.result()

        print("----Key-value pairs found in document----")

            # Analyze styles (e.g., whether the document contains handwritten content)
            # Process the analysis result for each page
        #for page in result.pages:
        #  print(f"----Analyzing layout from page #{page.page_number}----")
        #  page_content = []

        # Collect words from the current page
        #for word in page.words:
        #    page_content.append(word.content)

        # Join words to form the complete text of the page
        #full_page_text = " ".join(page_content)

        # Split the text into Markdown blocks
        #markdown_blocks = full_page_text.split("```")

        # Process each Markdown block
        #for i, block in enumerate(markdown_blocks):
        #    if i % 2 != 0:
        #        print(f"Markdown Content (Page {page.page_number}):\n{block}\n")

                # Here, you can add additional processing for paragraphs, tables, images, etc.
                # For example:
                # - Identify paragraphs: split by double newlines
                # - Identify tables: look for table syntax in Markdown
                # - Identify images: look for image syntax in Markdown

        #        paragraphs = block.split('\n\n')
        #        for paragraph in paragraphs:
        #            if paragraph.startswith('|') and paragraph.endswith('|'):
        #                print(f"Table (Page {page.page_number}):\n{paragraph}\n")
        #            elif paragraph.startswith('![') and '](' in paragraph:
        #                print(f"Image (Page {page.page_number}):\n{paragraph}\n")
        #            else:
        #                print(f"Paragraph (Page {page.page_number}):\n{paragraph}\n")

        if result.key_value_pairs:
                for kv_pair in result.key_value_pairs:
                    if kv_pair.key:
                        print(f"Key '{kv_pair.key.content}' found within " f"'{kv_pair.key.bounding_regions}' bounding regions")
                    if kv_pair.value:
                        print(
                            f"Value '{kv_pair.value.content}' found within "
                            f"'{kv_pair.value.bounding_regions}' bounding regions\n"
                        )
        
            # Analyze paragraphs
        if result.paragraphs:
                 table_offsets = []
                 page_content = []

                 for paragraph in result.paragraphs:
                      for span in paragraph.spans:
                         if span.offset not in table_offsets:
                          for region in paragraph.bounding_regions:
                              page_number = region.page_number
                              if page_number not in page_content:
                              # page_content[page_number] = []
                               page_content.append(paragraph.content)
               # self.analyze_text_from_doc(paragraph_content)
                          #self.analyze_text_from_doc_llm(page_content)
                               # By using an alias, the most suitable model will be downloaded
        # to your end-user's device.
        print(f"----Countent from pages #{page_content}----")
        alias = "phi-3.5-mini"

        # Create a FoundryLocalManager instance. This will start the Foundry
        # Local service if it is not already running and load the specified model.
        manager = FoundryLocalManager(alias)

        # The remaining code us es the OpenAI Python SDK to interact with the local model.
        #page_content = "der am 01.12.2025 geschlossene Kaufvertrag, UVZ-Nr. 1465/2025 SB des Notars Dr. Manuel Ladiges, hier eingegangen am 16.12.2025, wird gemäß § 2 Grundstückverkehrsgesetz für die hessische Fläche genehmigt, da ihm Hinderungsgründe nach Maßgabe des Grundstückver- kehrsgesetzes nicht entgegenstehen."

        # Configure the client to use the local Foundry service
        client = openai.OpenAI(
                base_url=manager.endpoint,
                api_key=manager.api_key  # API key is not required for local usage
                    )
        text = ""
        # Set the model to use and generate a streaming response
        prompt = f"""Hier ist ein Textblock:

        {page_content}

        Extrahiere Entitäten aus dem Textblock und gib sie im JSON-Format zurück. verwenden nur diese labels: "Name", "Adresse", "Kaufdatum", "Gemarkung", "Flache", "Notar", "UVZ-Nr.", "Posteingang", "Vertragart"."""


        stream = client.chat.completions.create(
            model=manager.get_model_info(alias).id,
            messages=[{"role": "user", "content": prompt }],
           stream=True
        )
       # Print the streaming response
        for chunk in stream:
         if chunk.choices[0].delta.content is not None:
           text += chunk.choices[0].delta.content
       
        # Print the streaming response
       # for chunk in stream:
        #    if chunk.choices[0].delta.content is not None:
        #         print(chunk.choices[0].delta.content, end="", flush=True)
                #text+=chunk.choices[0].delta.content
        left_index = text.find('{')
        right_index = text.find('}', left_index)
        try:
           json_string = text[left_index:right_index+1]
           json_data = json.loads(json_string)
           print(json_data)
        except IndexError:
            print("No json found!")    
            # Analyze tables
       #     if result.tables:
       #         table_content = parse_tables(result, table_offsets)
                #self.analyze_text_from_doc(table_content)
       #         self.analyze_text_from_doc_llm
        print("----------------------------------------")


    def analyze_text_from_doc(self, documents):
        # settings
        endpointtext = "http://localhost:5021"
        credential = AzureKeyCredential("38iBbELbkiBEZxtLPCZr2ukTzyAtD1eE7IPxjUaKHslbLQIF4yKYJQQJ99CBACPV0roXJ3w3AAAaACOGRcJg")

        text_analytics_client = TextAnalyticsClient(endpoint=endpointtext, credential=credential)
   
        response = text_analytics_client.recognize_entities(documents, language="de")
        result = [doc for doc in response if not doc.is_error]

        for doc in result:
          for entity in doc.entities:
            print("Entity: {}".format(entity.text))
            print("...Category: {}".format(entity.category))
            print("...Confidence Score: {}".format(entity.confidence_score))
            print("...Offset: {}".format(entity.offset))
            
    def analyze_text_from_doc_llm(self, text_block):
            # By using an alias, the most suitable model will be downloaded
        # to your end-user's device.
        alias = "phi-3.5-mini"

        # Create a FoundryLocalManager instance. This will start the Foundry
        # Local service if it is not already running and load the specified model.
        manager = FoundryLocalManager(alias)

        # The remaining code us es the OpenAI Python SDK to interact with the local model.

        # Configure the client to use the local Foundry service
        client = openai.OpenAI(
                base_url=manager.endpoint,
                api_key=manager.api_key  # API key is not required for local usage
                    )

        # Set the model to use and generate a streaming response
        prompt = f"""Hier ist ein Textblock:

        {text_block}

        Extrahiere Entitäten aus dem Textblock und gib sie im JSON-Format zurück."""


        stream = client.chat.completions.create(
            model=manager.get_model_info(alias).id,
            messages=[{"role": "user", "content": prompt }],
            stream=True,response_format={"type": "json_object"}
        )

        # Print the streaming response
        for chunk in stream:
            if chunk.choices[0].delta.content is not None:
                text+=chunk.choices[0].delta.content
        left_index = text.find('{')
        right_index = text.find('}', left_index)
        try:
            json_string = text[left_index:right_index+1]
            json_data = json.loads(json_string)
            print(json_data)
        except IndexError:
            print("No json found!")       
        return json_data

def parse_paragraphs(self, analyze_result):
    table_offsets = []
    page_content = []

    for paragraph in analyze_result.paragraphs:
        if len(page_content) < 5:
            for span in paragraph.spans:
                if span.offset not in table_offsets:
                    for region in paragraph.bounding_regions:
                        page_content.append(paragraph.content)
    
    return page_content, table_offsets

def parse_tables(self, analyze_result, table_offsets):
    page_content = {}

    for table in analyze_result.tables:
        table_data = []
        for region in table.bounding_regions:
            page_number = region.page_number
            for cell in table.cells:
                for span in cell.spans:
                    table_offsets.append(span.offset)
                table_data.append(f"Cell [{cell.row_index}, {cell.column_index}]: {cell.content}")

        if page_number not in page_content:
            page_content[page_number] = []
        
        page_content[page_number].append({
        "content_text": "\n".join(table_data)})
    
    return page_content