import os

# from api.call_api import *
# from main import APIBASE
from dotenv import load_dotenv
import requests
import base64
from PIL import Image
from io import BytesIO

load_dotenv()
APIBASE = os.environ.get("APIBASE")



# API URL
url = f"{APIBASE}/sdapi/v1/txt2img"


# API request payload
data = {
    "prompt": "1girl, pale skin, {purple eyes}, sanpaku, very long hair, pink hair, teeth, bloomers, slippers, waist apron, lollipop, spoon, best quality, amazing quality, very aesthetic, absurdres, masterpiece",
    "seed": 768779861,
    "width": 896,
    "height": 1152,
    "steps": 20,
    "sampler_name": "DPM++ 2M SDE",
    "scheduler": "Karras",
    "cfg_scale": 5,
    "batch_size": 1,
    "hr_checkpoint_name": "NovelAIv2-7.safetensors"
}

# Sending POST request to the API
response = requests.post(url, json=data)

# Check if the response is successful
if response.status_code == 200:
    # Assuming the response contains a base64 string under 'image' key
    response_data = response.json()
    base64_image = response_data['images'][0]  # Extract the base64 image string

    # Decode the base64 string into image data
    image_data = base64.b64decode(base64_image)

    # Convert the image data to an actual image
    image = Image.open(BytesIO(image_data))

    # Save or show the image
    image.save("output_image.png")  # Save as a file

    # Display the info
    png_info = response_data['info']
    print(png_info)
else:
    print(f"Error: {response.status_code}, {response.text}")






# Using Default Payload
# image = generate_image(url="APIBASE", payload=None, save_path="database/gens/something2/2.png")