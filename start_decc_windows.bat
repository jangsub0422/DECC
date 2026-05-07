@echo off
setlocal

cd /d "%~dp0"

echo Starting DECC Streamlit wrapper...
python -m streamlit run web_app.py

if errorlevel 1 (
    echo.
    echo Failed to start with "python -m streamlit".
    echo Make sure Python and Streamlit are installed and available in PATH.
    pause
)
