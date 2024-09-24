import requests
import base64
from PIL import Image
from io import BytesIO
import json
import dotenv
import os

dotenv.load_dotenv()

RUNPOD_API_KEY = os.environ.get("RUNPOD_API_KEY")
RUNPOD_SERVERLESS_ENDPOINT = os.environ.get("RUNPOD_SERVERLESS_ENDPOINT")




# Data to send in the POST request (this matches your input format)
data = {
    "input": {
        "prompt": "1girl, anime, best quality, good quality",
        "negative_prompt": "animals",
        "sampler_name": "Euler",
        "steps": 50,
        "cfg_scale": 5,
        "width": 512,
        "height": 512,
    }
}

# Headers to include the API key
headers = {
    "Authorization": f"Bearer {RUNPOD_API_KEY}"
}

# Make the POST request
response = requests.post(RUNPOD_SERVERLESS_ENDPOINT, json=data, headers=headers)

# Check if the request was successful
if response.status_code == 200:
    try:
        response_json = response.json()

        # Decode the response base64 string to image
        image_data = response_json['output']['images'][0]
        image = Image.open(BytesIO(base64.b64decode(image_data)))
        image.show()

        # Print the response (Turn string into json)
        print(json.loads(response_json['output']['info']))
    except requests.exceptions.JSONDecodeError as e:
        print("Failed to parse JSON response:", e)
        print("Response content:", response.info)
else:
    print("Request failed with status code:", response.status_code)

    # Show Raw Response
    print(response.text)