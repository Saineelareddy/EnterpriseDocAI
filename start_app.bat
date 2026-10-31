@echo off
set "PYTHON_EXE=C:\Users\saine\OneDrive\Documents\New folder\python_env\python.exe"
if not exist "%PYTHON_EXE%" (
    set "PYTHON_EXE=python"
)

echo ===================================================
echo Starting EnterpriseDoc AI (Unified Runner)
echo Backend:  http://127.0.0.1:8000
echo Frontend: http://127.0.0.1:8501
echo ===================================================

"%PYTHON_EXE%" run_all.py
pause
