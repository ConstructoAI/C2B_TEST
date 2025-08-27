@echo off
cls
color 0A
echo ============================================================
echo    GESTIONNAIRE DE SOUMISSIONS C2B CONSTRUCTION
echo ============================================================
echo.
echo [+] VERSION PRODUCTION COMPLETE
echo.
echo Fonctionnalites disponibles :
echo   - Dashboard unifie (Heritage + Uploads)
echo   - Creation de soumissions Heritage
echo   - Upload multi-format (PDF, Word, Excel, Images)
echo   - Modification et suppression
echo   - Liens clients avec approbation
echo.
echo ============================================================
echo.

REM Verifier si Python est installe
py --version >nul 2>&1
if %errorlevel% neq 0 (
    echo [ERREUR] Python n'est pas installe ou pas dans le PATH
    echo Veuillez installer Python depuis https://www.python.org
    pause
    exit /b 1
)

echo [1/3] Verification de l'environnement Python...
py --version

echo.
echo [2/3] Installation des dependances...
py -m pip install -r requirements.txt --quiet 2>nul
if %errorlevel% neq 0 (
    echo Installation des packages en cours...
    py -m pip install -r requirements.txt
)

echo.
echo [3/3] Creation des dossiers necessaires...
if not exist "data" mkdir data
if not exist "files" mkdir files

echo.
echo ============================================================
echo    APPLICATION PRETE !
echo ============================================================
echo.
echo URL LOCAL : http://localhost:8501
echo.
echo ACCES ADMIN :
echo   - Mot de passe : admin2025
echo.
echo RACCOURCIS :
echo   - Ctrl+C pour arreter l'application
echo   - F5 dans le navigateur pour rafraichir
echo.
echo ============================================================
echo.
echo Lancement de l'application...
echo.

REM Lancer Streamlit
py -m streamlit run app.py --server.port=8501 --server.address=localhost

echo.
echo ============================================================
echo Application fermee.
echo ============================================================
pause