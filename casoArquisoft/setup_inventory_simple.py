#!/usr/bin/env python3
"""
Script simple para configurar el microservicio de inventario
Sin dependencias de Django setup
"""

import os
import shutil

def setup_inventory_microservice():
    """Configuración básica del microservicio sin Django setup"""
    
    print("🚀 Configurando microservicio de inventario...")
    
    project_dir = os.path.dirname(os.path.abspath(__file__))
    
    # 1. Crear scripts de base de datos
    create_database_scripts(project_dir)
    
    # 2. Crear archivos de prueba
    create_simple_test_files(project_dir)
    
    # 3. Crear script de inicio
    create_startup_script(project_dir)
    
    print("✅ Configuración básica completada!")
    print("\n📋 Próximos pasos:")
    print("1. Ejecutar: install_inventory_db.bat (en Windows)")
    print("2. Activar entorno virtual: .\\env\\Scripts\\activate")
    print("3. Instalar dependencias: pip install django-cors-headers redis mysql-connector-python")
    print("4. Ejecutar: python manage.py runserver")
    print("5. Probar: http://localhost:8000/api/inventory/health/")

def create_database_scripts(project_dir):
    """Crear scripts simplificados de base de datos"""
    
    # Script SQL simplificado
    sql_simple = '''-- Script SQL simplificado para microservicio de inventario
-- Ejecutar con: mysql -u root -p

CREATE DATABASE IF NOT EXISTS inventario_db;
USE inventario_db;

CREATE USER IF NOT EXISTS 'inventory_user'@'localhost' IDENTIFIED BY 'inventory123';
GRANT ALL PRIVILEGES ON inventario_db.* TO 'inventory_user'@'localhost';
FLUSH PRIVILEGES;

-- Tabla de productos en inventario
CREATE TABLE IF NOT EXISTS productos_inventario (
    id BIGINT AUTO_INCREMENT PRIMARY KEY,
    producto_id VARCHAR(50) NOT NULL,
    ubicacion VARCHAR(20) NOT NULL,
    cantidad INT NOT NULL DEFAULT 0,
    cantidad_reservada INT NOT NULL DEFAULT 0,
    fecha_actualizacion TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    
    UNIQUE KEY uk_producto_ubicacion (producto_id, ubicacion),
    INDEX idx_producto (producto_id),
    INDEX idx_ubicacion (ubicacion)
);

-- Tabla de transacciones
CREATE TABLE IF NOT EXISTS transacciones_inventario (
    id VARCHAR(50) PRIMARY KEY,
    producto_id VARCHAR(50) NOT NULL,
    tipo_operacion ENUM('RECEPCION', 'PICKING', 'DEVOLUCION') NOT NULL,
    cantidad INT NOT NULL,
    ubicacion VARCHAR(20) NOT NULL,
    operario_id VARCHAR(50) NOT NULL,
    estado ENUM('PROCESANDO', 'COMPLETADA', 'CANCELADA') NOT NULL DEFAULT 'PROCESANDO',
    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    tiempo_procesamiento_ms INT,
    
    INDEX idx_producto_fecha (producto_id, timestamp),
    INDEX idx_estado (estado)
);

-- Datos iniciales
INSERT INTO productos_inventario (producto_id, ubicacion, cantidad) VALUES
('zapatos', 'A1-B1', 100),
('zapatos', 'A2-B1', 75),
('caja', 'A2-B1', 200),
('libro', 'A3-B1', 300),
('mesa', 'A4-B1', 50),
('silla', 'A5-B1', 80)
ON DUPLICATE KEY UPDATE cantidad = VALUES(cantidad);

SELECT 'Base de datos configurada exitosamente' as resultado;
'''
    
    with open(os.path.join(project_dir, 'setup_inventory_simple.sql'), 'w', encoding='utf-8') as f:
        f.write(sql_simple)
    
    # Script batch para Windows
    batch_script = '''@echo off
echo Configurando base de datos del microservicio de inventario...

mysql --version >nul 2>&1
if errorlevel 1 (
    echo Error: MySQL no está instalado o no está en el PATH
    echo Por favor instala MySQL y asegurate de que esté en el PATH
    pause
    exit /b 1
)

echo Ejecutando script SQL...
mysql -u root -p < setup_inventory_simple.sql

if %errorlevel% equ 0 (
    echo.
    echo ======================================
    echo Base de datos configurada exitosamente
    echo ======================================
    echo.
    echo Para verificar, ejecuta:
    echo mysql -u inventory_user -p
    echo Contraseña: inventory123
    echo.
    echo Luego ejecuta:
    echo USE inventario_db;
    echo SHOW TABLES;
    echo.
) else (
    echo Error al configurar la base de datos
)

pause
'''
    
    with open(os.path.join(project_dir, 'install_inventory_db.bat'), 'w', encoding='utf-8') as f:
        f.write(batch_script)
    
    print("✅ Scripts de base de datos creados")

def create_simple_test_files(project_dir):
    """Crear archivos de prueba simplificados"""
    
    # Test simple con requests
    test_script = '''#!/usr/bin/env python3
"""
Script de prueba simple para el microservicio de inventario
"""

import requests
import json
import time

def test_inventory_api():
    base_url = 'http://localhost:8000'
    
    print("🧪 Iniciando pruebas del microservicio de inventario...")
    
    # Test 1: Health check
    try:
        response = requests.get(f'{base_url}/health/inventory/')
        if response.status_code == 200:
            print("✅ Health check: OK")
        else:
            print(f"❌ Health check: Error {response.status_code}")
    except Exception as e:
        print(f"❌ Health check: {e}")
    
    # Test 2: Consultar stock
    try:
        response = requests.get(f'{base_url}/api/inventory/status/zapatos/A1-B1/')
        if response.status_code == 200:
            data = response.json()
            print(f"✅ Consulta stock: {data}")
        else:
            print(f"❌ Consulta stock: Error {response.status_code}")
    except Exception as e:
        print(f"❌ Consulta stock: {e}")
    
    # Test 3: Crear transacción
    try:
        data = {
            'producto_id': 'zapatos',
            'tipo_operacion': 'RECEPCION',
            'cantidad': 10,
            'ubicacion': 'A1-B1',
            'operario_id': 'TEST_USER'
        }
        
        start_time = time.time()
        response = requests.post(
            f'{base_url}/api/inventory/transactions/',
            json=data
        )
        end_time = time.time()
        
        response_time_ms = (end_time - start_time) * 1000
        
        if response.status_code == 201:
            result = response.json()
            print(f"✅ Crear transacción: {result}")
            print(f"⏱️  Tiempo de respuesta: {response_time_ms:.2f}ms")
            
            if response_time_ms < 500:
                print("✅ ASR cumplido: < 500ms")
            else:
                print("❌ ASR no cumplido: > 500ms")
        else:
            print(f"❌ Crear transacción: Error {response.status_code}")
    except Exception as e:
        print(f"❌ Crear transacción: {e}")
    
    print("\\n🏁 Pruebas completadas")

if __name__ == '__main__':
    test_inventory_api()
'''
    
    with open(os.path.join(project_dir, 'test_inventory_simple.py'), 'w', encoding='utf-8') as f:
        f.write(test_script)
    
    print("✅ Archivos de prueba creados")

def create_startup_script(project_dir):
    """Crear script de inicio del proyecto"""
    
    startup_script = '''@echo off
echo ========================================
echo  MICROSERVICIO DE INVENTARIO - STARTUP
echo ========================================

echo.
echo 1. Activando entorno virtual...
if exist env\\Scripts\\activate.bat (
    call env\\Scripts\\activate.bat
    echo ✅ Entorno virtual activado
) else (
    echo ⚠️  Entorno virtual no encontrado. Creando...
    python -m venv env
    call env\\Scripts\\activate.bat
    echo ✅ Entorno virtual creado y activado
)

echo.
echo 2. Instalando dependencias...
pip install --quiet django==3.2.6 django-cors-headers redis mysql-connector-python

echo.
echo 3. Iniciando servidor Django...
echo 📊 ASR objetivo: 1500 usuarios concurrentes, <500ms respuesta
echo 🌐 URL: http://localhost:8000
echo 🔍 Health check: http://localhost:8000/health/inventory/
echo 📋 API docs: http://localhost:8000/api/inventory/
echo.
echo Presiona Ctrl+C para detener el servidor
echo.

python manage.py runserver
'''
    
    with open(os.path.join(project_dir, 'start_microservice.bat'), 'w', encoding='utf-8') as f:
        f.write(startup_script)
    
    print("✅ Script de inicio creado")

if __name__ == '__main__':
    setup_inventory_microservice()