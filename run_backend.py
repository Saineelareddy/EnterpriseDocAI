import sys
from pathlib import Path

# Add project root to sys.path
sys.path.insert(0, str(Path(__file__).parent.resolve()))

import uvicorn
from backend.config import BACKEND_HOST, BACKEND_PORT

if __name__ == "__main__":
    print(f"Starting EnterpriseDoc AI Backend on http://{BACKEND_HOST}:{BACKEND_PORT}")
    uvicorn.run("backend.app:app", host=BACKEND_HOST, port=BACKEND_PORT, reload=True)

