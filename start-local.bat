@echo off
rem ==========================================================================
rem  Multilingual OCR Suite - demarrage complet SANS Docker (developpement local)
rem  API FastAPI (SQLite + OCR dans un thread, pas de PostgreSQL/Redis/Celery)
rem  + application Cartes de visite (5174)
rem  Prerequis : Python 3.12 + uv, Node.js 20+
rem ==========================================================================
setlocal
chcp 65001 >nul
cd /d "%~dp0"
set "ROOT=%~dp0"

echo.
echo [1/5] Environnement Python...
if exist ".venv\Scripts\python.exe" goto venv_ok
where uv >nul 2>&1
if errorlevel 1 goto no_uv
echo  Creation de .venv et installation des dependances, plusieurs minutes...
uv venv --python 3.12 .venv || goto fail
uv pip install --python .venv\Scripts\python.exe -e "./packages[paddle,tesseract,synthetic]" -e ./apps/api || goto fail
echo  Telechargement des modeles OCR...
.venv\Scripts\python.exe infrastructure\scripts\download_models.py >nul || goto fail
:venv_ok

echo [2/5] Dependances web...
where npm >nul 2>&1
if errorlevel 1 goto no_npm
if not exist "node_modules" call npm install || goto fail

echo [3/5] Base de donnees locale (SQLite) et migrations...
if not exist "data\storage" mkdir "data\storage"
set "DATABASE_URL=sqlite:///%ROOT:\=/%data/dev.db"
set "STORAGE_LOCAL_PATH=%ROOT%data\storage"
set "JOB_EXECUTION=thread"
set "OCR_WARMUP=true"
set "PYTHONIOENCODING=utf-8"
pushd apps\api
"%ROOT%.venv\Scripts\python.exe" -m alembic upgrade head
if errorlevel 1 (popd & goto fail)
popd

echo [4/5] Demarrage des 2 serveurs (chacun dans sa fenetre)...
start "OCR API :8000" cmd /k ""%ROOT%.venv\Scripts\python.exe" -m uvicorn app.main:app --app-dir "%ROOT%apps\api" --port 8000"
set "VITE_BASE=/"
start "Cartes de visite :5174" cmd /k "cd /d "%ROOT%apps\business-card-web" && npm run dev"

echo [5/5] Attente de l'API (chargement des modeles OCR)...
set /a TRIES=0
:wait
set /a TRIES+=1
curl -fs "http://localhost:8000/api/v1/health" >nul 2>&1
if not errorlevel 1 goto ready
if %TRIES% GEQ 40 goto api_timeout
timeout /t 3 /nobreak >nul
goto wait

:ready
echo.
echo  Tout est pret :
echo    Cartes de visite   : http://localhost:5174/
echo    Documentation API  : http://localhost:8000/api/v1/docs
echo.
echo  Pour arreter : fermez les 2 fenetres ouvertes.
if not defined NO_BROWSER start "" "http://localhost:5174/"
pause
exit /b 0

:no_uv
echo  ERREUR : uv introuvable. Installation : https://docs.astral.sh/uv/getting-started/installation/
pause
exit /b 1

:no_npm
echo  ERREUR : Node.js / npm introuvable. Installez Node.js 20 ou plus.
pause
exit /b 1

:api_timeout
echo  L'API ne repond pas : regardez la fenetre OCR API 8000.
pause
exit /b 1

:fail
echo.
echo  ERREUR pendant l'installation / la migration (voir les messages ci-dessus).
pause
exit /b 1
