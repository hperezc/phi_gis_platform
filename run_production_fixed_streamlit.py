import os
import sys
from werkzeug.middleware.dispatcher import DispatcherMiddleware

# Forzar inicialización de Streamlit en producción
os.environ['FORCE_STREAMLIT_INIT'] = 'true'
os.environ['ENVIRONMENT'] = 'production'
os.environ['DATABASE_URL'] = "postgresql://doadmin:AVNS_nAsg-fcAlH1dOF3pzB_@db-postgresql-nyc1-96388-do-user-22908693-0.l.db.ondigitalocean.com:25060/defaultdb?sslmode=require"
os.environ['MAPBOX_TOKEN'] = "pk.eyJ1IjoiaHBlcmV6Yzk3IiwiYSI6ImNtNXljaDc0cjBpNDMya3E1aGdzcjdpZnkifQ.9FBt1VDj52w2yw-7ewLU6Q"
os.environ['SECRET_KEY'] = "phi-gis-production-2024"
os.environ['PYTHONPATH'] = "/opt/phi_gis_platform"

from main import create_main_app, init_streamlit_apps
from Dashboard_BD_PHI.dashboard.app import create_dash_app

if __name__ == "__main__":
    # FORZAR inicialización de Streamlit
    print("🚀 Iniciando aplicaciones Streamlit...")
    init_streamlit_apps()
    
    main_app = create_main_app()
    dash_app = create_dash_app()

    application = DispatcherMiddleware(main_app, {
        '/dashboard': dash_app.server
    })

    print("=== PHI GIS PLATFORM ===")
    print("✅ URL Principal: http://45.55.212.201:8050")
    print("✅ Dashboard: http://45.55.212.201:8050/dashboard")
    print("✅ Streamlit Asistentes: http://45.55.212.201:8501")
    print("✅ Streamlit Temporal: http://45.55.212.201:8502")
    print("✅ Streamlit Geográfico: http://45.55.212.201:8503")
    print("=======================")

    from werkzeug.serving import run_simple
    run_simple('0.0.0.0', 8050, application, use_reloader=False, use_debugger=True)
