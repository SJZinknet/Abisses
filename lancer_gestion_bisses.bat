@echo off
setlocal
cd /d "%~dp0"

echo ============================================================
echo Lancement de Gestion Bisses
echo ============================================================

if exist ".venv\Scripts\python.exe" goto USE_VENV

where python >nul 2>&1
if not errorlevel 1 goto USE_PYTHON

where python3 >nul 2>&1
if not errorlevel 1 goto USE_PYTHON3

where py >nul 2>&1
if not errorlevel 1 goto USE_PY

goto USE_ASSOCIATION


:USE_VENV
".venv\Scripts\python.exe" lancer_gestion_bisses.py
set "APP_ERROR=%ERRORLEVEL%"
goto END


:USE_PYTHON
python lancer_gestion_bisses.py
set "APP_ERROR=%ERRORLEVEL%"
goto END


:USE_PYTHON3
python3 lancer_gestion_bisses.py
set "APP_ERROR=%ERRORLEVEL%"
goto END


:USE_PY
py lancer_gestion_bisses.py
set "APP_ERROR=%ERRORLEVEL%"
goto END


:USE_ASSOCIATION
echo Python n'est pas disponible dans le PATH.
echo Tentative avec l'association Windows des fichiers .py...
start "" /wait "%~dp0lancer_gestion_bisses.py"
set "APP_ERROR=%ERRORLEVEL%"
goto END


:END
if not "%APP_ERROR%"=="0" (
    echo.
    echo Gestion Bisses ne s'est pas lance correctement.
    echo Consultez lancement_gestion_bisses.log dans ce dossier.
    pause
)

endlocal
