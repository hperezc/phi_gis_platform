#!/usr/bin/env python3
"""
Script maestro para ejecutar TODA la plataforma PHI GIS con DigitalOcean
Incluye: Main App + Dashboard + 3 ML Apps + Geoportal
"""

import os
import sys
import subprocess
import time
import threading
from pathlib import Path
import psutil

# Configurar variables de entorno para DigitalOcean
os.environ['ENVIRONMENT'] = 'production'
os.environ['DATABASE_URL'] = 'postgresql://doadmin:AVNS_nAsg-fcAlH1dOF3pzB_@db-postgresql-nyc1-96388-do-user-22908693-0.l.db.ondigitalocean.com:25060/defaultdb?sslmode=require'
os.environ['DB_USER'] = 'doadmin'
os.environ['DB_PASSWORD'] = 'AVNS_nAsg-fcAlH1dOF3pzB_'
os.environ['DB_HOST'] = 'db-postgresql-nyc1-96388-do-user-22908693-0.l.db.ondigitalocean.com'
os.environ['DB_PORT'] = '25060'
os.environ['DB_NAME'] = 'defaultdb'
os.environ['SECRET_KEY'] = 'phi-gis-digitalocean-local-dev'
os.environ['MAPBOX_TOKEN'] = 'pk.eyJ1IjoiaHBlcmV6Yzk3IiwiYSI6ImNtNXljaDc0cjBpNDMya3E1aGdzcjdqZnkifQ.9FBt1VDj52w2yw-7ewLU6Q'

# Variables globales para procesos
processes = {}

def kill_port_processes(port):
    """Mata procesos que estén usando un puerto específico"""
    try:
        for proc in psutil.process_iter(['pid', 'name', 'connections']):
            try:
                for conn in proc.info['connections'] or []:
                    if conn.laddr.port == port:
                        print(f"🔪 Limpiando puerto {port} - proceso {proc.info['name']} (PID: {proc.info['pid']})")
                        proc.kill()
            except (psutil.NoSuchProcess, psutil.AccessDenied):
                pass
    except Exception as e:
        print(f"⚠️ Error limpiando puerto {port}: {e}")

def start_main_app():
    """Inicia la aplicación principal con dashboard"""
    try:
        print("🏠 Iniciando aplicación principal (Flask + Dashboard)...")
        
        # Limpiar puerto 8050
        kill_port_processes(8050)
        time.sleep(1)
        
        process = subprocess.Popen(
            [sys.executable, 'run_with_digitalocean.py'],
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            bufsize=1
        )
        
        processes['main_app'] = process
        print("✅ Main App + Dashboard iniciado en http://localhost:8050")
        return True
        
    except Exception as e:
        print(f"❌ Error iniciando main app: {e}")
        return False

def start_geoportal():
    """Inicia el geoportal backend"""
    try:
        print("🌍 Iniciando geoportal backend...")
        
        # Limpiar puerto 8000
        kill_port_processes(8000)
        time.sleep(1)
        
        backend_dir = Path(os.getcwd()) / 'geoportal' / 'backend'
        
        if not backend_dir.exists():
            print("⚠️ No se encontró directorio del geoportal")
            return False
        
        # Comando para ejecutar FastAPI
        cmd = [sys.executable, '-m', 'uvicorn', 'app.main:app', '--host', '0.0.0.0', '--port', '8000']
        
        process = subprocess.Popen(
            cmd,
            cwd=backend_dir,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            bufsize=1
        )
        
        processes['geoportal'] = process
        print("✅ Geoportal backend iniciado en http://localhost:8000")
        return True
        
    except Exception as e:
        print(f"❌ Error iniciando geoportal: {e}")
        return False

def monitor_process(process, name):
    """Monitorea la salida de un proceso"""
    if process:
        try:
            for line in iter(process.stdout.readline, ''):
                if line:
                    # Solo mostrar líneas importantes para evitar spam
                    if any(keyword in line.lower() for keyword in ['error', 'exception', 'failed', 'critical', 'started', 'running']):
                        print(f"[{name}] {line.strip()}")
        except Exception:
            pass

def cleanup():
    """Limpia todos los procesos al salir"""
    print("\n🛑 Deteniendo toda la plataforma PHI GIS...")
    
    for name, process in processes.items():
        if process:
            print(f"🔧 Deteniendo {name}...")
            try:
                process.terminate()
                process.wait(timeout=5)
            except subprocess.TimeoutExpired:
                process.kill()
            except Exception:
                pass
    
    # Limpiar puertos
    ports_to_clean = [8050, 8000, 8501, 8502, 8503, 3000]
    for port in ports_to_clean:
        kill_port_processes(port)
    
    print("✅ Plataforma PHI GIS detenida completamente")

def wait_for_service(url, name, timeout=30):
    """Espera a que un servicio esté disponible"""
    try:
        import requests
        start_time = time.time()
        
        while time.time() - start_time < timeout:
            try:
                response = requests.get(url, timeout=5)
                if response.status_code == 200:
                    return True
            except:
                pass
            time.sleep(2)
        
        return False
    except ImportError:
        print("⚠️ requests no disponible para verificar servicios")
        time.sleep(5)  # Esperar un poco sin verificar
        return True

def main():
    """Función principal"""
    print("🚀 INICIANDO PLATAFORMA PHI GIS COMPLETA CON DIGITALOCEAN")
    print("=" * 70)
    
    # Registrar función de limpieza
    import atexit
    atexit.register(cleanup)
    
    try:
        results = {}
        
        # Paso 1: Iniciar aplicación principal (incluye Streamlit apps)
        results['main_app'] = start_main_app()
        
        if results['main_app']:
            print("⏳ Esperando a que la aplicación principal inicie...")
            if wait_for_service('http://localhost:8050/health', 'Main App'):
                print("💚 Main App health check: OK")
            time.sleep(5)  # Dar tiempo a las apps de Streamlit
        
        # Paso 2: Iniciar geoportal
        results['geoportal'] = start_geoportal()
        
        if results['geoportal']:
            print("⏳ Esperando a que el geoportal inicie...")
            time.sleep(3)
        
        # Mostrar resumen
        print("\n" + "=" * 70)
        print("🎉 PLATAFORMA PHI GIS INICIADA")
        print("=" * 70)
        
        if results['main_app']:
            print("🏠 App Principal: http://localhost:8050")
            print("📊 Dashboard: http://localhost:8050/dashboard")
            print("💚 Health Check: http://localhost:8050/health")
            print("🤖 ML Asistentes: http://localhost:8501")
            print("📈 ML Temporal: http://localhost:8502")
            print("🗺️ ML Geográfico: http://localhost:8503")
        
        if results['geoportal']:
            print("🌍 Geoportal API: http://localhost:8000")
            print("📋 API Docs: http://localhost:8000/docs")
        
        total_services = sum(results.values())
        print(f"\n🎯 {total_services}/2 servicios principales iniciados")
        print("📊 Base de datos: DigitalOcean PostgreSQL + PostGIS")
        print("📍 4,960 actividades históricas disponibles")
        
        print("\n🔄 Presiona Ctrl+C para detener toda la plataforma")
        print("=" * 70)
        
        # Iniciar monitores de procesos
        threads = []
        for name, process in processes.items():
            if process:
                thread = threading.Thread(
                    target=monitor_process,
                    args=(process, name.replace('_', ' ').title()),
                    daemon=True
                )
                thread.start()
                threads.append(thread)
        
        # Mantener el script corriendo
        try:
            while True:
                time.sleep(1)
                
                # Verificar si los procesos siguen vivos
                for name, process in processes.items():
                    if process and process.poll() is not None:
                        print(f"❌ {name} se detuvo inesperadamente")
                        return False
        
        except KeyboardInterrupt:
            print("\n🛑 Interrupción recibida...")
        
        cleanup()
        return True
        
    except Exception as e:
        print(f"❌ Error crítico: {e}")
        cleanup()
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1) 