import re

import openai
from foundry_local import FoundryLocalManager
import json

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
text_block="der am 01.12.2025 geschlossene Kaufvertrag, UVZ-Nr. 1465/2025 SB des Notars Dr. Manuel Ladiges, hier eingegangen am 16.12.2025, wird gemäß § 2 Grundstückverkehrsgesetz für die hessische Fläche genehmigt, da ihm Hinderungsgründe nach Maßgabe des Grundstückver- kehrsgesetzes nicht entgegenstehen."
# Set the model to use and generate a streaming response
prompt = f"""Hier ist ein Textblock:

{text_block}

Extrahiere Entitäten aus dem Textblock und gib sie im JSON-Format zurück."""


stream = client.chat.completions.create(
    model=manager.get_model_info(alias).id,
    messages=[{"role": "user", "content": prompt }],
    stream=True
)
text=""
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

        
