@echo off
cd /d "%~dp0"
python flashcards_gui.py
if %errorlevel% neq 0 pause
