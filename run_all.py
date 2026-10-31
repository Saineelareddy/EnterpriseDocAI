import sys
import threading
import time
from pathlib import Path

# Add project root to path
PROJECT_ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(PROJECT_ROOT))

import uvicorn
from backend.config import BACKEND_HOST, BACKEND_PORT
from backend.app import app
from streamlit.web import bootstrap

def start_backend():
    print(f"Starting Backend on http://{BACKEND_HOST}:{BACKEND_PORT}...")
    config = uvicorn.Config(app, host=BACKEND_HOST, port=BACKEND_PORT, log_level="warning")
    server = uvicorn.Server(config)
    server.run()

if __name__ == "__main__":
    # Start backend in a background daemon thread
    backend_thread = threading.Thread(target=start_backend, daemon=True)
    backend_thread.start()

    time.sleep(1.5)
    print("Backend started successfully.")

    frontend_path = PROJECT_ROOT / "frontend" / "app.py"
    print(f"Launching Streamlit Frontend on http://127.0.0.1:8501: {frontend_path}")
    bootstrap.run(
        str(frontend_path),
        is_hello=False,
        args=[],
        flag_options={
            "server.port": 8501,
            "server.address": "127.0.0.1",
            "server.headless": True,
            "browser.gatherUsageStats": False
        }
    )

