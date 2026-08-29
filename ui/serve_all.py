import uvicorn
from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import RedirectResponse
import os

app = FastAPI(title="GeoLLM Integrated UI & Tile Server")

# Allow CORS for everything
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Define directories
ui_dir = os.path.abspath(r"d:\An_GeoLLM\ui")
data_dir = os.path.abspath(r"d:\TEST_0708")

# Check directories exist
if not os.path.isdir(data_dir):
    print(f"Warning: Data directory {data_dir} not found.")
if not os.path.isdir(ui_dir):
    print(f"Warning: UI directory {ui_dir} not found.")

# Mount the heavy 3D tiles and data first
app.mount("/TEST_0708", StaticFiles(directory=data_dir), name="tiles")

# Root redirect to index.html to ensure it serves correctly if just / is hit
@app.get("/")
def read_root():
    return RedirectResponse(url="/index.html")

# Mount the UI directory at root. Must be mounted LAST because it catches everything else.
app.mount("/", StaticFiles(directory=ui_dir, html=True), name="ui")

if __name__ == "__main__":
    print("Starting Integrated Server...")
    print("UI is available at: http://localhost:8000/")
    print("Data is available at: http://localhost:8000/TEST_0708/")
    uvicorn.run(app, host="0.0.0.0", port=8000)
