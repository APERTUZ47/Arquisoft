#!/usr/bin/env python3
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
    
    print("\n🏁 Pruebas completadas")

if __name__ == '__main__':
    test_inventory_api()
