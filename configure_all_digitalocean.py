#!/usr/bin/env python3
"""
Script para configurar TODOS los aplicativos para usar DigitalOcean
Incluye: Main App, Dashboard, ML Apps (3), Geoportal
"""

import os
import sys
from pathlib import Path

# Configuración centralizada de DigitalOcean
DIGITALOCEAN_CONFIG = {
    'ENVIRONMENT': 'production',
    'DATABASE_URL': 'postgresql://doadmin:AVNS_nAsg-fcAlH1dOF3pzB_@db-postgresql-nyc1-96388-do-user-22908693-0.l.db.ondigitalocean.com:25060/defaultdb?sslmode=require',
    
    # Para geoportal (variables individuales)
    'DB_USER': 'doadmin',
    'DB_PASSWORD': 'AVNS_nAsg-fcAlH1dOF3pzB_',
    'DB_HOST': 'db-postgresql-nyc1-96388-do-user-22908693-0.l.db.ondigitalocean.com',
    'DB_PORT': '25060',
    'DB_NAME': 'defaultdb',
    
    # Configuración adicional
    'SECRET_KEY': 'phi-gis-digitalocean-production-2025',
    'MAPBOX_TOKEN': 'pk.eyJ1IjoiaHBlcmV6Yzk3IiwiYSI6ImNtNXljaDc0cjBpNDMya3E1aGdzcjdqZnkifQ.9FBt1VDj52w2yw-7ewLU6Q',
    'GEOPORTAL_URL': 'http://localhost:3000'
}

def set_environment_variables():
    """Establece todas las variables de entorno para DigitalOcean"""
    print("🔧 Configurando variables de entorno para DigitalOcean...")
    
    for key, value in DIGITALOCEAN_CONFIG.items():
        os.environ[key] = value
        print(f"✅ {key} = {value[:50]}{'...' if len(value) > 50 else ''}")

def test_main_app():
    """Prueba la aplicación principal"""
    try:
        print("\n🔍 Probando aplicación principal...")
        
        from config.database import DATABASE_URL, ENVIRONMENT
        print(f"📊 Entorno: {ENVIRONMENT}")
        print(f"🔗 Base de datos: {'DigitalOcean' if 'digitalocean' in DATABASE_URL else 'Local'}")
        
        from main import create_main_app
        app = create_main_app()
        
        with app.test_client() as client:
            response = client.get('/health')
            if response.status_code == 200:
                print("✅ Main App: OK")
                return True
            else:
                print(f"❌ Main App: Error {response.status_code}")
                return False
                
    except Exception as e:
        print(f"❌ Main App: Error - {e}")
        return False

def test_dashboard():
    """Prueba el dashboard Dash"""
    try:
        print("\n🔍 Probando Dashboard...")
        
        from Dashboard_BD_PHI.dashboard.app import create_dash_app
        dash_app = create_dash_app()
        
        if dash_app:
            print("✅ Dashboard: OK")
            return True
        else:
            print("❌ Dashboard: No se pudo crear")
            return False
            
    except Exception as e:
        print(f"❌ Dashboard: Error - {e}")
        return False

def test_ml_apps():
    """Prueba los aplicativos ML"""
    try:
        print("\n🔍 Probando aplicativos ML...")
        
        # Ajustar paths
        ml_path = Path(os.getcwd()) / 'ml_module'
        sys.path.append(str(ml_path))
        
        from utils.data_loader import DataLoader
        
        # Probar conexión
        data_loader = DataLoader()
        
        # Test básico de consulta
        zonas = data_loader.get_zonas_geograficas()
        if zonas:
            print(f"✅ ML Apps: OK - {len(zonas)} zonas geográficas")
            return True
        else:
            print("❌ ML Apps: No se pudieron cargar datos")
            return False
            
    except Exception as e:
        print(f"❌ ML Apps: Error - {e}")
        return False

def test_geoportal():
    """Prueba el geoportal backend"""
    try:
        print("\n🔍 Probando Geoportal...")
        
        # Cambiar al directorio del geoportal
        geoportal_path = Path(os.getcwd()) / 'geoportal' / 'backend'
        sys.path.append(str(geoportal_path))
        
        from app.database import engine
        from sqlalchemy import text
        
        # Test de conexión con text() para SQLAlchemy
        with engine.connect() as conn:
            result = conn.execute(text("SELECT 1 as test"))
            if result.fetchone():
                print("✅ Geoportal: OK")
                return True
            
    except Exception as e:
        print(f"❌ Geoportal: Error - {e}")
        return False

def create_unified_env_file():
    """Crea un archivo .env unificado"""
    try:
        print("\n📝 Creando archivo .env unificado...")
        
        env_content = """# Configuración unificada para DigitalOcean
# Generado automáticamente - NO EDITAR MANUALMENTE

# Entorno
ENVIRONMENT=production

# Base de datos principal (para Main App, Dashboard, ML Apps)
DATABASE_URL=postgresql://doadmin:AVNS_nAsg-fcAlH1dOF3pzB_@db-postgresql-nyc1-96388-do-user-22908693-0.l.db.ondigitalocean.com:25060/defaultdb?sslmode=require

# Variables individuales para Geoportal
DB_USER=doadmin
DB_PASSWORD=AVNS_nAsg-fcAlH1dOF3pzB_
DB_HOST=db-postgresql-nyc1-96388-do-user-22908693-0.l.db.ondigitalocean.com
DB_PORT=25060
DB_NAME=defaultdb

# Configuración de aplicación
SECRET_KEY=phi-gis-digitalocean-production-2025
MAPBOX_TOKEN=pk.eyJ1IjoiaHBlcmV6Yzk3IiwiYSI6ImNtNXljaDc0cjBpNDMya3E1aGdzcjdqZnkifQ.9FBt1VDj52w2yw-7ewLU6Q

# URLs de servicios
GEOPORTAL_URL=http://localhost:3000
DOMAIN=142.93.118.216

# Configuración de puertos (para desarrollo local)
STREAMLIT_PORT_ASISTENTES=8501
STREAMLIT_PORT_TEMPORAL=8502
STREAMLIT_PORT_GEOGRAFICO=8503
"""
        
        with open('.env', 'w', encoding='utf-8') as f:
            f.write(env_content)
        
        print("✅ Archivo .env creado correctamente")
        return True
        
    except Exception as e:
        print(f"❌ Error creando .env: {e}")
        return False

def main():
    """Función principal"""
    print("🚀 CONFIGURANDO TODOS LOS APLICATIVOS PARA DIGITALOCEAN")
    print("=" * 60)
    
    # Paso 1: Configurar variables de entorno
    set_environment_variables()
    
    # Paso 2: Crear archivo .env unificado
    if not create_unified_env_file():
        print("❌ Fallo creando archivo .env")
        return False
    
    # Paso 3: Probar cada aplicativo
    results = {}
    
    results['main_app'] = test_main_app()
    results['dashboard'] = test_dashboard()
    results['ml_apps'] = test_ml_apps()
    results['geoportal'] = test_geoportal()
    
    # Resumen
    print("\n" + "=" * 60)
    print("📋 RESUMEN DE CONFIGURACIÓN:")
    print("=" * 60)
    
    for app, status in results.items():
        icon = "✅" if status else "❌"
        print(f"{icon} {app.replace('_', ' ').title()}: {'Configurado' if status else 'Error'}")
    
    total_ok = sum(results.values())
    print(f"\n🎯 {total_ok}/4 aplicativos configurados correctamente")
    
    if total_ok >= 3:  # Al menos 3 de 4 funcionando
        print("\n🎉 ¡CONFIGURACIÓN EXITOSA!")
        print("💡 Aplicativos listos para usar DigitalOcean")
        print("\n🚀 Para ejecutar con DigitalOcean:")
        print("   python run_with_digitalocean.py")
        return True
    else:
        print("\n⚠️ Configuración parcial completada")
        print("💡 Algunos aplicativos necesitan revisión")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1) 