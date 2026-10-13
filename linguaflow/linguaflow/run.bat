@echo off
cd /d "%~dp0"
echo Installing requirements...
python -m pip install -r requirements.txt
echo.
echo Starting LinguaFlow...
python linguaflow.py
pause
