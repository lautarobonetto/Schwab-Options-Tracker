from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
import os

app = FastAPI(title="Schwab Options Tracker")

# Mount static files (Frontend)
# In development, we might not use this if running Vite separately, but for the Docker build it is needed.
# We'll check if the directory exists to avoid errors in dev mode involving just the backend.
static_path = "/app/static"
if os.path.exists(static_path):
    app.mount("/", StaticFiles(directory=static_path, html=True), name="static")

@app.get("/health")
def health_check():
    return {"status": "ok"}
