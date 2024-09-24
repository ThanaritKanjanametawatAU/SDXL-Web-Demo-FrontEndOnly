# SparkJoy Image Generation Web App Demo

## Deployment

- **Website**: Deployed on Vercel at [sparkjoy-webdemo.vercel.app](https://sparkjoy-webdemo.vercel.app)


## Tech Stack

- **Frontend**: FastHTML
- **Backend**: FastAPI, RunPod API

## Setup Instructions

1. **Install Python 3.12.6**

2. **Create a virtual environment**

   ```sh
   python -m venv venv
   ```

3. **Activate the virtual environment**

   ```sh
   source venv/bin/activate
   ```

   To deactivate the virtual environment:

   ```sh
   deactivate
   ```

4. **Install requirements**

   ```sh
   pip install -r requirements.txt
   ```

5. **Run the application**

   ```sh
   ./start_server.sh
   ```

   If that doesn't work, try:

   ```sh
   chmod +x start_server.sh
   ```

   Or manually run the server with uvicorn:

   ```sh
   uvicorn main:app --reload --port 5000
   ```

6. **Open your browser and navigate to** [localhost:5000](http://localhost:5000)

