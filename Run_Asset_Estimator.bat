@echo off
setlocal
title ASSET ESTIMATOR - HASNAOUI GROUPE
cd /d "%~dp0"

echo =======================================================
echo     ASSET ESTIMATOR - HASNAOUI GROUPE
echo =======================================================
echo.

:: Check if port 5000 is occupied
netstat -ano | findstr :5000 | findstr LISTENING > nul
if %errorlevel% equ 0 (
    echo [INFO] Le serveur est deja en cours d'execution.
) else (
    echo [INFO] Demarrage du serveur Python...
    :: Use 'start' to run the server in a separate hidden window or just run it here
    :: Running it here keeps the window open so the user knows it's active.
    start "Asset Estimator Server" python ui.py
    echo [WAIT] Initialisation (5s)...
    timeout /t 5 /nobreak > nul
)

echo [INFO] Ouverture de l'interface...
start http://localhost:5000

echo.
echo =======================================================
echo  L'APPLICATION EST PRETE !
echo  Gardez la fenetre "Asset Estimator Server" ouverte.
echo =======================================================
echo.
timeout /t 10
exit
