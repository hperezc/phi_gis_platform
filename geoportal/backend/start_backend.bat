@echo off
echo Iniciando Backend del Geoportal...

set DB_USER=doadmin
set DB_PASSWORD=AVNS_nAsg-fcAlH1dOF3pzB_
set DB_HOST=db-postgresql-nyc1-96388-do-user-22908693-0.l.db.ondigitalocean.com
set DB_PORT=25060
set DB_NAME=defaultdb

echo Variables de entorno configuradas
echo Iniciando uvicorn...

uvicorn app.main:app --reload --host 0.0.0.0 --port 8000 