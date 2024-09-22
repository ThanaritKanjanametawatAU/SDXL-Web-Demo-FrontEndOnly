import os
from dotenv import load_dotenv
import requests

from api.text2img import default_payload

load_dotenv()
APIBASE = os.environ.get("APIBASE")
url = f"{APIBASE}/sdapi/v1/memory"

# Payload
default_payload = {

}

def get_memory(url=url, payload=default_payload):
    # Sending POST request to the API
    response = requests.post(url, json=payload)

    # Check if the response is successful
    if response.status_code == 200:
        print("Memory retrieved")
        print(f"RAM usage: {response.json()['ram']} MB")
        print(f"GPU Memory usage: {response.json()['cuda']} MB")

    else:
        print(f"Error: {response.status_code}, {response.text}")