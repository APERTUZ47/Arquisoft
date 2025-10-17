# =============================================================================
# Script de Integración del Microservicio de Inventario con Django
# Configura automáticamente el proyecto principal para usar el microservicio
# =============================================================================

import os
import sys
import django
from django.conf import settings
from django.core.management import execute_from_command_line

# Agregar el directorio del proyecto al path
project_path = os.path.dirname(os.path.abspath(__file__))
sys.path.append(project_path)

# Configurar Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'casoArquisoft.settings')
django.setup()

def integrate_inventory_microservice():
    """
    Integra el microservicio de inventario con el proyecto Django principal
    """
    
    print("🚀 Iniciando integración del microservicio de inventario...")
    
    # 1. Modificar settings.py para agregar configuración del microservicio
    update_settings_file()
    
    # 2. Actualizar urls.py principal
    update_main_urls()
    
    # 3. Crear migraciones para las nuevas tablas
    create_inventory_migrations()
    
    # 4. Configurar base de datos
    setup_inventory_database()
    
    # 5. Crear archivos de prueba
    create_test_files()
    
    print("✅ Integración completada exitosamente!")
    print("\n📋 Próximos pasos:")
    print("1. Ejecutar: python manage.py migrate --database=inventory")
    print("2. Ejecutar: python manage.py runserver")
    print("3. Probar endpoints en: http://localhost:8000/api/inventory/")
    print("4. Monitor de salud en: http://localhost:8000/health/inventory/")

def update_settings_file():
    """
    Actualiza el archivo settings.py para incluir configuración del microservicio
    """
    
    settings_file = os.path.join(project_path, 'casoArquisoft', 'settings.py')
    
    # Leer contenido actual
    with open(settings_file, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Configuración adicional para el microservicio
    additional_config = '''

# =============================================================================
# CONFIGURACIÓN DEL MICROSERVICIO DE INVENTARIO
# =============================================================================

# Importar configuración del microservicio
from inventory_config import (
    INVENTORY_DATABASE_CONFIG, 
    ASR_CONFIG, 
    MONITORING_CONFIG,
    configure_django_for_inventory
)

# Base de datos adicional para inventario
DATABASES['inventory'] = INVENTORY_DATABASE_CONFIG

# Router para dirigir queries a la base de datos correcta
DATABASE_ROUTERS = ['inventory_config.InventoryDatabaseRouter']

# Cache adicional para inventario
CACHES['inventory'] = {
    'BACKEND': 'django.core.cache.backends.redis.RedisCache',
    'LOCATION': 'redis://localhost:6379/2',
    'OPTIONS': {
        'CLIENT_CLASS': 'django_redis.client.DefaultClient',
    },
    'KEY_PREFIX': 'inventory_',
    'TIMEOUT': 300,
}

# Configuración de CORS para el microservicio
CORS_ALLOW_ALL_ORIGINS = True  # Solo para desarrollo
CORS_ALLOWED_ORIGINS = [
    "http://localhost:3000",
    "http://127.0.0.1:3000",
    "http://localhost:8000",
    "http://127.0.0.1:8000",
]

# Headers permitidos para CORS
CORS_ALLOW_HEADERS = [
    'accept',
    'accept-encoding',
    'authorization',
    'content-type',
    'dnt',
    'origin',
    'user-agent',
    'x-csrftoken',
    'x-requested-with',
    'x-api-key',  # Para autenticación del microservicio
]

# Configuración de logging para el microservicio
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'verbose': {
            'format': '{levelname} {asctime} {module} {process:d} {thread:d} {message}',
            'style': '{',
        },
    },
    'handlers': {
        'inventory_file': {
            'level': 'INFO',
            'class': 'logging.handlers.RotatingFileHandler',
            'filename': 'logs/inventory_microservice.log',
            'maxBytes': 15728640,
            'backupCount': 5,
            'formatter': 'verbose',
        },
        'console': {
            'level': 'DEBUG',
            'class': 'logging.StreamHandler',
            'formatter': 'verbose',
        },
    },
    'loggers': {
        'inventory_microservice': {
            'handlers': ['inventory_file', 'console'],
            'level': 'INFO',
            'propagate': True,
        },
    },
}

# Configurar directorio de logs
import os
if not os.path.exists('logs'):
    os.makedirs('logs')

# Aplicar configuración automática
configure_django_for_inventory()

# Configuración específica del ASR
ASR_MAX_RESPONSE_TIME_MS = ASR_CONFIG['max_response_time_ms']
ASR_CONCURRENT_USERS = ASR_CONFIG['concurrent_users']
'''
    
    # Agregar configuración si no existe
    if 'MICROSERVICIO DE INVENTARIO' not in content:
        # Agregar corsheaders a INSTALLED_APPS si no está
        if "'corsheaders'," not in content:
            content = content.replace(
                "INSTALLED_APPS = [",
                "INSTALLED_APPS = [\n    'corsheaders',"
            )
        
        # Agregar CorsMiddleware si no está
        if "'corsheaders.middleware.CorsMiddleware'," not in content:
            content = content.replace(
                "MIDDLEWARE = [",
                "MIDDLEWARE = [\n    'corsheaders.middleware.CorsMiddleware',"
            )
        
        # Agregar configuración del microservicio al final
        content += additional_config
        
        # Guardar archivo actualizado
        with open(settings_file, 'w', encoding='utf-8') as f:
            f.write(content)
        
        print("✅ Settings.py actualizado con configuración del microservicio")
    else:
        print("ℹ️  Settings.py ya contiene configuración del microservicio")

def update_main_urls():
    """
    Actualiza el archivo urls.py principal para incluir las rutas del microservicio
    """
    
    main_urls_file = os.path.join(project_path, 'casoArquisoft', 'urls.py')
    
    # Leer contenido actual
    with open(main_urls_file, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Rutas adicionales para el microservicio
    inventory_urls = """
    # URLs del microservicio de inventario
    path('api/inventory/', include('inventory_urls')),
    path('health/inventory/', InventoryHealthView.as_view(), name='inventory_health'),"""
    
    # Importaciones adicionales
    inventory_imports = """from django.http import JsonResponse
from django.utils import timezone
from django.views import View

class InventoryHealthView(View):
    def get(self, request):
        return JsonResponse({
            'status': 'healthy',
            'service': 'inventory_microservice',
            'timestamp': timezone.now().isoformat(),
            'version': '1.0.0'
        })

"""
    
    # Agregar si no existe
    if 'inventory_urls' not in content:
        # Agregar importación de include si no está
        if 'from django.urls import' in content and 'include' not in content:
            content = content.replace(
                'from django.urls import path',
                'from django.urls import path, include'
            )
        
        # Agregar las importaciones al inicio después de los imports existentes
        import_section = content.find('urlpatterns = [')
        content = content[:import_section] + inventory_imports + content[import_section:]
        
        # Agregar las rutas del microservicio
        urlpatterns_end = content.rfind(']')
        content = content[:urlpatterns_end] + inventory_urls + '\n' + content[urlpatterns_end:]
        
        # Guardar archivo actualizado
        with open(main_urls_file, 'w', encoding='utf-8') as f:
            f.write(content)
        
        print("✅ URLs principales actualizadas con rutas del microservicio")
    else:
        print("ℹ️  URLs principales ya contienen rutas del microservicio")

def create_inventory_migrations():
    """
    Crea los archivos de migración para el microservicio de inventario
    """
    
    # Crear directorio de migraciones si no existe
    migrations_dir = os.path.join(project_path, 'inventory_migrations')
    if not os.path.exists(migrations_dir):
        os.makedirs(migrations_dir)
    
    # Crear __init__.py
    init_file = os.path.join(migrations_dir, '__init__.py')
    with open(init_file, 'w') as f:
        f.write('')
    
    # Crear migración inicial
    migration_content = '''# Generated migration for inventory microservice
from django.db import migrations, models

class Migration(migrations.Migration):

    initial = True

    dependencies = []

    operations = [
        # Nota: Las tablas se crean directamente en la base de datos
        # usando el script SQL setup_inventory_db.sql
        # Esta migración es solo para registro en Django
        migrations.RunSQL(
            "SELECT 1;",  # No-op SQL
            reverse_sql="SELECT 1;",
        ),
    ]
'''
    
    migration_file = os.path.join(migrations_dir, '0001_initial.py')
    with open(migration_file, 'w') as f:
        f.write(migration_content)
    
    print("✅ Archivos de migración creados")

def setup_inventory_database():
    """
    Configura la base de datos para el microservicio
    """
    
    print("📦 Configurando base de datos del microservicio...")
    
    # Crear script de instalación de base de datos
    install_script_content = '''#!/bin/bash
# Script de instalación de la base de datos del microservicio de inventario

echo "Configurando base de datos del microservicio de inventario..."

# Verificar si MySQL está disponible
if ! command -v mysql &> /dev/null; then
    echo "MySQL no está instalado. Por favor instala MySQL primero."
    exit 1
fi

echo "Ejecutando script SQL..."

# Ejecutar el script SQL
mysql -u root -p < setup_inventory_db.sql

if [ $? -eq 0 ]; then
    echo "Base de datos configurada exitosamente"
    echo "Puedes verificar con:"
    echo "   mysql -u inventory_user -p"
    echo "   USE inventario_db;"
    echo "   SHOW TABLES;"
else
    echo "Error al configurar la base de datos"
    exit 1
fi
'''
    
    install_script_file = os.path.join(project_path, 'install_inventory_db.sh')
    with open(install_script_file, 'w', encoding='utf-8') as f:
        f.write(install_script_content)
    
    # Crear script para Windows
    install_script_content_win = '''@echo off
REM Script de instalación de la base de datos del microservicio de inventario

echo Configurando base de datos del microservicio de inventario...

REM Verificar si MySQL está disponible
mysql --version >nul 2>&1
if errorlevel 1 (
    echo MySQL no está instalado. Por favor instala MySQL primero.
    exit /b 1
)

echo Ejecutando script SQL...

REM Ejecutar el script SQL
mysql -u root -p < setup_inventory_db.sql

if %errorlevel% equ 0 (
    echo Base de datos configurada exitosamente
    echo Puedes verificar con:
    echo   mysql -u inventory_user -p
    echo   USE inventario_db;
    echo   SHOW TABLES;
) else (
    echo Error al configurar la base de datos
    exit /b 1
)
'''
    
    install_script_file_win = os.path.join(project_path, 'install_inventory_db.bat')
    with open(install_script_file_win, 'w', encoding='utf-8') as f:
        f.write(install_script_content_win)
    
    print("✅ Scripts de instalación de base de datos creados")

def create_test_files():
    """
    Crea archivos de prueba para verificar el funcionamiento del microservicio
    """
    
    # Crear archivo de pruebas unitarias
    test_content = '''import unittest
import json
from django.test import TestCase, Client
from django.urls import reverse
from unittest.mock import patch, MagicMock

class InventoryMicroserviceTests(TestCase):
    
    def setUp(self):
        self.client = Client()
        self.base_url = '/api/inventory'
    
    def test_health_check(self):
        """Prueba el endpoint de health check"""
        response = self.client.get('/health/inventory/')
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.content)
        self.assertEqual(data['status'], 'healthy')
        self.assertEqual(data['service'], 'inventory_microservice')
    
    @patch('inventory_microservice.InventoryService.create_transaction')
    def test_create_transaction(self, mock_create):
        """Prueba la creación de transacciones"""
        mock_create.return_value = {
            'success': True,
            'transaction_id': 'TXN_123',
            'processing_time_ms': 250
        }
        
        data = {
            'producto_id': 'zapatos',
            'tipo_operacion': 'RECEPCION',
            'cantidad': 50,
            'ubicacion': 'A1-B1',
            'operario_id': 'OP001'
        }
        
        response = self.client.post(
            f'{self.base_url}/transactions/',
            data=json.dumps(data),
            content_type='application/json'
        )
        
        self.assertEqual(response.status_code, 201)
        response_data = json.loads(response.content)
        self.assertTrue(response_data['success'])
        self.assertIn('transaction_id', response_data)
    
    @patch('inventory_microservice.InventoryService.get_stock_status')
    def test_get_stock_status(self, mock_get_stock):
        """Prueba la consulta de estado de stock"""
        mock_get_stock.return_value = {
            'producto_id': 'zapatos',
            'ubicacion': 'A1-B1',
            'cantidad': 100,
            'cantidad_disponible': 90
        }
        
        response = self.client.get(f'{self.base_url}/status/zapatos/A1-B1/')
        
        self.assertEqual(response.status_code, 200)
        response_data = json.loads(response.content)
        self.assertEqual(response_data['producto_id'], 'zapatos')
        self.assertEqual(response_data['cantidad'], 100)

class ASRComplianceTests(TestCase):
    """Pruebas para verificar cumplimiento del ASR"""
    
    def test_response_time_compliance(self):
        """Verifica que las respuestas sean menores a 500ms"""
        import time
        
        start_time = time.time()
        response = self.client.get('/health/inventory/')
        end_time = time.time()
        
        response_time_ms = (end_time - start_time) * 1000
        self.assertLess(response_time_ms, 500, 
                       f"Response time {response_time_ms}ms exceeds ASR limit of 500ms")
    
    def test_concurrent_user_simulation(self):
        """Simula múltiples usuarios concurrentes (prueba básica)"""
        import concurrent.futures
        import threading
        
        def make_request():
            client = Client()
            return client.get('/health/inventory/')
        
        # Simular 10 usuarios concurrentes (escalable a 1500 en pruebas de carga)
        with concurrent.futures.ThreadPoolExecutor(max_workers=10) as executor:
            futures = [executor.submit(make_request) for _ in range(10)]
            results = [future.result() for future in concurrent.futures.as_completed(futures)]
        
        # Verificar que todas las respuestas sean exitosas
        for response in results:
            self.assertEqual(response.status_code, 200)

if __name__ == '__main__':
    unittest.main()
'''
    
    test_file = os.path.join(project_path, 'test_inventory_microservice.py')
    with open(test_file, 'w', encoding='utf-8') as f:
        f.write(test_content)
    
    # Crear archivo de pruebas de carga con requests
    load_test_content = '''#!/usr/bin/env python3
"""
Script de pruebas de carga para verificar cumplimiento del ASR
Simula 1500 usuarios concurrentes realizando operaciones de inventario
"""

import requests
import json
import time
import threading
import statistics
from concurrent.futures import ThreadPoolExecutor, as_completed

# Configuración de pruebas
BASE_URL = 'http://localhost:8000'
CONCURRENT_USERS = 100  # Empezar con 100, escalar gradualmente
REQUESTS_PER_USER = 10
ASR_MAX_RESPONSE_TIME = 500  # milisegundos

class InventoryLoadTester:
    
    def __init__(self, base_url=BASE_URL):
        self.base_url = base_url
        self.results = []
        self.lock = threading.Lock()
    
    def make_inventory_request(self, user_id):
        """Simula operaciones de un usuario"""
        session = requests.Session()
        user_results = []
        
        for i in range(REQUESTS_PER_USER):
            try:
                # Alternar entre diferentes tipos de operaciones
                if i % 3 == 0:
                    # Crear transacción
                    data = {
                        'producto_id': f'producto_{user_id % 10}',
                        'tipo_operacion': 'RECEPCION',
                        'cantidad': 10,
                        'ubicacion': f'A{(user_id % 5) + 1}-B1',
                        'operario_id': f'OP{user_id:03d}'
                    }
                    start_time = time.time()
                    response = session.post(
                        f'{self.base_url}/api/inventory/transactions/',
                        json=data,
                        timeout=5
                    )
                    end_time = time.time()
                
                elif i % 3 == 1:
                    # Consultar stock
                    start_time = time.time()
                    response = session.get(
                        f'{self.base_url}/api/inventory/status/producto_{user_id % 10}/A{(user_id % 5) + 1}-B1/',
                        timeout=5
                    )
                    end_time = time.time()
                
                else:
                    # Health check
                    start_time = time.time()
                    response = session.get(
                        f'{self.base_url}/health/inventory/',
                        timeout=5
                    )
                    end_time = time.time()
                
                response_time_ms = (end_time - start_time) * 1000
                
                result = {
                    'user_id': user_id,
                    'request_id': i,
                    'status_code': response.status_code,
                    'response_time_ms': response_time_ms,
                    'success': response.status_code < 400,
                    'asr_compliant': response_time_ms <= ASR_MAX_RESPONSE_TIME
                }
                
                user_results.append(result)
                
                # Pequeña pausa para simular comportamiento real
                time.sleep(0.1)
                
            except Exception as e:
                user_results.append({
                    'user_id': user_id,
                    'request_id': i,
                    'status_code': 0,
                    'response_time_ms': 0,
                    'success': False,
                    'asr_compliant': False,
                    'error': str(e)
                })
        
        with self.lock:
            self.results.extend(user_results)
        
        return user_results
    
    def run_load_test(self):
        """Ejecuta la prueba de carga"""
        print(f"🚀 Iniciando prueba de carga con {CONCURRENT_USERS} usuarios concurrentes")
        print(f"📊 {REQUESTS_PER_USER} peticiones por usuario")
        print(f"⏱️  ASR: Tiempo máximo de respuesta {ASR_MAX_RESPONSE_TIME}ms")
        print("-" * 60)
        
        start_time = time.time()
        
        with ThreadPoolExecutor(max_workers=CONCURRENT_USERS) as executor:
            futures = [
                executor.submit(self.make_inventory_request, user_id) 
                for user_id in range(CONCURRENT_USERS)
            ]
            
            for future in as_completed(futures):
                try:
                    future.result()
                except Exception as e:
                    print(f"❌ Error en thread: {e}")
        
        end_time = time.time()
        total_time = end_time - start_time
        
        self.analyze_results(total_time)
    
    def analyze_results(self, total_time):
        """Analiza los resultados de la prueba"""
        if not self.results:
            print("❌ No se obtuvieron resultados")
            return
        
        total_requests = len(self.results)
        successful_requests = len([r for r in self.results if r['success']])
        asr_compliant_requests = len([r for r in self.results if r['asr_compliant']])
        
        response_times = [r['response_time_ms'] for r in self.results if r['success']]
        
        print("\\n📈 RESULTADOS DE LA PRUEBA DE CARGA")
        print("=" * 60)
        print(f"⏱️  Tiempo total de prueba: {total_time:.2f} segundos")
        print(f"👥 Usuarios concurrentes: {CONCURRENT_USERS}")
        print(f"📊 Total de peticiones: {total_requests}")
        print(f"✅ Peticiones exitosas: {successful_requests} ({(successful_requests/total_requests)*100:.1f}%)")
        print(f"⚡ Cumplimiento ASR (<500ms): {asr_compliant_requests} ({(asr_compliant_requests/total_requests)*100:.1f}%)")
        
        if response_times:
            print(f"⏱️  Tiempo promedio: {statistics.mean(response_times):.2f}ms")
            print(f"⏱️  Tiempo mediano: {statistics.median(response_times):.2f}ms")
            print(f"⏱️  Tiempo mínimo: {min(response_times):.2f}ms")
            print(f"⏱️  Tiempo máximo: {max(response_times):.2f}ms")
        
        requests_per_second = total_requests / total_time
        print(f"🚀 Throughput: {requests_per_second:.2f} peticiones/segundo")
        
        # Verificar cumplimiento del ASR
        asr_compliance_rate = (asr_compliant_requests / total_requests) * 100
        if asr_compliance_rate >= 95:
            print(f"✅ ASR CUMPLIDO: {asr_compliance_rate:.1f}% de peticiones bajo 500ms")
        else:
            print(f"❌ ASR NO CUMPLIDO: Solo {asr_compliance_rate:.1f}% de peticiones bajo 500ms")
        
        print("=" * 60)

if __name__ == '__main__':
    tester = InventoryLoadTester()
    tester.run_load_test()
'''
    
    load_test_file = os.path.join(project_path, 'load_test_inventory.py')
    with open(load_test_file, 'w', encoding='utf-8') as f:
        f.write(load_test_content)
    
    print("✅ Archivos de prueba creados")
    print("   - test_inventory_microservice.py (pruebas unitarias)")
    print("   - load_test_inventory.py (pruebas de carga)")

if __name__ == '__main__':
    integrate_inventory_microservice()