#!/bin/bash

echo "=== EJECUTANDO PHI GIS NATIVAMENTE SIN DOCKER ==="

# 1. Instalar Python y dependencias
echo ">>> Instalando Python y dependencias..."
sudo apt-get update
sudo apt-get install -y python3 python3-pip python3-venv redis-server

# 2. Crear entorno virtual
echo ">>> Creando entorno virtual..."
python3 -m venv venv
source venv/bin/activate

# 3. Instalar dependencias Python
echo ">>> Instalando dependencias Python..."
pip install --upgrade pip
pip install \
    flask \
    gunicorn \
    streamlit \
    psycopg2-binary \
    redis \
    requests \
    pandas \
    plotly \
    dash \
    werkzeug

# 4. Configurar Redis
echo ">>> Configurando Redis..."
sudo systemctl enable redis-server
sudo systemctl start redis-server

# 5. Configurar variables de entorno
echo ">>> Configurando variables de entorno..."
export ENVIRONMENT=production
export DATABASE_URL="postgresql://doadmin:AVNS_nAsg-fcAlH1dOF3pzB_@db-postgresql-nyc1-96388-do-user-22908693-0.l.db.ondigitalocean.com:25060/defaultdb?sslmode=require"
export MAPBOX_TOKEN="pk.eyJ1IjoiaHBlcmV6Yzk3IiwiYSI6ImNtNXljaDc0cjBpNDMya3E1aGdzcjdpZnkifQ.9FBt1VDj52w2yw-7ewLU6Q"
export SECRET_KEY="phi-gis-production-2024"
export PYTHONPATH=/opt/phi_gis_platform

# 6. Crear script de inicio
cat << 'EOF' > start_phi_native.sh
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
EOF

chmod +x start_phi_native.sh

# 7. Crear servicio systemd
sudo tee /etc/systemd/system/phi-gis.service << 'EOF'
[Unit]
Description=PHI GIS Platform
After=network.target redis.service

[Service]
Type=simple
User=root
WorkingDirectory=/opt/phi_gis_platform
Environment=ENVIRONMENT=production
Environment=DATABASE_URL=postgresql://doadmin:AVNS_nAsg-fcAlH1dOF3pzB_@db-postgresql-nyc1-96388-do-user-22908693-0.l.db.ondigitalocean.com:25060/defaultdb?sslmode=require
Environment=MAPBOX_TOKEN=pk.eyJ1IjoiaHBlcmV6Yzk3IiwiYSI6ImNtNXljaDc0cjBpNDMya3E1aGdzcjdpZnkifQ.9FBt1VDj52w2yw-7ewLU6Q
Environment=SECRET_KEY=phi-gis-production-2024
Environment=PYTHONPATH=/opt/phi_gis_platform
ExecStart=/opt/phi_gis_platform/venv/bin/python /opt/phi_gis_platform/main.py
Restart=always
RestartSec=3

[Install]
WantedBy=multi-user.target
EOF

# 8. Habilitar y iniciar servicio
sudo systemctl daemon-reload
sudo systemctl enable phi-gis
sudo systemctl start phi-gis

# 9. Verificar estado
echo ">>> Verificando servicios..."
sudo systemctl status redis-server
sudo systemctl status phi-gis

echo ""
echo "=== APLICACIÓN INICIADA ==="
echo "URL: http://45.55.212.201:8050"
echo "Para ver logs: sudo journalctl -u phi-gis -f"
echo "Para reiniciar: sudo systemctl restart phi-gis"
echo "Para detener: sudo systemctl stop phi-gis" 