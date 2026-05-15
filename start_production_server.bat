@echo off
echo =======================================================
echo     Demarrage du Serveur Amortissement (Production)
echo =======================================================
echo.
echo Veuillez vous assurer d'avoir installe les dependances avec :
echo    pip install -r requirements.txt
echo.
echo Le serveur sera accessible sur le port 5000.
echo Appuyez sur CTRL+C pour l'arreter.
echo.

waitress-serve --host=0.0.0.0 --port=5000 ui:app

pause
