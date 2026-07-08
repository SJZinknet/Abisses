@echo off
cd /d "%~dp0"
if exist ".venv\Scripts\python.exe" (
    ".venv\Scripts\python.exe" lancer_gestion_bisses.py
) else (
    py lancer_gestion_bisses.py
)
