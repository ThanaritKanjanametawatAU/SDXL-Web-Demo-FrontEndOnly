import os
from dotenv import load_dotenv
import requests

from api.text2img import default_payload

load_dotenv()
APIBASE = os.environ.get("APIBASE")
url = f"{APIBASE}/sdapi/v1/unload-checkpoint"

# Payload
default_payload = {
}


def unload_checkpoint(url=url, payload=default_payload):
    # Sending POST request to the API
    response = requests.post(url)

    # Check if the response is successful
    if response.status_code == 200:
        print("Checkpoint unloaded")
    else:
        print(f"Error: {response.status_code}, {response.text}")
