import sys
from pathlib import Path
from streamlit.web import bootstrap

if __name__ == "__main__":
    frontend_path = Path(__file__).parent / "frontend" / "app.py"
    print(f"Launching Streamlit Frontend: {frontend_path}")
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

