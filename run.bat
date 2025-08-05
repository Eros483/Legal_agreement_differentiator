@echo off
echo Starting Backend and Frontend Applications...

REM Set conda environment path
set CONDA_ENV_PATH=%USERPROFILE%\miniconda3\envs\legal

REM Start backend server using direct python path
start "Backend Server" cmd /k "cd /d %~dp0backend && %CONDA_ENV_PATH%\python.exe -m uvicorn main:app --reload"

REM Wait a moment before starting frontend
timeout /t 2 /nobreak >nul

REM Start frontend application using direct python path
start "Frontend App" cmd /k "cd /d %~dp0 && %CONDA_ENV_PATH%\python.exe -m streamlit run app.py"

echo Both applications are starting...
echo Backend will be available at: http://localhost:8000
echo Frontend will be available at: http://localhost:8501
pause