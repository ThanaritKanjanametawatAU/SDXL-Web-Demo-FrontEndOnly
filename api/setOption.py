import os
from dotenv import load_dotenv
import requests
import json


load_dotenv()
APIBASE = os.environ.get("APIBASE")
url = f"{APIBASE}/sdapi/v1/options"

# Payload
default_payload = {
    "something": "something",
    "something": "something"
}

def getOptions(url=url, payload=default_payload):
    # Sending POST request to the API
    response = requests.get(url)

    # Check if the response is successful
    if response.status_code == 200:

        # Print Pretty
        print(json.dumps(response.json(), indent=4))
    else:
        print(f"Error: {response.status_code}, {response.text}")

def setOptions(url=url, payload=default_payload):
    # Sending POST request to the API
    response = requests.post(url, json=payload)

    # Check if the response is successful
    if response.status_code == 200:
        print(response.json())
    else:
        print(f"Error: {response.status_code}, {response.text}")

