@echo off
echo Starting Backend and Frontend Applications...

REM Kill any existing conda processes that might be holding files
taskkill /f /im conda.exe 2>nul
taskkill /f /im python.exe 2>nul

REM Wait a moment
timeout /t 2 /nobreak >nul

REM Use direct python activation instead of conda activate
set CONDA_PATH=%USERPROFILE%\miniconda3
set LEGAL_ENV=%CONDA_PATH%\envs\legal

REM Start backend server
start "Backend Server" cmd /k "set PATH=%LEGAL_ENV%;%LEGAL_ENV%\Scripts;%PATH% && cd /d %~dp0backend && python -m uvicorn main:app --reload"

REM Start frontend application
start "Frontend App" cmd /k "set PATH=%LEGAL_ENV%;%LEGAL_ENV%\Scripts;%PATH% && cd /d %~dp0 && python -m streamlit run app.py"

echo Both applications are starting...
echo Backend will be available at: http://localhost:8000
echo Frontend will be available at: http://localhost:8501
pause