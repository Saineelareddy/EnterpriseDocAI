@echo off
set "PYTHON_EXE=C:\Users\saine\OneDrive\Documents\New folder\python_env\python.exe"
if not exist "%PYTHON_EXE%" (
    set "PYTHON_EXE=python"
)
echo Starting FastAPI Backend with %PYTHON_EXE%...
"%PYTHON_EXE%" run_backend.py
pause
