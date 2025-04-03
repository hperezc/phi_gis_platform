import os
import webbrowser

def create_map_html(map_obj, output_file):
    """Crea el HTML final usando la plantilla y el mapa"""
    try:
        # Crear directorio templates si no existe
        template_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'templates')
        os.makedirs(template_dir, exist_ok=True)
        
        # Crear archivo de plantilla si no existe
        template_path = os.path.join(template_dir, 'mapa_template.html')
        if not os.path.exists(template_path):
            with open(template_path, 'w', encoding='utf-8') as f:
                f.write("""<!DOCTYPE html>
<html lang="es">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Visor Geográfico PHI</title>
    
    <!-- Estilos base -->
    <link rel="stylesheet" href="https://cdn.jsdelivr.net/npm/leaflet@1.9.3/dist/leaflet.css"/>
    <link rel="stylesheet" href="https://cdn.jsdelivr.net/npm/bootstrap@5.2.2/dist/css/bootstrap.min.css"/>
    <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.2.0/css/all.min.css"/>
    
    <style>
        body { margin: 0; padding: 0; }
        #header {
            position: fixed;
            top: 0;
            left: 0;
            right: 0;
            height: 60px;
            background-color: #fff;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
            z-index: 1000;
            display: flex;
            align-items: center;
            padding: 0 20px;
        }
        #header h1 {
            font-size: 1.5rem;
            margin: 0;
            color: #333;
        }
        #map {
            position: absolute;
            top: 60px;
            bottom: 0;
            left: 0;
            right: 0;
            z-index: 1;
        }
        .info-box {
            position: absolute;
            bottom: 20px;
            left: 20px;
            background: white;
            padding: 15px;
            border-radius: 4px;
            box-shadow: 0 1px 4px rgba(0,0,0,0.2);
            z-index: 1000;
            max-width: 300px;
        }
    </style>
</head>
<body>
    <div id="header">
        <h1>
            <i class="fas fa-map-marked-alt"></i>
            Visor Geográfico PHI - Actividades Territoriales
        </h1>
    </div>
    
    {{ map_div }}
    
    <div class="info-box">
        <h4>Información</h4>
        <p>Este visor muestra la distribución geográfica de las actividades PHI en diferentes niveles territoriales:</p>
        <ul>
            <li>Departamentos</li>
            <li>Municipios</li>
            <li>Veredas</li>
            <li>Cabeceras</li>
        </ul>
        <small>Use el control de capas en la esquina superior derecha para mostrar/ocultar niveles.</small>
    </div>

    <!-- Scripts base -->
    <script src="https://cdn.jsdelivr.net/npm/leaflet@1.9.3/dist/leaflet.js"></script>
    <script src="https://code.jquery.com/jquery-3.7.1.min.js"></script>
    <script src="https://cdn.jsdelivr.net/npm/bootstrap@5.2.2/dist/js/bootstrap.bundle.min.js"></script>
    
    <!-- Código del mapa -->
    {{ map_script }}
</body>
</html>""")
        
        # Leer la plantilla
        with open(template_path, 'r', encoding='utf-8') as f:
            template = f.read()
        
        # Obtener el código del mapa
        map_html = map_obj._repr_html_()
        
        # Separar el div del mapa y el script
        map_div = map_html[map_html.find('<div'):map_html.find('</div>') + 6]
        map_script = map_html[map_html.find('<script'):map_html.find('</script>') + 9]
        
        # Reemplazar en la plantilla
        final_html = template.replace('{{ map_div }}', map_div).replace('{{ map_script }}', map_script)
        
        # Guardar el archivo final
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write(final_html)
            
        print(f"Mapa creado exitosamente en: {output_file}")
        return True
        
    except Exception as e:
        print(f"Error al crear el mapa HTML: {str(e)}")
        return False 