import logging
from fasthtml.common import *
from dotenv import load_dotenv
from fastcore.parallel import threaded
import uuid
from api.text2img import text2img
from pymongo import MongoClient
import base64
from io import BytesIO
from datetime import datetime
import time
import random
import json
import os
import io
from PIL import Image

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

load_dotenv()
TESTVAR = os.environ.get("TESTVAR")
APIBASE = os.environ.get("APIBASE")
MONGO_URI = os.environ.get("MONGO_URL")

# Lazy imports
from functools import lru_cache

import certifi

@lru_cache(maxsize=None)
def get_db_client():
    from pymongo import MongoClient
    logger.info("Connecting to MongoDB...")
    
    # Modify the connection string
    connection_string = f"{MONGO_URI}&tlsAllowInvalidCertificates=true&tls=true&tlsInsecure=true"
    
    client = MongoClient(connection_string, 
                         serverSelectionTimeoutMS=5000,
                         tlsCAFile=certifi.where())  # Add this line
    try:
        # Test the connection
        client.server_info()
        logger.info("Successfully connected to MongoDB")
        return client
    except Exception as e:
        logger.error(f"Failed to connect to MongoDB: {str(e)}")
        return None

def get_db():
    client = get_db_client()
    if client is not None:
        return client['sdxl_demo_db']
    return None

# Flexbox CSS (http://flexboxgrid.com/)
gridlink = Link(rel="stylesheet", href="https://cdnjs.cloudflare.com/ajax/libs/flexboxgrid/6.3.1/flexboxgrid.min.css",
                type="text/css")

# Custom CSS for improved styling
custom_css = """
<style>
    body { background-color: #0f172a; color: #e2e8f0; font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; }
    .container { max-width: 800px; margin: 0 auto; padding: 20px; }
    .card { background: #1e293b; border-radius: 12px; padding: 24px; margin-bottom: 24px; box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1); }
    .form-group { margin-bottom: 20px; }
    .form-group label { display: block; margin-bottom: 8px; font-weight: 600; font-size: 14px; color: #93c5fd; }
    .form-control { width: 100%; padding: 12px; border: 1px solid #4b5563; border-radius: 6px; background-color: #2d3748; color: #e2e8f0; font-size: 16px; transition: border-color 0.3s ease; }
    .form-control:focus { border-color: #60a5fa; outline: none; }
    .btn-primary { background-color: #3b82f6; color: #ffffff; padding: 12px 20px; border: none; border-radius: 6px; cursor: pointer; width: 100%; font-size: 16px; font-weight: bold; transition: background-color 0.3s ease; }
    .btn-primary:hover { background-color: #2563eb; }
    .image-grid { display: flex; flex-wrap: wrap; gap: 24px; }
    .image-card { flex: 0 0 calc(50% - 12px); max-width: calc(50% - 12px); }
    @media (max-width: 768px) { .image-card { flex: 0 0 100%; max-width: 100%; } }
    .range-container { display: grid; grid-template-columns: 1fr 100px; gap: 8px; align-items: center; }
    .range-input { -webkit-appearance: none; width: 100%; height: 6px; border-radius: 3px; background: #4b5563; outline: none; margin-top: 8px; margin-bottom: 8px; }
    .range-input::-webkit-slider-thumb { -webkit-appearance: none; appearance: none; width: 18px; height: 18px; border-radius: 50%; background: #60a5fa; cursor: pointer; }
    .range-input::-moz-range-thumb { width: 18px; height: 18px; border-radius: 50%; background: #60a5fa; cursor: pointer; }
    .range-value { width: 100%; text-align: right; font-weight: 600; color: #93c5fd; background-color: #2d3748; border: 1px solid #4b5563; border-radius: 4px; padding: 8px; }
    .range-value:focus { outline: none; border-color: #60a5fa; }
    .prompt-label { font-size: 18px; color: #93c5fd; margin-bottom: 12px; }
    .prompt-textarea { min-height: 120px; resize: vertical; }
    .progress-bar {
        transition: width 0.5s ease-in-out;
    }
</style>
"""

# Add this near the top of your file, after the imports
SECRET_KEY = os.environ.get("SECRET_KEY") or os.urandom(24).hex()

app, rt = fast_app(hdrs=(picolink, gridlink, NotStr(custom_css)), secret_key=SECRET_KEY)

@rt("/")
def get():
    try:
        logger.info("GET / route accessed")
        
        db = get_db()
        if db is None:
            logger.error("Failed to connect to the database")
            return "Database connection error. Please try again later."

        gens = db['generated_images']
        
        # Log the number of documents in the collection
        try:
            doc_count = gens.count_documents({})
            logger.info(f"Number of documents in 'generated_images' collection: {doc_count}")
        except Exception as e:
            logger.error(f"Error counting documents: {str(e)}")
            return "Error accessing the database. Please try again later."

        form_inputs = [
            Div(
                Label("Positive Prompt", cls="prompt-label"),
                Textarea(id="prompt", name="prompt", placeholder="Enter a positive prompt", rows=4,
                         cls="form-control prompt-textarea")
            ),
            Div(
                Label("Negative Prompt", cls="prompt-label"),
                Textarea(id="negative_prompt", name="negative_prompt", placeholder="Enter a negative prompt", rows=4,
                         cls="form-control prompt-textarea")
            ),
            Group(
                Label("Width", cls="prompt-label"),
                Div(
                    Input(type="range", id="width", name="width", min="64", max="2048", value="832", step="8",
                          cls="range-input"),
                    Input(type="number", value="832", step="8", cls="form-control range-value", id="width-value"),
                    cls="range-container"
                )
            ),
            Group(
                Label("Height", cls="prompt-label"),
                Div(
                    Input(type="range", id="height", name="height", min="64", max="2048", value="1216", step="8",
                          cls="range-input"),
                    Input(type="number", value="1216", step="8", cls="form-control range-value", id="height-value"),
                    cls="range-container"
                )
            ),
            Group(
                Label("Steps", cls="prompt-label"),
                Div(
                    Input(type="range", id="num_inference_steps", name="num_inference_steps", min="1", max="100",
                          value="28", cls="range-input"),
                    Input(type="number", value="28", cls="form-control range-value", id="steps-value"),
                    cls="range-container"
                )
            ),
            Group(
                Label("Guidance Scale", cls="prompt-label"),
                Div(
                    Input(type="range", id="guidance_scale", name="guidance_scale", min="0", max="10", step="0.5",
                          value="5.0", cls="range-input"),
                    Input(type="number", value="5", step="0.5", cls="form-control range-value", id="guidance-value"),
                    cls="range-container"
                )
            ),
            Group(
                Label("Clip Skip", cls="prompt-label"),
                Div(
                    Input(type="range", id="clip_skip", name="clip_skip", min="0", max="5", step="1",
                          value="2", cls="range-input"),
                    Input(type="number", value="2", step="1", cls="form-control range-value", id="clip-skip-value"),
                    cls="range-container"
                )
            ),
            Div(
                Label("Seed", cls="prompt-label"),
                Input(type="number", id="seed", name="seed", value="-1", cls="form-control")
            ),
            Div(
                Label("Sampler", cls="prompt-label"),
                Select(
                    Option("DPM++ 2M SDE", value="DPM++ 2M SDE", selected=True),
                    id="sampler", name="sampler", cls="form-control"
                )
            )
        ]

        add = Form(*form_inputs, Button("Generate 1 Image", cls="btn-primary"),
                   hx_post="/generate", target_id='gen-list', hx_swap="afterbegin", cls="card")

        # Fetch generation previews
        try:
            gen_containers = [generation_preview(g) for g in gens.find().sort('metadata.date_created', -1).limit(10)]
            logger.info(f"Retrieved {len(gen_containers)} generation previews")
        except Exception as e:
            logger.error(f"Error fetching generation previews: {str(e)}")
            return "Error retrieving generation previews. Please try again later."

        gen_list = Div(*gen_containers, id='gen-list', cls="image-grid")

        return (
            Socials(
                title="Image Generation SDXL",
                site_name="SDXL Demo",
                description="A demo of SDXL image generation",
                image="https://example.com/sdxl-og-image.jpg",
                url="https://your-deployment-url.com",
                twitter_site="@your_twitter",
            ),
            Container(
                Card(
                    H1('Image Generation SDXL', cls="text-center", style="color: #60a5fa; margin-bottom: 24px;"),
                    add,
                    gen_list,
                    footer=(
                        P(
                            "Powered by SDXL and FastHTML. ",
                            A("Learn more", href="https://your-docs-url.com"),
                            " about this project.",
                        )
                    ),
                ),
            ),
            Script("""
                // Function to handle width and height inputs
                function setupDivisibleBy8Input(container) {
                    const rangeInput = container.querySelector('.range-input');
                    const valueInput = container.querySelector('.range-value');

                    function roundToNearest8(value) {
                        return Math.round(value / 8) * 8;
                    }

                    function updateValue(value, shouldRound = true) {
                        let processedValue = shouldRound ? roundToNearest8(value) : value;
                        const min = parseInt(rangeInput.min);
                        const max = parseInt(rangeInput.max);

                        if (shouldRound) {
                            processedValue = Math.max(min, Math.min(max, processedValue));
                            rangeInput.value = processedValue;
                        }

                        valueInput.value = processedValue;
                    }

                    rangeInput.addEventListener('input', () => updateValue(rangeInput.value));
                    valueInput.addEventListener('input', () => updateValue(valueInput.value, false));
                    valueInput.addEventListener('blur', () => {
                        if (valueInput.value === '') {
                            updateValue(rangeInput.value);
                        } else {
                            updateValue(valueInput.value);
                        }
                    });
                }

                // Function to handle all other inputs
                function setupOtherInput(container) {
                    const rangeInput = container.querySelector('.range-input');
                    const valueInput = container.querySelector('.range-value');

                    function updateValue(value) {
                        const min = parseFloat(rangeInput.min);
                        const max = parseFloat(rangeInput.max);
                        const step = parseFloat(rangeInput.step) || 1;

                        let processedValue = Math.max(min, Math.min(max, parseFloat(value)));
                        processedValue = Math.round(processedValue / step) * step;

                        rangeInput.value = processedValue;
                        valueInput.value = processedValue;
                    }

                    rangeInput.addEventListener('input', () => updateValue(rangeInput.value));
                    valueInput.addEventListener('input', () => updateValue(valueInput.value));
                    valueInput.addEventListener('blur', () => {
                        if (valueInput.value === '') {
                            updateValue(rangeInput.value);
                        }
                    });
                }

                // Set up width and height inputs
                document.querySelectorAll('#width .range-container, #height .range-container').forEach(setupDivisibleBy8Input);

                // Set up all other inputs
                document.querySelectorAll('.range-container:not(#width .range-container):not(#height .range-container)').forEach(setupOtherInput);
            """),
        )

    except Exception as e:
        logger.error(f"Error in GET / route: {str(e)}")
        return "An error occurred. Please check the logs for more information."

# Show the image (if available) and prompt for a generation
def generation_preview(g):
    if g and 'image_base64' in g:
        prompt = g.get('metadata', {}).get('prompt', 'No prompt available')
        # Use a data URI with a compressed JPEG instead of PNG
        compressed_image = compress_image(g['image_base64'])
        return Div(
            Img(src=f"data:image/jpeg;base64,{compressed_image}", alt="Generated image", style="width: 100%; border-radius: 8px;"),
            Div(P(B("Prompt: "), prompt, style="margin-top: 12px; font-size: 14px; color: #93c5fd;")),
            cls="card image-card", id=f'gen-{g["image_id"]}'
        )
    elif g:
        prompt = g.get('metadata', {}).get('prompt', 'No prompt available')
        return Div(
            P(f"Generating image with prompt: {prompt}", style="color: #93c5fd;"),
            Div(cls="progress-bar", style="width: 0%; height: 5px; background-color: #4CAF50; transition: width 0.5s;"),
            cls="card image-card", id=f'gen-{g["image_id"]}',
            hx_get=f"/gens/{g['image_id']}", hx_trigger="every 500ms", hx_swap="outerHTML"
        )
    else:
        return Div(P("No image data available", style="color: #93c5fd;"), cls="card image-card")

def compress_image(base64_string, quality=85, max_size=(800, 800)):
    # Decode base64 string to bytes
    image_data = base64.b64decode(base64_string)
    
    # Open the image using PIL
    with Image.open(io.BytesIO(image_data)) as img:
        # Resize the image if it's larger than max_size
        img.thumbnail(max_size, Image.LANCZOS)
        
        # Save the image as JPEG with the specified quality
        buffer = io.BytesIO()
        img.convert('RGB').save(buffer, format='JPEG', quality=quality, optimize=True)
        
        # Get the compressed image as base64
        compressed_base64 = base64.b64encode(buffer.getvalue()).decode('utf-8')
    
    return compressed_base64

@rt("/gens/{id}")
def preview(id: str):
    db = get_db()
    if db is None:
        logger.error("Failed to connect to the database in preview function")
        return Div(P("Database connection error. Please try again later.", style="color: #93c5fd;"), cls="card image-card")

    gens = db['generated_images']
    g = gens.find_one({'image_id': id})
    if g and 'image_base64' in g:
        return generation_preview(g)
    elif g:
        progress = min((time.time() - g['metadata']['start_time']) / 10 * 100, 99)  # Assume 10 seconds generation time
        return Div(
            P(f"Generating image with prompt: {g['metadata']['prompt']}", style="color: #93c5fd;"),
            Div(cls="progress-bar", style=f"width: {progress}%; height: 5px; background-color: #4CAF50; transition: width 0.5s;"),
            cls="card image-card", id=f'gen-{g["image_id"]}',
            hx_get=f"/gens/{g['image_id']}", hx_trigger="every 500ms", hx_swap="outerHTML"
        )
    else:
        return Div(P("No image data available", style="color: #93c5fd;"), cls="card image-card")

@rt("/{fname:path}.{ext:static}")
def static(fname: str, ext: str): return FileResponse(f'{fname}.{ext}')

@rt("/generate")
def generate(prompt: str, negative_prompt: str, width: int, height: int, num_inference_steps: int,
             guidance_scale: float, clip_skip: int, seed: int, sampler: str):
    try:
        db = get_db()
        if db is None:
            logger.error("Failed to connect to the database")
            return "Database connection error. Please try again later."

        gens = db['generated_images']

        image_id = str(uuid.uuid4())

        payload = {
            "prompt": prompt,
            "negative_prompt": negative_prompt,
            "seed": seed,
            "width": width,
            "height": height,
            "steps": num_inference_steps,
            "sampler_name": sampler,
            "scheduler": "Karras",
            "cfg_scale": guidance_scale,
            "batch_size": 1,
            "hr_checkpoint_name": "NovelAIv2-7.safetensors",
            "override_settings": {
                "CLIP_stop_at_last_layers": clip_skip
            }
        }

        initial_doc = {
            'image_id': image_id,
            'metadata': {
                'prompt': prompt,
                'start_time': time.time(),
                'date_created': datetime.utcnow()
            }
        }

        gens.insert_one(initial_doc)

        generate_and_save(payload, image_id)

        # Instead of returning the full preview, return a placeholder
        placeholder = Div(
            P(f"Image generation started. ID: {image_id}", style="color: #93c5fd;"),
            Div(cls="progress-bar", style="width: 0%; height: 5px; background-color: #4CAF50; transition: width 0.5s;"),
            cls="card image-card", id=f'gen-{image_id}',
            hx_get=f"/gens/{image_id}", hx_trigger="load delay:500ms", hx_swap="outerHTML"
        )

        clear_inputs = [
            Textarea(id="prompt", name="prompt", placeholder="Enter a positive prompt", rows=4,
                     cls="form-control prompt-textarea", hx_swap_oob='true'),
            Textarea(id="negative_prompt", name="negative_prompt", placeholder="Enter a negative prompt", rows=4,
                     cls="form-control prompt-textarea", hx_swap_oob='true'),
        ]

        return placeholder, *clear_inputs

    except Exception as e:
        logger.error(f"Error in generate function: {str(e)}")
        return "An error occurred during image generation. Please try again later."

@threaded
def generate_and_save(payload, image_id):
    try:
        db = get_db()
        if db is None:
            logger.error("Failed to connect to the database in generate_and_save")
            return False

        gens = db['generated_images']

        image_base64, png_info = text2img(payload=payload)

        # Parse png_info
        png_info = json.loads(png_info)

        # Update MongoDB document with image data
        gens.update_one(
            {'image_id': image_id},
            {'$set': {'image_base64': image_base64,
                      'png_info': png_info}}
        )
        return True
    except Exception as e:
        logger.error(f"Error in generate_and_save function: {str(e)}")
        return False

serve()
