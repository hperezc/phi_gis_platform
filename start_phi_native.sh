#!/bin/bash
cd /opt/phi_gis_platform
source venv/bin/activate

export ENVIRONMENT=production
export DATABASE_URL="postgresql://doadmin:AVNS_nAsg-fcAlH1dOF3pzB_@db-postgresql-nyc1-96388-do-user-22908693-0.l.db.ondigitalocean.com:25060/defaultdb?sslmode=require"
export MAPBOX_TOKEN="pk.eyJ1IjoiaHBlcmV6Yzk3IiwiYSI6ImNtNXljaDc0cjBpNDMya3E1aGdzcjdpZnkifQ.9FBt1VDj52w2yw-7ewLU6Q"
export SECRET_KEY="phi-gis-production-2024"
export PYTHONPATH=/opt/phi_gis_platform

echo "Iniciando PHI GIS Platform nativo..."
echo "URL: http://45.55.212.201:8050"

python3 main.py
