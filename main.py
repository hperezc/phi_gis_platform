import os
import sys

# Agregar el directorio raíz al path de Python
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from flask import Flask, render_template, send_from_directory, redirect
from werkzeug.middleware.dispatcher import DispatcherMiddleware
from werkzeug.serving import run_simple
from fastapi import FastAPI
from fastapi.middleware.wsgi import WSGIMiddleware

# Importar aplicaciones
from Dashboard_BD_PHI.dashboard.app import create_dash_app

def create_main_app():
    """Crea la aplicación principal Flask"""
    app = Flask(__name__)
    
    # Configurar rutas para archivos estáticos del dashboard
    @app.route('/dashboard/assets/<path:filename>')
    def serve_dashboard_static(filename):
        dashboard_assets = os.path.join(os.path.dirname(os.path.abspath(__file__)), 
                                      'Dashboard_BD_PHI', 'dashboard', 'assets')
        return send_from_directory(dashboard_assets, filename)
    
    @app.route('/')
    def index():
        return render_template('index.html')
    
    # Rutas para las aplicaciones
    @app.route('/dashboard')
    def dashboard():
        return redirect('/dashboard/')
    
    @app.route('/geoportal')
    def geoportal():
        # Redireccionar al frontend del geoportal
        geoportal_url = os.getenv('GEOPORTAL_URL', 'http://localhost:3000')
        return redirect(geoportal_url)
    
    return app

# Crear aplicaciones
main_app = create_main_app()
dash_app = create_dash_app()

# Configurar el dispatcher
application = DispatcherMiddleware(main_app, {
    '/dashboard': dash_app.server
})

if __name__ == '__main__':
    run_simple('localhost', 8050, application, 
               use_reloader=True, 
               use_debugger=True,
               static_files={
                   '/dashboard/assets': os.path.join(os.path.dirname(os.path.abspath(__file__)), 
                                                   'Dashboard_BD_PHI', 'dashboard', 'assets')
               })
