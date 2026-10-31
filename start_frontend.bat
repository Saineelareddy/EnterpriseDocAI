@echo off
set "PYTHON_EXE=C:\Users\saine\OneDrive\Documents\New folder\python_env\python.exe"
if not exist "%PYTHON_EXE%" (
    set "PYTHON_EXE=python"
)
echo Starting Streamlit Frontend with %PYTHON_EXE%...
"%PYTHON_EXE%" -m streamlit run frontend\app.py --server.port 8501 --server.address 127.0.0.1 --server.headless true --browser.gatherUsageStats false
pause
