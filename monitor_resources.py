#!/usr/bin/env python3
"""
Script de monitoreo de recursos para PHI GIS Platform
Monitorea memoria, CPU y estado de contenedores Docker
"""

import subprocess
import time
import json
import psutil
import sys
from datetime import datetime

def get_system_info():
    """Obtiene información del sistema"""
    memory = psutil.virtual_memory()
    disk = psutil.disk_usage('/')
    cpu_percent = psutil.cpu_percent(interval=1)
    
    return {
        'timestamp': datetime.now().isoformat(),
        'memory': {
            'total': round(memory.total / (1024**3), 2),  # GB
            'available': round(memory.available / (1024**3), 2),  # GB
            'used': round(memory.used / (1024**3), 2),  # GB
            'percent': memory.percent
        },
        'disk': {
            'total': round(disk.total / (1024**3), 2),  # GB
            'free': round(disk.free / (1024**3), 2),  # GB
            'used': round(disk.used / (1024**3), 2),  # GB
            'percent': round((disk.used / disk.total) * 100, 2)
        },
        'cpu': {
            'percent': cpu_percent,
            'cores': psutil.cpu_count()
        }
    }

def get_docker_stats():
    """Obtiene estadísticas de contenedores Docker"""
    try:
        result = subprocess.run(
            ['docker', 'stats', '--no-stream', '--format', 'json'],
            capture_output=True,
            text=True,
            check=True
        )
        
        containers = []
        for line in result.stdout.strip().split('\n'):
            if line:
                try:
                    container_stats = json.loads(line)
                    containers.append({
                        'name': container_stats.get('Name', 'unknown'),
                        'cpu_percent': container_stats.get('CPUPerc', '0%').replace('%', ''),
                        'memory_usage': container_stats.get('MemUsage', '0B / 0B'),
                        'memory_percent': container_stats.get('MemPerc', '0%').replace('%', ''),
                        'net_io': container_stats.get('NetIO', '0B / 0B'),
                        'block_io': container_stats.get('BlockIO', '0B / 0B')
                    })
                except json.JSONDecodeError:
                    continue
        
        return containers
    except subprocess.CalledProcessError:
        return []

def get_docker_compose_status():
    """Obtiene el estado de los servicios de Docker Compose"""
    try:
        result = subprocess.run(
            ['docker-compose', '-f', 'docker-compose.production.yml', 'ps', '--format', 'json'],
            capture_output=True,
            text=True,
            check=True
        )
        
        services = []
        for line in result.stdout.strip().split('\n'):
            if line:
                try:
                    service = json.loads(line)
                    services.append({
                        'name': service.get('Service', 'unknown'),
                        'status': service.get('Status', 'unknown'),
                        'ports': service.get('Publishers', [])
                    })
                except json.JSONDecodeError:
                    continue
        
        return services
    except subprocess.CalledProcessError:
        return []

def check_service_health():
    """Verifica la salud de los servicios"""
    services = {
        'main_app': 'http://localhost:8050/health',
        'geoportal_backend': 'http://localhost:8000',
        'geoportal_frontend': 'http://localhost:3000',
        'nginx': 'http://localhost:80',
        'prometheus': 'http://localhost:9090'
    }
    
    health_status = {}
    
    for name, url in services.items():
        try:
            result = subprocess.run(
                ['curl', '-f', '-s', '--connect-timeout', '5', url],
                capture_output=True,
                text=True,
                timeout=10
            )
            health_status[name] = 'healthy' if result.returncode == 0 else 'unhealthy'
        except subprocess.TimeoutExpired:
            health_status[name] = 'timeout'
        except Exception:
            health_status[name] = 'error'
    
    return health_status

def print_status_report():
    """Imprime un reporte completo del estado del sistema"""
    print("=" * 80)
    print(f"PHI GIS PLATFORM - REPORTE DE RECURSOS")
    print(f"Fecha y Hora: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 80)
    
    # Información del sistema
    system_info = get_system_info()
    print(f"\n🖥️  SISTEMA:")
    print(f"   CPU: {system_info['cpu']['percent']}% ({system_info['cpu']['cores']} cores)")
    print(f"   Memoria: {system_info['memory']['used']}GB / {system_info['memory']['total']}GB ({system_info['memory']['percent']}%)")
    print(f"   Disco: {system_info['disk']['used']}GB / {system_info['disk']['total']}GB ({system_info['disk']['percent']}%)")
    
    # Estado de salud de servicios
    health = check_service_health()
    print(f"\n🏥 SALUD DE SERVICIOS:")
    for service, status in health.items():
        emoji = "✅" if status == "healthy" else "❌"
        print(f"   {emoji} {service}: {status}")
    
    # Estado de Docker Compose
    compose_services = get_docker_compose_status()
    print(f"\n🐳 SERVICIOS DOCKER COMPOSE:")
    for service in compose_services:
        status_emoji = "🟢" if "Up" in service['status'] else "🔴"
        print(f"   {status_emoji} {service['name']}: {service['status']}")
    
    # Estadísticas de contenedores
    docker_stats = get_docker_stats()
    if docker_stats:
        print(f"\n📊 ESTADÍSTICAS DE CONTENEDORES:")
        print(f"   {'Contenedor':<20} {'CPU%':<8} {'Memoria':<15} {'Mem%':<8}")
        print(f"   {'-'*20} {'-'*8} {'-'*15} {'-'*8}")
        for container in docker_stats:
            print(f"   {container['name']:<20} {container['cpu_percent']:<8} {container['memory_usage']:<15} {container['memory_percent']:<8}")
    
    # Alertas de memoria
    if system_info['memory']['percent'] > 85:
        print(f"\n🚨 ALERTA: Uso de memoria alto ({system_info['memory']['percent']}%)")
    if system_info['disk']['percent'] > 85:
        print(f"\n🚨 ALERTA: Uso de disco alto ({system_info['disk']['percent']}%)")
    
    print("\n" + "=" * 80)

def monitor_continuous():
    """Monitoreo continuo cada 30 segundos"""
    print("Iniciando monitoreo continuo (Ctrl+C para detener)...")
    
    try:
        while True:
            print_status_report()
            time.sleep(30)
    except KeyboardInterrupt:
        print("\n\nMonitoreo detenido por el usuario.")
        sys.exit(0)

def save_report_to_file():
    """Guarda el reporte en un archivo"""
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    filename = f"resources_report_{timestamp}.txt"
    
    # Redirigir stdout a archivo temporalmente
    import io
    import contextlib
    
    f = io.StringIO()
    with contextlib.redirect_stdout(f):
        print_status_report()
    
    report_content = f.getvalue()
    
    with open(filename, 'w', encoding='utf-8') as file:
        file.write(report_content)
    
    print(f"Reporte guardado en: {filename}")
    return filename

if __name__ == "__main__":
    if len(sys.argv) > 1:
        if sys.argv[1] == "--continuous":
            monitor_continuous()
        elif sys.argv[1] == "--save":
            save_report_to_file()
            print_status_report()
        else:
            print("Uso:")
            print("  python monitor_resources.py           # Reporte único")
            print("  python monitor_resources.py --continuous  # Monitoreo continuo")
            print("  python monitor_resources.py --save    # Guardar reporte en archivo")
    else:
        print_status_report() 