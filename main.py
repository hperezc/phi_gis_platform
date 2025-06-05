import os
import sys
from dotenv import load_dotenv
import subprocess
import threading
import time
import logging

# Configurar logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('/app/logs/app.log') if os.path.exists('/app/logs') else logging.StreamHandler(),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# Cargar variables de entorno
load_dotenv()

# Agregar el directorio raíz al path de Python
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from flask import Flask, render_template, send_from_directory, redirect, jsonify
from werkzeug.middleware.dispatcher import DispatcherMiddleware
from werkzeug.serving import run_simple
from fastapi import FastAPI
from fastapi.middleware.wsgi import WSGIMiddleware

# Importar aplicaciones
try:
    from Dashboard_BD_PHI.dashboard.app import create_dash_app
    logger.info("Dashboard importado exitosamente")
except ImportError as e:
    logger.error(f"Error importando dashboard: {e}")
    create_dash_app = None

# Variable global para controlar los procesos Streamlit
streamlit_processes = {}

def start_streamlit_app(app_name, file_path, port):
    """Inicia una aplicación Streamlit como proceso independiente"""
    try:
        command = f"streamlit run {file_path} --server.port={port} --server.headless=true --server.address=0.0.0.0"
        process = subprocess.Popen(command, shell=True)
        streamlit_processes[app_name] = {'process': process, 'port': port}
        logger.info(f"Iniciado {app_name} en el puerto {port}")
        return process
    except Exception as e:
        logger.error(f"Error iniciando {app_name}: {e}")
        return None

def stop_streamlit_apps():
    """Detiene todas las aplicaciones Streamlit en ejecución"""
    for app_name, data in streamlit_processes.items():
        logger.info(f"Deteniendo {app_name}...")
        if 'process' in data and data['process'].poll() is None:
            try:
                data['process'].terminate()
                data['process'].wait(timeout=10)
            except subprocess.TimeoutExpired:
                data['process'].kill()
            except Exception as e:
                logger.error(f"Error deteniendo {app_name}: {e}")
    logger.info("Todas las aplicaciones Streamlit han sido detenidas")

def init_streamlit_apps():
    """Inicializa todas las aplicaciones Streamlit necesarias"""
    # Solo inicializar en modo desarrollo, cuando se ejecuta directamente, o cuando se fuerza
    if os.getenv('ENVIRONMENT') == 'production' and __name__ != '__main__' and not os.getenv('FORCE_STREAMLIT_INIT'):
        logger.info("Modo producción detectado, omitiendo inicialización de Streamlit apps")
        return
        
    # Rutas a los archivos de las aplicaciones
    ml_module_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'ml_module')
    
    apps = {
        'asistentes': {
            'file': os.path.join(ml_module_dir, 'ml_module', 'app.py'),
            'port': 8501
        },
        'temporal': {
            'file': os.path.join(ml_module_dir, 'ml_module', 'temporal_analysis', 'app_temporal.py'),
            'port': 8502
        },
        'geografico': {
            'file': os.path.join(ml_module_dir, 'ml_module', 'geographic_analysis', 'app_geographic.py'),
            'port': 8503
        }
    }
    
    # Iniciar cada aplicación en un hilo separado
    for app_name, config in apps.items():
        # Comprobar si el archivo existe
        if os.path.exists(config['file']):
            logger.info(f"Iniciando aplicación {app_name}...")
            start_streamlit_app(app_name, config['file'], config['port'])
        else:
            logger.warning(f"No se encontró el archivo {config['file']} para la aplicación {app_name}")
    
    # Dar tiempo para que las aplicaciones se inicien
    if streamlit_processes:
        time.sleep(5)

def create_main_app():
    """Crea la aplicación principal Flask"""
    app = Flask(__name__)
    
    # Configurar secret key
    app.secret_key = os.getenv('SECRET_KEY', 'dev-secret-key-change-in-production')
    
    # Configurar rutas para archivos estáticos del dashboard
    @app.route('/dashboard/assets/<path:filename>')
    def serve_dashboard_static(filename):
        dashboard_assets = os.path.join(os.path.dirname(os.path.abspath(__file__)), 
                                      'Dashboard_BD_PHI', 'dashboard', 'assets')
        return send_from_directory(dashboard_assets, filename)
    
    @app.route('/')
    def index():
        try:
            return render_template('index.html')
        except Exception as e:
            logger.error(f"Error en ruta principal: {e}")
            return f"Error: {str(e)}", 500
    
    # Health check endpoint para monitoreo
    @app.route('/health')
    def health_check():
        try:
            # Verificar estado de servicios críticos
            health_status = {
                'status': 'healthy',
                'timestamp': time.time(),
                'services': {
                    'main_app': 'ok',
                    'streamlit_apps': len(streamlit_processes),
                    'environment': os.getenv('ENVIRONMENT', 'development')
                }
            }
            
            # Verificar base de datos si es posible
            try:
                from config.database import DATABASE_URL
                if DATABASE_URL:
                    health_status['services']['database'] = 'configured'
            except:
                health_status['services']['database'] = 'not_configured'
            
            return jsonify(health_status), 200
        except Exception as e:
            logger.error(f"Health check failed: {e}")
            return jsonify({'status': 'unhealthy', 'error': str(e)}), 500
    
    # Rutas para las aplicaciones
    @app.route('/dashboard')
    def dashboard():
        return redirect('/dashboard/')
    
    @app.route('/geoportal')
    def geoportal():
        # Redireccionar al frontend del geoportal
        geoportal_url = os.getenv('GEOPORTAL_URL', 'http://localhost:3000')
        return redirect(geoportal_url)
    
    @app.route('/predictivos')
    def predictivos():
        try:
            return render_template('predictivos.html')
        except Exception as e:
            logger.error(f"Error en ruta predictivos: {e}")
            return f"Error: {str(e)}", 500
    
    @app.route('/predictivos/asistentes')
    def predictivos_asistentes():
        # Para desarrollo local con BD DigitalOcean, usar localhost
        # Solo usar el dominio en despliegue real en VPS
        if os.getenv('DEPLOY_MODE') == 'vps':
            domain = os.getenv('DOMAIN', 'localhost')
            return redirect(f'https://{domain}/predictivos/asistentes/')
        return redirect('http://localhost:8501')
    
    @app.route('/predictivos/temporal')
    def predictivos_temporal():
        # Para desarrollo local con BD DigitalOcean, usar localhost
        # Solo usar el dominio en despliegue real en VPS
        if os.getenv('DEPLOY_MODE') == 'vps':
            domain = os.getenv('DOMAIN', 'localhost')
            return redirect(f'https://{domain}/predictivos/temporal/')
        return redirect('http://localhost:8502')
    
    @app.route('/predictivos/geografico')
    def predictivos_geografico():
        # Para desarrollo local con BD DigitalOcean, usar localhost
        # Solo usar el dominio en despliegue real en VPS
        if os.getenv('DEPLOY_MODE') == 'vps':
            domain = os.getenv('DOMAIN', 'localhost')
            return redirect(f'https://{domain}/predictivos/geografico/')
        return redirect('http://localhost:8503')
    
    # Error handlers
    @app.errorhandler(404)
    def not_found(error):
        return render_template('404.html'), 404
    
    @app.errorhandler(500)
    def internal_error(error):
        logger.error(f"Error interno del servidor: {error}")
        return render_template('500.html'), 500
    
    return app

# Iniciar las aplicaciones Streamlit si este script es el principal
if __name__ == '__main__':
    # Inicializar las aplicaciones Streamlit
    init_streamlit_apps()
    
    try:
        # Crear aplicaciones
        main_app = create_main_app()
        
        if create_dash_app:
            dash_app = create_dash_app()
            # Configurar el dispatcher
            application = DispatcherMiddleware(main_app, {
                '/dashboard': dash_app.server
            })
        else:
            logger.warning("Dashboard no disponible, usando solo aplicación principal")
            application = main_app

        # Arrancar el servidor
        logger.info("Iniciando servidor en modo desarrollo...")
        run_simple('localhost', 8050, application, 
                use_reloader=False,  # Cambiado a False para evitar problemas con los subprocesos
                use_debugger=True,
                static_files={
                    '/dashboard/assets': os.path.join(os.path.dirname(os.path.abspath(__file__)), 
                                                    'Dashboard_BD_PHI', 'dashboard', 'assets')
                })
    except KeyboardInterrupt:
        logger.info("Interrupción por teclado recibida")
    except Exception as e:
        logger.error(f"Error crítico en la aplicación: {e}")
    finally:
        # Asegurarse de que todas las aplicaciones Streamlit se detengan al salir
        stop_streamlit_apps()
else:
    # Solo crear la aplicación Flask para el modo WSGI (producción)
    logger.info("Iniciando en modo producción (WSGI)")
    main_app = create_main_app()
    
    if create_dash_app:
        dash_app = create_dash_app()
        # Configurar el dispatcher
        application = DispatcherMiddleware(main_app, {
            '/dashboard': dash_app.server
        })
    else:
        logger.warning("Dashboard no disponible, usando solo aplicación principal")
        application = main_app
