import os
from dotenv import load_dotenv
import requests
import base64
from PIL import Image
from io import BytesIO
from api.text2img import text2img
from pymongo import MongoClient
import uuid
from datetime import datetime

# Load environment variables
load_dotenv()

# MongoDB connection
MONGO_URI = os.environ.get("MONGO_URL")
client = MongoClient(MONGO_URI)
db = client['sdxl_demo_db']
collection = db['generated_images']

# Generate image
image, png_info = text2img()

# Convert image to base64
buffered = BytesIO()
image.save(buffered, format="PNG")
image_base64 = base64.b64encode(buffered.getvalue()).decode('utf-8')

# Store in MongoDB
image_id = str(uuid.uuid4())
document = {
    'image_id': image_id,
    'image_base64': image_base64,
    'metadata': {
        'prompt': "No prompt available",
        'date_created': datetime.utcnow()
    }
}
insert_result = collection.insert_one(document)
print(f"Image stored in MongoDB with ID: {insert_result.inserted_id}")

# Retrieve from MongoDB
retrieved_doc = collection.find_one({'image_id': image_id})

if retrieved_doc:
    # Convert base64 back to image
    retrieved_image_data = base64.b64decode(retrieved_doc['image_base64'])
    retrieved_image = Image.open(BytesIO(retrieved_image_data))
    
    # Save retrieved image to file
    retrieved_image.save(f"retrieved_image_{image_id}.png")
    print(f"Retrieved image saved as: retrieved_image_{image_id}.png")
    
    # Verify data integrity
    original_bytes = buffered.getvalue()
    retrieved_bytes = BytesIO()
    retrieved_image.save(retrieved_bytes, format="PNG")
    retrieved_bytes = retrieved_bytes.getvalue()
    
    if original_bytes == retrieved_bytes:
        print("Data integrity verified: Original and retrieved images are identical.")
    else:
        print("Warning: Data integrity check failed. Images are not identical.")
else:
    print("Error: Could not retrieve image from MongoDB.")

# Close MongoDB connection
client.close()

