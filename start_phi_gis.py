#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Script simple para iniciar la plataforma PHI GIS con DigitalOcean
"""

import os
import sys
import subprocess
import time

# Configurar codificación
os.environ['PYTHONIOENCODING'] = 'utf-8'

# Configurar variables de entorno para DigitalOcean
os.environ['ENVIRONMENT'] = 'production'
os.environ['DATABASE_URL'] = 'postgresql://doadmin:AVNS_nAsg-fcAlH1dOF3pzB_@db-postgresql-nyc1-96388-do-user-22908693-0.l.db.ondigitalocean.com:25060/defaultdb?sslmode=require'
os.environ['SECRET_KEY'] = 'phi-gis-digitalocean-local'
os.environ['MAPBOX_TOKEN'] = 'pk.eyJ1IjoiaHBlcmV6Yzk3IiwiYSI6ImNtNXljaDc0cjBpNDMya3E1aGdzcjdqZnkifQ.9FBt1VDj52w2yw-7ewLU6Q'

print("=" * 60)
print("INICIANDO PLATAFORMA PHI GIS CON DIGITALOCEAN")
print("=" * 60)
print("Base de datos: DigitalOcean PostgreSQL + PostGIS")
print("Entorno: Desarrollo local con BD en la nube")
print("=" * 60)

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
            print(f"{app['name']}: http://localhost:{app['port']}")
        else:
            print(f"No se encontro {app['file']}")
    
    return processes

def start_geoportal():
    """Inicia el geoportal completo (backend + frontend)"""
    processes = []
    
    try:
        # Configurar variables de entorno para el geoportal
        os.environ['DB_USER'] = 'doadmin'
        os.environ['DB_PASSWORD'] = 'AVNS_nAsg-fcAlH1dOF3pzB_'
        os.environ['DB_HOST'] = 'db-postgresql-nyc1-96388-do-user-22908693-0.l.db.ondigitalocean.com'
        os.environ['DB_PORT'] = '25060'
        os.environ['DB_NAME'] = 'defaultdb'
        
        # Iniciar Backend (FastAPI)
        print("Iniciando Geoportal backend...")
        backend_dir = os.path.join(os.getcwd(), 'geoportal', 'backend')
        
        if os.path.exists(backend_dir):
            # Usar shell=True y cd para asegurar el directorio de trabajo correcto
            backend_cmd = f'cd "{backend_dir}" && python -m uvicorn app.main:app --host 0.0.0.0 --port 8000'
            
            backend_process = subprocess.Popen(
                backend_cmd,
                shell=True,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL
            )
            processes.append(backend_process)
            print("Backend iniciado: http://localhost:8000")
        else:
            print("No se encontro directorio backend del geoportal")
            
        # Iniciar Frontend (Next.js)
        print("Iniciando Geoportal frontend...")
        frontend_dir = os.path.join(os.getcwd(), 'geoportal', 'frontend')
        
        if os.path.exists(frontend_dir):
            # Verificar si existe package.json
            package_json = os.path.join(frontend_dir, 'package.json')
            if os.path.exists(package_json):
                # En Windows, usar npm.cmd en lugar de npm
                npm_cmd = 'npm.cmd' if os.name == 'nt' else 'npm'
                
                # Verificar si existen node_modules, si no, instalar dependencias
                node_modules_dir = os.path.join(frontend_dir, 'node_modules')
                if not os.path.exists(node_modules_dir):
                    print("Instalando dependencias del frontend...")
                    install_cmd = [npm_cmd, 'install', '--legacy-peer-deps']
                    subprocess.run(install_cmd, cwd=frontend_dir, shell=True, capture_output=True)
                    print("Dependencias instaladas")
                
                frontend_cmd = [npm_cmd, 'run', 'dev']
                
                frontend_process = subprocess.Popen(
                    frontend_cmd,
                    cwd=frontend_dir,
                    shell=True,
                    stdout=subprocess.DEVNULL,
                    stderr=subprocess.DEVNULL
                )
                processes.append(frontend_process)
                print("Frontend iniciado: http://localhost:3000")
            else:
                print("package.json no encontrado en frontend")
        else:
            print("No se encontro directorio frontend del geoportal")
        
        if processes:
            print("API Docs: http://localhost:8000/docs")
        
        return processes
        
    except Exception as e:
        print(f"Error iniciando geoportal: {e}")
        return []

def start_main_app():
    """Inicia la aplicación principal Flask + Dashboard"""
    try:
        print("Iniciando aplicacion principal (Flask + Dashboard)...")
        
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
        
        print("Aplicacion principal: http://localhost:8050")
        print("Dashboard: http://localhost:8050/dashboard")
        print("Health check: http://localhost:8050/health")
        
        # Ejecutar servidor
        run_simple('localhost', 8050, application, 
                  use_reloader=False,
                  use_debugger=False,
                  threaded=True)
                  
    except Exception as e:
        print(f"Error iniciando aplicacion principal: {e}")
        return False

def main():
    streamlit_processes = []
    geoportal_processes = []
    
    try:
        # Iniciar aplicaciones Streamlit
        streamlit_processes = start_streamlit_apps()
        
        # Iniciar geoportal
        geoportal_processes = start_geoportal()
        
        print(f"Iniciados {len(streamlit_processes)} aplicativos ML")
        if geoportal_processes:
            print(f"Geoportal iniciado con {len(geoportal_processes)} servicios")
        print("Esperando 8 segundos para que inicien...")
        time.sleep(8)
        
        print("=" * 60)
        print("URLS DE ACCESO:")
        print("=" * 60)
        print("App Principal: http://localhost:8050")
        print("Dashboard: http://localhost:8050/dashboard") 
        print("ML Asistentes: http://localhost:8501")
        print("ML Temporal: http://localhost:8502")
        print("ML Geografico: http://localhost:8503")
        if geoportal_processes:
            print("Geoportal Frontend: http://localhost:3000")
            print("Geoportal API: http://localhost:8000")
            print("API Docs: http://localhost:8000/docs")
        print("=" * 60)
        print("Presiona Ctrl+C para detener")
        print("=" * 60)
        
        # Iniciar aplicación principal (esto bloquea hasta Ctrl+C)
        start_main_app()
        
    except KeyboardInterrupt:
        print("\nDeteniendo aplicaciones...")
        
        # Terminar procesos Streamlit
        for process in streamlit_processes:
            try:
                process.terminate()
            except:
                pass
        
        # Terminar procesos geoportal
        for process in geoportal_processes:
            try:
                process.terminate()
            except:
                pass
        
        print("Aplicaciones detenidas")
    
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    main() 