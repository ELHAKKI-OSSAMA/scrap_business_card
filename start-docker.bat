@echo off
rem ==========================================================================
rem  Multilingual OCR Suite - demarrage complet avec Docker
rem  (PostgreSQL, Redis, API, worker OCR, application web, passerelle nginx)
rem ==========================================================================
setlocal
chcp 65001 >nul
cd /d "%~dp0"

echo.
echo [1/4] Verification de Docker...
docker info >nul 2>&1
if errorlevel 1 (
    echo  ERREUR : Docker n'est pas demarre. Lancez Docker Desktop puis relancez ce fichier.
    pause
    exit /b 1
)

echo [2/4] Verification du fichier .env...
if not exist ".env" (
    echo  Aucun .env : creation a partir de .env.example avec des secrets aleatoires.
    powershell -NoProfile -Command ^
      "$r = { -join ((48..57)+(65..90)+(97..122) | Get-Random -Count 48 | %% {[char]$_}) };" ^
      "(Get-Content '.env.example') -replace '^JWT_SECRET=$', ('JWT_SECRET=' + (& $r)) -replace '^POSTGRES_PASSWORD=$', ('POSTGRES_PASSWORD=' + (& $r)) -replace '^GRAFANA_ADMIN_PASSWORD=$', ('GRAFANA_ADMIN_PASSWORD=' + (& $r)) | Set-Content -Encoding ascii '.env'"
    if errorlevel 1 (
        echo  ERREUR : impossible de creer .env
        pause
        exit /b 1
    )
)

set "PORT=8080"
for /f "tokens=1,* delims==" %%a in ('findstr /b "HTTP_PORT=" .env') do set "PORT=%%b"

echo [3/4] Construction et demarrage des conteneurs (la premiere fois : 10-20 min)...
docker compose up -d --build
if errorlevel 1 (
    echo  ERREUR : docker compose a echoue. Voir : docker compose logs
    pause
    exit /b 1
)

echo [4/4] Attente de l'API (http://localhost:%PORT%/api/v1/health/ready)...
set /a TRIES=0
:wait
set /a TRIES+=1
curl -fs "http://localhost:%PORT%/api/v1/health/ready" >nul 2>&1
if not errorlevel 1 goto ready
if %TRIES% GEQ 60 (
    echo  L'API ne repond pas encore. Etat des services :
    docker compose ps
    pause
    exit /b 1
)
timeout /t 5 /nobreak >nul
goto wait

:ready
echo.
echo  Tout est pret :
echo    Cartes de visite   : http://localhost:%PORT%/cards/
echo    Documentation API  : http://localhost:%PORT%/api/v1/docs
echo.
echo  Arreter   : docker compose down
echo  Journaux  : docker compose logs -f worker
echo.
if not defined NO_BROWSER start "" "http://localhost:%PORT%/cards/"
pause
