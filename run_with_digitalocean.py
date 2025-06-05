#!/usr/bin/env python3
"""
Script para ejecutar la aplicación PHI GIS localmente 
pero conectada a la base de datos de DigitalOcean
"""

import os
import sys

# Establecer el entorno de producción para usar DigitalOcean
os.environ['ENVIRONMENT'] = 'production'
# Pero forzar el inicio de Streamlit apps localmente
os.environ['FORCE_STREAMLIT_INIT'] = 'true'

# Configurar otras variables necesarias
os.environ['SECRET_KEY'] = 'local-dev-with-digitalocean-db'
os.environ['MAPBOX_TOKEN'] = 'pk.eyJ1IjoiaHBlcmV6Yzk3IiwiYSI6ImNtNXljaDc0cjBpNDMya3E1aGdzcjdpZnkifQ.9FBt1VDj52w2yw-7ewLU6Q'

print("Configurando aplicacion para usar base de datos de DigitalOcean...")
print("Ejecutando localmente en: http://localhost:8050")
print("Dashboard disponible en: http://localhost:8050/dashboard")
print("Health check en: http://localhost:8050/health")
print("Ctrl+C para detener")
print("-" * 60)

# Funciones para geoportal
def start_geoportal():
    """Iniciar geoportal backend y frontend"""
    processes = []
    
    # Configurar variables de entorno para geoportal
    os.environ['DB_USER'] = 'doadmin'
    os.environ['DB_PASSWORD'] = 'AVNS_nAsg-fcAlH1dOF3pzB_'
    os.environ['DB_HOST'] = 'db-postgresql-nyc1-96388-do-user-22908693-0.l.db.ondigitalocean.com'
    os.environ['DB_PORT'] = '25060'
    os.environ['DB_NAME'] = 'defaultdb'
    
    try:
        # Iniciar backend usando script específico
        print("Iniciando Geoportal Backend...")
        backend_script = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'start_geoportal_backend.py')
        if os.path.exists(backend_script):
            backend_cmd = [sys.executable, backend_script]
            backend_process = subprocess.Popen(backend_cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            processes.append(backend_process)
            print("Geoportal Backend: http://localhost:8000")
        else:
            print("Error: Script de backend no encontrado")
        
        # Iniciar frontend
        print("Iniciando Geoportal Frontend...")
        frontend_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'geoportal', 'frontend')
        if os.path.exists(frontend_dir):
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
            frontend_process = subprocess.Popen(frontend_cmd, cwd=frontend_dir, shell=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            processes.append(frontend_process)
            print("Geoportal Frontend: http://localhost:3000")
            
    except Exception as e:
        print(f"Error iniciando geoportal: {e}")
    
    return processes

def stop_geoportal(processes):
    """Detener procesos del geoportal"""
    for process in processes:
        try:
            process.terminate()
        except:
            pass

# Importar y ejecutar la aplicación principal
if __name__ == "__main__":
    import subprocess
    from main import create_main_app, create_dash_app, init_streamlit_apps, stop_streamlit_apps
    from werkzeug.middleware.dispatcher import DispatcherMiddleware
    from werkzeug.serving import run_simple
    import atexit
    
    # Variable global para procesos del geoportal
    geoportal_processes = []
    
    try:
        print("Iniciando aplicaciones Streamlit...")
        
        # Inicializar aplicaciones Streamlit
        init_streamlit_apps()
        
        # Inicializar geoportal
        print("Iniciando Geoportal...")
        geoportal_processes = start_geoportal()
        
        # Registrar funciones para detener al salir
        atexit.register(stop_streamlit_apps)
        atexit.register(lambda: stop_geoportal(geoportal_processes))
        
        # Crear aplicaciones
        main_app = create_main_app()
        
        if create_dash_app:
            print("Creando dashboard...")
            dash_app = create_dash_app()
            
            # Configurar dispatcher
            application = DispatcherMiddleware(main_app, {
                '/dashboard': dash_app.server
            })
        else:
            print("Dashboard no disponible")
            application = main_app
        
        print("\n" + "=" * 60)
        print("PLATAFORMA PHI GIS INICIADA")
        print("=" * 60)
        print("Servidor Principal: http://localhost:8050")
        print("Dashboard: http://localhost:8050/dashboard")
        print("ML Asistentes: http://localhost:8501")
        print("ML Temporal: http://localhost:8502") 
        print("ML Geografico: http://localhost:8503")
        if geoportal_processes:
            print("Geoportal Frontend: http://localhost:3000")
            print("Geoportal Backend: http://localhost:8000")
            print("API Docs: http://localhost:8000/docs")
        print("=" * 60)
        print("Presiona Ctrl+C para detener toda la plataforma")
        print("=" * 60)
        
        # Ejecutar servidor
        run_simple('localhost', 8050, application, 
                  use_reloader=False,  # False para evitar conflictos con Streamlit
                  use_debugger=True)
                  
    except KeyboardInterrupt:
        print("\nDeteniendo aplicaciones...")
        stop_streamlit_apps()
        stop_geoportal(geoportal_processes)
        print("Todas las aplicaciones detenidas")
    except Exception as e:
        print(f"Error: {e}")
        stop_streamlit_apps()
        stop_geoportal(geoportal_processes) 