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

load_dotenv()
TESTVAR = os.environ.get("TESTVAR")
APIBASE = os.environ.get("APIBASE")
MONGO_URI = os.environ.get("MONGO_URL")

# MongoDB connection
client = MongoClient(MONGO_URI)
db = client['sdxl_demo_db']
gens = db['generated_images']

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

# Our FastHTML app
app = FastHTML(hdrs=(picolink, gridlink, NotStr(custom_css)))


# Main page
@app.get("/")
def home():
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
               hx_post="/", target_id='gen-list', hx_swap="afterbegin", cls="card")

    gen_containers = [generation_preview(g) for g in gens.find().sort('metadata.date_created', -1).limit(10)]
    gen_list = Div(*gen_containers, id='gen-list', cls="image-grid")  # flexbox container

    return Title('Image Generation SDXL'), Main(
        H1('Image Generation SDXL', cls="text-center", style="color: #60a5fa; margin-bottom: 24px;"),
        add,
        gen_list,
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
        cls='container'
    )


# Show the image (if available) and prompt for a generation
def generation_preview(g):
    if g and 'image_base64' in g:
        prompt = g.get('metadata', {}).get('prompt', 'No prompt available')
        return Div(
            Img(src=f"data:image/png;base64,{g['image_base64']}", alt="Generated image", style="width: 100%; border-radius: 8px;"),
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


# A pending preview keeps polling this route until we return the image preview
@app.get("/gens/{id}")
def preview(id: str):
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


# For images, CSS, etc.
@app.get("/{fname:path}.{ext:static}")
def static(fname: str, ext: str): return FileResponse(f'{fname}.{ext}')


# Generation route
@app.post("/")
def post(prompt: str, negative_prompt: str, width: int, height: int, num_inference_steps: int,
         guidance_scale: float, clip_skip: int, seed: int, sampler: str):
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

    # Create initial document with start time
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

    # Clear inputs (you may need to adjust this based on your needs)
    clear_inputs = [
        Textarea(id="prompt", name="prompt", placeholder="Enter a positive prompt", rows=4,
                 cls="form-control prompt-textarea", hx_swap_oob='true'),
        Textarea(id="negative_prompt", name="negative_prompt", placeholder="Enter a negative prompt", rows=4,
                 cls="form-control prompt-textarea", hx_swap_oob='true'),
    ]

    return generation_preview(gens.find_one({'image_id': image_id})), *clear_inputs


# Generate an image and save it to MongoDB (in a separate thread)
@threaded
def generate_and_save(payload, image_id):
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


# if __name__ == '__main__':
#     uvicorn.run("main:app", host='0.0.0.0', port=int(os.getenv("PORT", default=5000)), reload=True)