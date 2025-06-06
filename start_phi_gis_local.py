#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Script para iniciar la plataforma PHI GIS con BASE DE DATOS LOCAL
"""

import os
import sys
import subprocess
import time
from dotenv import load_dotenv

# Configurar codificación
os.environ['PYTHONIOENCODING'] = 'utf-8'

# CONFIGURACIÓN PARA BASE DE DATOS LOCAL
os.environ['ENVIRONMENT'] = 'development'  # Usar 'development' para BD local
os.environ['DATABASE_URL'] = 'postgresql://postgres:0000@localhost:5432/bd_actividades_historicas'
os.environ['SECRET_KEY'] = 'phi-gis-local-development'
os.environ['MAPBOX_TOKEN'] = 'pk.eyJ1IjoiaHBlcmV6Yzk3IiwiYSI6ImNtNXljaDc0cjBpNDMya3E1aGdzcjdqZnkifQ.9FBt1VDj52w2yw-7ewLU6Q'

# Variables para geoportal con BD local
os.environ['DB_USER'] = 'postgres'
os.environ['DB_PASSWORD'] = '0000'
os.environ['DB_HOST'] = 'localhost'
os.environ['DB_PORT'] = '5432'
os.environ['DB_NAME'] = 'bd_actividades_historicas'

print("=" * 60)
print("INICIANDO PLATAFORMA PHI GIS CON BASE DE DATOS LOCAL")
print("=" * 60)
print("Base de datos: PostgreSQL Local (localhost:5432)")
print("BD: bd_actividades_historicas")
print("Usuario: postgres")
print("Entorno: Desarrollo local")
print("=" * 60)

def check_database_connection():
    """Verificar conexión a la base de datos local"""
    try:
        import psycopg2
        conn = psycopg2.connect(
            host='localhost',
            port='5432',
            database='bd_actividades_historicas',
            user='postgres',
            password='0000'
        )
        conn.close()
        print("✅ Conexión a base de datos local exitosa")
        return True
    except Exception as e:
        print(f"❌ Error conectando a BD local: {e}")
        print("Verifica que PostgreSQL esté ejecutándose y la BD exista")
        return False

def start_streamlit_apps():
    """Inicia las aplicaciones Streamlit"""
    ml_dir = os.path.join(os.getcwd(), 'ml_module', 'ml_module')
    
    apps = [
        {'name': 'ML Asistentes', 'file': 'app.py', 'port': 8501},
        {'name': 'ML Temporal', 'file': 'temporal_analysis/app_temporal.py', 'port': 8502},
        {'name': 'ML Geografico', 'file': 'geographic_analysis/app_geographic.py', 'port': 8503}
    ]
    
    processes = []
    
    for app in apps:
        app_file = os.path.join(ml_dir, app['file'])
        if os.path.exists(app_file):
            print(f"Iniciando {app['name']} en puerto {app['port']}...")
            cmd = [
                sys.executable, '-m', 'streamlit', 'run', 
                app_file,
                '--server.port', str(app['port']),
                '--server.headless', 'true',
                '--server.address', '0.0.0.0'
            ]
            
            process = subprocess.Popen(
                cmd,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL
            )
            processes.append(process)
            print(f"✅ {app['name']}: http://localhost:{app['port']}")
        else:
            print(f"❌ No se encontró {app['file']}")
    
    return processes

def start_geoportal():
    """Inicia el geoportal con BD local"""
    processes = []
    
    try:
        print("Iniciando Geoportal con BD local...")
        
        # Iniciar Backend (FastAPI)
        backend_dir = os.path.join(os.getcwd(), 'geoportal', 'backend')
        
        if os.path.exists(backend_dir):
            print("Iniciando Geoportal backend...")
            backend_cmd = f'cd "{backend_dir}" && python -m uvicorn app.main:app --host 0.0.0.0 --port 8000'
            
            backend_process = subprocess.Popen(
                backend_cmd,
                shell=True,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL
            )
            processes.append(backend_process)
            print("✅ Backend iniciado: http://localhost:8000")
        else:
            print("❌ No se encontró directorio backend del geoportal")
            
        # Iniciar Frontend (Next.js)
        frontend_dir = os.path.join(os.getcwd(), 'geoportal', 'frontend')
        
        if os.path.exists(frontend_dir):
            package_json = os.path.join(frontend_dir, 'package.json')
            if os.path.exists(package_json):
                npm_cmd = 'npm.cmd' if os.name == 'nt' else 'npm'
                
                # Verificar node_modules
                node_modules_dir = os.path.join(frontend_dir, 'node_modules')
                if not os.path.exists(node_modules_dir):
                    print("📦 Instalando dependencias del frontend...")
                    install_cmd = [npm_cmd, 'install', '--legacy-peer-deps']
                    subprocess.run(install_cmd, cwd=frontend_dir, shell=True)
                    print("✅ Dependencias instaladas")
                
                print("Iniciando Geoportal frontend...")
                frontend_cmd = [npm_cmd, 'run', 'dev']
                
                frontend_process = subprocess.Popen(
                    frontend_cmd,
                    cwd=frontend_dir,
                    shell=True,
                    stdout=subprocess.DEVNULL,
                    stderr=subprocess.DEVNULL
                )
                processes.append(frontend_process)
                print("✅ Frontend iniciado: http://localhost:3000")
            else:
                print("❌ package.json no encontrado en frontend")
        else:
            print("❌ No se encontró directorio frontend del geoportal")
        
        return processes
        
    except Exception as e:
        print(f"❌ Error iniciando geoportal: {e}")
        return []

def start_main_app():
    """Inicia la aplicación principal Flask + Dashboard"""
    try:
        print("Iniciando aplicación principal (Flask + Dashboard)...")
        
        # Importar después de configurar variables de entorno
        from main import create_main_app
        from Dashboard_BD_PHI.dashboard.app import create_dash_app
        from werkzeug.middleware.dispatcher import DispatcherMiddleware
        from werkzeug.serving import run_simple
        
        # Crear aplicaciones
        main_app = create_main_app()
        dash_app = create_dash_app()
        
        # Configurar dispatcher
        application = DispatcherMiddleware(main_app, {
            '/dashboard': dash_app.server
        })
        
        print("✅ Aplicación principal: http://localhost:8050")
        print("✅ Dashboard: http://localhost:8050/dashboard")
        print("✅ Health check: http://localhost:8050/health")
        
        # Ejecutar servidor
        run_simple('localhost', 8050, application, 
                  use_reloader=False,
                  use_debugger=False,
                  threaded=True)
                  
    except Exception as e:
        print(f"❌ Error iniciando aplicación principal: {e}")
        return False

def main():
    # Verificar conexión a BD antes de continuar
    if not check_database_connection():
        print("\n❌ No se puede conectar a la base de datos local.")
        print("Asegúrate de que:")
        print("1. PostgreSQL esté ejecutándose")
        print("2. La base de datos 'bd_actividades_historicas' exista")
        print("3. El usuario 'postgres' tenga acceso")
        print("4. La contraseña sea '0000'")
        return
    
    streamlit_processes = []
    geoportal_processes = []
    
    try:
        # Iniciar aplicaciones Streamlit
        streamlit_processes = start_streamlit_apps()
        
        # Iniciar geoportal
        geoportal_processes = start_geoportal()
        
        print(f"\n✅ Iniciados {len(streamlit_processes)} aplicativos ML")
        if geoportal_processes:
            print(f"✅ Geoportal iniciado con {len(geoportal_processes)} servicios")
        print("⏳ Esperando 8 segundos para que todos los servicios inicien...")
        time.sleep(8)
        
        print("\n" + "=" * 60)
        print("🎉 PLATAFORMA PHI GIS INICIADA CON BD LOCAL")
        print("=" * 60)
        print("🏠 App Principal: http://localhost:8050")
        print("📊 Dashboard: http://localhost:8050/dashboard") 
        print("🤖 ML Asistentes: http://localhost:8501")
        print("📈 ML Temporal: http://localhost:8502")
        print("🗺️ ML Geográfico: http://localhost:8503")
        if geoportal_processes:
            print("🌍 Geoportal Frontend: http://localhost:3000")
            print("📡 Geoportal API: http://localhost:8000")
            print("📖 API Docs: http://localhost:8000/docs")
        print("=" * 60)
        print("⏹️ Presiona Ctrl+C para detener toda la plataforma")
        print("=" * 60)
        
        # Iniciar aplicación principal (esto mantiene el proceso vivo)
        start_main_app()
        
    except KeyboardInterrupt:
        print("\n🛑 Deteniendo plataforma...")
        for process in streamlit_processes + geoportal_processes:
            try:
                process.terminate()
            except:
                pass
        print("✅ Plataforma detenida")

if __name__ == "__main__":
    main() 