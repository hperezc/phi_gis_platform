import os
import sys

# Configurar variables de entorno
os.environ['ENVIRONMENT'] = 'production'
os.environ['DATABASE_URL'] = "postgresql://doadmin:AVNS_nAsg-fcAlH1dOF3pzB_@db-postgresql-nyc1-96388-do-user-22908693-0.l.db.ondigitalocean.com:25060/defaultdb?sslmode=require"
os.environ['MAPBOX_TOKEN'] = "pk.eyJ1IjoiaHBlcmV6Yzk3IiwiYSI6ImNtNXljaDc0cjBpNDMya3E1aGdzcjdpZnkifQ.9FBt1VDj52w2yw-7ewLU6Q"
os.environ['SECRET_KEY'] = "phi-gis-production-2024"
os.environ['PYTHONPATH'] = "/opt/phi_gis_platform"

from main import create_main_app

if __name__ == "__main__":
    app = create_main_app()
    print("=== PHI GIS PLATFORM ===")
    print("URL: http://45.55.212.201:8050")
    print("Streamlit Apps:")
    print("- Asistentes: http://45.55.212.201:8501")
    print("- Temporal: http://45.55.212.201:8502") 
    print("- Geográfico: http://45.55.212.201:8503")
    print("=======================")
    
    # Correr en todas las interfaces (0.0.0.0)
    app.run(host='0.0.0.0', port=8050, debug=False)
