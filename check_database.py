#!/usr/bin/env python3
"""
Script para verificar qué base de datos está configurada
"""

import os
from dotenv import load_dotenv

load_dotenv()

print("🔍 Verificando configuración de base de datos...")
print("-" * 50)

# Verificar entorno
environment = os.getenv('ENVIRONMENT', 'development')
print(f"🌍 Entorno actual: {environment}")

# Importar configuración
from config.database import DATABASE_URL, ENVIRONMENT

print(f"📊 Entorno desde config: {ENVIRONMENT}")
print(f"🔗 DATABASE_URL: {DATABASE_URL[:50]}...")

if 'digitalocean' in DATABASE_URL:
    print("✅ ¡Configurado para usar DigitalOcean!")
    print("🌍 La aplicación se conectará a la BD en la nube")
else:
    print("🏠 Configurado para usar base de datos local")
    print("💡 Para usar DigitalOcean, establece: ENVIRONMENT=production")

print("-" * 50) 