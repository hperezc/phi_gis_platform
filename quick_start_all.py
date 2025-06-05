#!/usr/bin/env python3
"""
Script simple y confiable para iniciar toda la plataforma PHI GIS
"""
import os
import sys
import subprocess
import time

# Configurar variables de entorno para DigitalOcean
os.environ['ENVIRONMENT'] = 'production'
os.environ['FORCE_STREAMLIT_INIT'] = 'true'
os.environ['DATABASE_URL'] = 'postgresql://doadmin:AVNS_nAsg-fcAlH1dOF3pzB_@db-postgresql-nyc1-96388-do-user-22908693-0.l.db.ondigitalocean.com:25060/defaultdb?sslmode=require'
os.environ['SECRET_KEY'] = 'phi-gis-digitalocean-local'
os.environ['MAPBOX_TOKEN'] = 'pk.eyJ1IjoiaHBlcmV6Yzk3IiwiYSI6ImNtNXljaDc0cjBpNDMya3E1aGdzcjdpZnkifQ.9FBt1VDj52w2yw-7ewLU6Q'

# Variables para geoportal
os.environ['DB_USER'] = 'doadmin'
os.environ['DB_PASSWORD'] = 'AVNS_nAsg-fcAlH1dOF3pzB_'
os.environ['DB_HOST'] = 'db-postgresql-nyc1-96388-do-user-22908693-0.l.db.ondigitalocean.com'
os.environ['DB_PORT'] = '25060'
os.environ['DB_NAME'] = 'defaultdb'

def start_backend_manually():
    """Iniciar backend del geoportal manualmente"""
    print("📡 Iniciando backend del geoportal...")
    backend_dir = os.path.join(os.getcwd(), 'geoportal', 'backend')
    
    # Crear un script batch temporal para Windows
    batch_content = f"""@echo off
cd /d "{backend_dir}"
set DB_USER=doadmin
set DB_PASSWORD=AVNS_nAsg-fcAlH1dOF3pzB_
set DB_HOST=db-postgresql-nyc1-96388-do-user-22908693-0.l.db.ondigitalocean.com
set DB_PORT=25060
set DB_NAME=defaultdb
python -m uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
"""
    
    batch_file = os.path.join(os.getcwd(), 'temp_backend.bat')
    with open(batch_file, 'w') as f:
        f.write(batch_content)
    
    # Ejecutar el script batch
    try:
        process = subprocess.Popen(batch_file, shell=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        return process
    except Exception as e:
        print(f"Error: {e}")
        return None

def start_frontend_manually():
    """Iniciar frontend del geoportal manualmente"""
    print("🎨 Iniciando frontend del geoportal...")
    frontend_dir = os.path.join(os.getcwd(), 'geoportal', 'frontend')
    
    # Verificar node_modules
    node_modules = os.path.join(frontend_dir, 'node_modules')
    if not os.path.exists(node_modules):
        print("📦 Instalando dependencias...")
        subprocess.run(['npm', 'install', '--legacy-peer-deps'], cwd=frontend_dir, shell=True)
    
    # Iniciar frontend
    try:
        process = subprocess.Popen(['npm', 'run', 'dev'], cwd=frontend_dir, shell=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        return process
    except Exception as e:
        print(f"Error: {e}")
        return None

def main():
    processes = []
    
    try:
        print("🚀 INICIANDO PLATAFORMA PHI GIS COMPLETA")
        print("=" * 60)
        
        # 1. Iniciar backend del geoportal
        backend_process = start_backend_manually()
        if backend_process:
            processes.append(backend_process)
            print("✅ Backend iniciado: http://localhost:8000")
            time.sleep(3)
        
        # 2. Iniciar frontend del geoportal
        frontend_process = start_frontend_manually()
        if frontend_process:
            processes.append(frontend_process)
            print("✅ Frontend iniciado: http://localhost:3000")
            time.sleep(5)
        
        # 3. Iniciar aplicación principal con Streamlit
        print("🎯 Iniciando aplicación principal...")
        main_cmd = [sys.executable, 'run_with_digitalocean.py']
        main_process = subprocess.Popen(main_cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        processes.append(main_process)
        
        print("\n" + "=" * 60)
        print("🎉 PLATAFORMA PHI GIS INICIADA")
        print("=" * 60)
        print("🏠 App Principal: http://localhost:8050")
        print("📊 Dashboard: http://localhost:8050/dashboard")
        print("🤖 ML Asistentes: http://localhost:8501")
        print("📈 ML Temporal: http://localhost:8502")
        print("🗺️ ML Geográfico: http://localhost:8503")
        print("🌍 Geoportal Frontend: http://localhost:3000")
        print("📡 Geoportal Backend: http://localhost:8000")
        print("=" * 60)
        print("⏹️ Presiona Ctrl+C para detener toda la plataforma")
        print("=" * 60)
        
        # Mantener vivo
        while True:
            time.sleep(1)
    
    except KeyboardInterrupt:
        print("\n🛑 Deteniendo plataforma...")
        for process in processes:
            try:
                process.terminate()
            except:
                pass
        
        # Limpiar archivo temporal
        temp_file = os.path.join(os.getcwd(), 'temp_backend.bat')
        if os.path.exists(temp_file):
            os.remove(temp_file)
        
        print("✅ Plataforma detenida")

if __name__ == "__main__":
    main() 