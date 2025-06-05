#!/usr/bin/env python3
"""
Script para ejecutar el geoportal completo con DigitalOcean
Inicia automáticamente backend (FastAPI) y frontend
"""

import os
import sys
import subprocess
import time
import threading
from pathlib import Path
import psutil
import signal

# Configurar variables de entorno para DigitalOcean
os.environ['ENVIRONMENT'] = 'production'
os.environ['DB_USER'] = 'doadmin'
os.environ['DB_PASSWORD'] = 'AVNS_nAsg-fcAlH1dOF3pzB_'
os.environ['DB_HOST'] = 'db-postgresql-nyc1-96388-do-user-22908693-0.l.db.ondigitalocean.com'
os.environ['DB_PORT'] = '25060'
os.environ['DB_NAME'] = 'defaultdb'

# Variables globales para procesos
backend_process = None
frontend_process = None

def kill_port_processes(port):
    """Mata procesos que estén usando un puerto específico"""
    try:
        for proc in psutil.process_iter(['pid', 'name', 'connections']):
            try:
                for conn in proc.info['connections'] or []:
                    if conn.laddr.port == port:
                        print(f"🔪 Matando proceso {proc.info['name']} (PID: {proc.info['pid']}) en puerto {port}")
                        proc.kill()
            except (psutil.NoSuchProcess, psutil.AccessDenied):
                pass
    except Exception as e:
        print(f"⚠️ Error limpiando puerto {port}: {e}")

def start_backend():
    """Inicia el backend FastAPI del geoportal"""
    global backend_process
    
    try:
        print("🔧 Iniciando backend del geoportal...")
        
        # Limpiar puerto 8000
        kill_port_processes(8000)
        time.sleep(2)
        
        # Cambiar al directorio del backend
        backend_dir = Path(os.getcwd()) / 'geoportal' / 'backend'
        
        # Comando para ejecutar FastAPI
        if os.name == 'nt':  # Windows
            cmd = ['python', '-m', 'uvicorn', 'app.main:app', '--host', '0.0.0.0', '--port', '8000', '--reload']
        else:  # Linux/Mac
            cmd = ['uvicorn', 'app.main:app', '--host', '0.0.0.0', '--port', '8000', '--reload']
        
        backend_process = subprocess.Popen(
            cmd,
            cwd=backend_dir,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            bufsize=1,
            universal_newlines=True
        )
        
        print("✅ Backend iniciado en http://localhost:8000")
        return True
        
    except Exception as e:
        print(f"❌ Error iniciando backend: {e}")
        return False

def start_frontend():
    """Inicia el frontend del geoportal"""
    global frontend_process
    
    try:
        print("🎨 Iniciando frontend del geoportal...")
        
        # Limpiar puerto 3000
        kill_port_processes(3000)
        time.sleep(2)
        
        # Cambiar al directorio del frontend
        frontend_dir = Path(os.getcwd()) / 'geoportal' / 'frontend'
        
        # Verificar si existe package.json
        package_json = frontend_dir / 'package.json'
        if not package_json.exists():
            print("⚠️ No se encontró package.json en el frontend")
            print("💡 El frontend podría no estar configurado")
            return False
        
        # Comando para ejecutar el frontend
        if os.name == 'nt':  # Windows
            cmd = ['npm', 'run', 'dev']
        else:  # Linux/Mac
            cmd = ['npm', 'run', 'dev']
        
        frontend_process = subprocess.Popen(
            cmd,
            cwd=frontend_dir,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            bufsize=1,
            universal_newlines=True
        )
        
        print("✅ Frontend iniciado en http://localhost:3000")
        return True
        
    except Exception as e:
        print(f"❌ Error iniciando frontend: {e}")
        return False

def monitor_process(process, name):
    """Monitorea la salida de un proceso"""
    if process:
        try:
            for line in iter(process.stdout.readline, ''):
                if line:
                    print(f"[{name}] {line.strip()}")
        except Exception:
            pass

def cleanup():
    """Limpia los procesos al salir"""
    global backend_process, frontend_process
    
    print("\n🛑 Deteniendo geoportal...")
    
    if backend_process:
        print("🔧 Deteniendo backend...")
        try:
            backend_process.terminate()
            backend_process.wait(timeout=5)
        except subprocess.TimeoutExpired:
            backend_process.kill()
        except Exception:
            pass
    
    if frontend_process:
        print("🎨 Deteniendo frontend...")
        try:
            frontend_process.terminate()
            frontend_process.wait(timeout=5)
        except subprocess.TimeoutExpired:
            frontend_process.kill()
        except Exception:
            pass
    
    # Limpiar puertos
    kill_port_processes(8000)
    kill_port_processes(3000)
    
    print("✅ Geoportal detenido")

def test_backend_health():
    """Verifica que el backend esté funcionando"""
    try:
        import requests
        time.sleep(3)  # Esperar a que inicie
        
        response = requests.get('http://localhost:8000/health', timeout=5)
        if response.status_code == 200:
            print("💚 Backend health check: OK")
            return True
        else:
            print(f"⚠️ Backend health check failed: {response.status_code}")
            return False
    except Exception as e:
        print(f"⚠️ No se pudo verificar backend: {e}")
        return False

def main():
    """Función principal"""
    print("🚀 INICIANDO GEOPORTAL COMPLETO CON DIGITALOCEAN")
    print("=" * 60)
    
    # Registrar función de limpieza
    import atexit
    atexit.register(cleanup)
    
    # Configurar manejador de señales
    signal.signal(signal.SIGINT, lambda s, f: cleanup())
    signal.signal(signal.SIGTERM, lambda s, f: cleanup())
    
    try:
        # Paso 1: Verificar directorios
        backend_dir = Path(os.getcwd()) / 'geoportal' / 'backend'
        frontend_dir = Path(os.getcwd()) / 'geoportal' / 'frontend'
        
        if not backend_dir.exists():
            print(f"❌ No se encontró directorio backend: {backend_dir}")
            return False
        
        if not frontend_dir.exists():
            print(f"⚠️ No se encontró directorio frontend: {frontend_dir}")
            print("💡 Solo se iniciará el backend")
        
        # Paso 2: Iniciar backend
        if not start_backend():
            print("❌ Fallo iniciando backend")
            return False
        
        # Paso 3: Verificar backend
        if test_backend_health():
            print("✅ Backend funcionando correctamente")
        
        # Paso 4: Iniciar frontend (si existe)
        frontend_started = False
        if frontend_dir.exists():
            frontend_started = start_frontend()
        
        # Paso 5: Mostrar información
        print("\n" + "=" * 60)
        print("🎉 GEOPORTAL INICIADO")
        print("=" * 60)
        print("🔧 Backend (FastAPI): http://localhost:8000")
        print("📋 API Docs: http://localhost:8000/docs")
        print("💚 Health Check: http://localhost:8000/health")
        
        if frontend_started:
            print("🎨 Frontend: http://localhost:3000")
        else:
            print("⚠️ Frontend no disponible")
        
        print("\n🔄 Presiona Ctrl+C para detener")
        print("=" * 60)
        
        # Monitorear procesos
        backend_thread = threading.Thread(
            target=monitor_process, 
            args=(backend_process, "Backend"), 
            daemon=True
        )
        backend_thread.start()
        
        if frontend_process:
            frontend_thread = threading.Thread(
                target=monitor_process, 
                args=(frontend_process, "Frontend"), 
                daemon=True
            )
            frontend_thread.start()
        
        # Mantener el script corriendo
        try:
            while True:
                time.sleep(1)
                
                # Verificar si los procesos siguen vivos
                if backend_process and backend_process.poll() is not None:
                    print("❌ Backend se detuvo inesperadamente")
                    break
                    
                if frontend_process and frontend_process.poll() is not None:
                    print("❌ Frontend se detuvo inesperadamente")
                    # No romper por frontend, puede no estar configurado
        
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