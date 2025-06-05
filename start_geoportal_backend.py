#!/usr/bin/env python3
"""
Script específico para iniciar el backend del geoportal
"""
import os
import sys
import subprocess

def start_backend():
    """Iniciar el backend del geoportal"""
    try:
        # Configurar variables de entorno
        os.environ['DB_USER'] = 'doadmin'
        os.environ['DB_PASSWORD'] = 'AVNS_nAsg-fcAlH1dOF3pzB_'
        os.environ['DB_HOST'] = 'db-postgresql-nyc1-96388-do-user-22908693-0.l.db.ondigitalocean.com'
        os.environ['DB_PORT'] = '25060'
        os.environ['DB_NAME'] = 'defaultdb'
        
        # Cambiar al directorio backend
        backend_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'geoportal', 'backend')
        os.chdir(backend_dir)
        
        print(f"Iniciando backend desde: {os.getcwd()}")
        
        # Ejecutar uvicorn directamente
        from uvicorn import run
        run("app.main:app", host="0.0.0.0", port=8000, reload=True)
        
    except Exception as e:
        print(f"Error iniciando backend: {e}")
        # Fallback usando subprocess
        try:
            cmd = [sys.executable, '-m', 'uvicorn', 'app.main:app', '--host', '0.0.0.0', '--port', '8000', '--reload']
            subprocess.run(cmd, cwd=backend_dir)
        except Exception as e2:
            print(f"Error en fallback: {e2}")

if __name__ == "__main__":
    start_backend() 