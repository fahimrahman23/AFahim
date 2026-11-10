@echo off
python main.py
if %errorlevel% neq 0 (
  echo Please run: pip install -r requirements.txt
  pause
)
