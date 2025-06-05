@echo off
echo Iniciando Plataforma PHI GIS...

REM Abrir terminal para backend
start "Backend Geoportal" cmd /k "cd geoportal\backend && set DB_USER=doadmin && set DB_PASSWORD=AVNS_nAsg-fcAlH1dOF3pzB_ && set DB_HOST=db-postgresql-nyc1-96388-do-user-22908693-0.l.db.ondigitalocean.com && set DB_PORT=25060 && set DB_NAME=defaultdb && python -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8000"

REM Esperar 5 segundos
timeout /t 5

REM Abrir terminal para frontend
start "Frontend Geoportal" cmd /k "cd geoportal\frontend && npm run dev"

REM Esperar 10 segundos
timeout /t 10

REM Abrir terminal para app principal
start "App Principal" cmd /k "python run_with_digitalocean.py"

echo.
echo ====================================================
echo PLATAFORMA PHI GIS INICIADA
echo ====================================================
echo Backend Geoportal: http://localhost:8000
echo Frontend Geoportal: http://localhost:3000
echo App Principal: http://localhost:8050
echo Dashboard: http://localhost:8050/dashboard
echo ML Asistentes: http://localhost:8501
echo ML Temporal: http://localhost:8502
echo ML Geografico: http://localhost:8503
echo ====================================================
echo Presiona cualquier tecla para cerrar esta ventana
pause 