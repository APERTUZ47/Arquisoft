"""
Microservicio de Gestión de Inventario
======================================

ASR: Soportar 1500 usuarios concurrentes realizando operaciones de actualización
Tiempo de respuesta: <0.5 segundos por transacción
Operaciones: recepciones, picking, devoluciones

Arquitectura del Microservicio:
- API REST para operaciones CRUD de inventario
- Base de datos dedicada (o esquema separado)
- Caché para operaciones frecuentes
- Queue para procesar operaciones asíncronas
- Event-driven para notificar cambios
"""

from django.shortcuts import render
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
import json
import time
from datetime import datetime
import mysql.connector
from mysql.connector import Error
import threading
from queue import Queue

# Pool de conexiones para alta concurrencia
connection_pool = mysql.connector.pooling.MySQLConnectionPool(
    pool_name="inventory_pool",
    pool_size=20,  # Para manejar 1500 usuarios concurrentes
    pool_reset_session=True,
    host='localhost',
    database='inventario_db',
    user='inventory_user',
    password='inventory123'
)

# Queue para operaciones asíncronas
inventory_queue = Queue()

class InventoryService:
    """Servicio principal de gestión de inventario"""
    
    def __init__(self):
        self.cache = {}
        self.lock = threading.Lock()
    
    def get_connection(self):
        """Obtener conexión del pool"""
        return connection_pool.get_connection()
    
    def execute_with_retry(self, query, params=None, retries=3):
        """Ejecutar query con reintentos automáticos"""
        for attempt in range(retries):
            try:
                connection = self.get_connection()
                cursor = connection.cursor(dictionary=True)
                
                if params:
                    cursor.execute(query, params)
                else:
                    cursor.execute(query)
                
                if query.strip().upper().startswith('SELECT'):
                    result = cursor.fetchall()
                else:
                    connection.commit()
                    result = cursor.rowcount
                
                cursor.close()
                connection.close()
                return result
                
            except Error as e:
                if attempt == retries - 1:
                    raise e
                time.sleep(0.1)  # Breve pausa antes de reintentar
    
    def create_inventory_transaction(self, transaction_data):
        """
        Crear nueva transacción de inventario
        POST /api/inventory/transactions/
        """
        start_time = time.time()
        
        try:
            # Validar datos
            required_fields = ['producto_id', 'tipo_operacion', 'cantidad', 'ubicacion', 'operario_id']
            for field in required_fields:
                if field not in transaction_data:
                    return {'error': f'Campo requerido: {field}', 'status': 400}
            
            # Generar ID único para la transacción
            transaction_id = f"TXN_{int(time.time() * 1000000)}"
            
            # Query para insertar transacción
            insert_query = """
            INSERT INTO transacciones_inventario 
            (id, producto_id, tipo_operacion, cantidad, cantidad_anterior, cantidad_nueva, 
             ubicacion, operario_id, timestamp, estado)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, 'PROCESANDO')
            """
            
            # Obtener cantidad actual del producto
            current_stock = self.get_product_stock(transaction_data['producto_id'], transaction_data['ubicacion'])
            
            # Calcular nueva cantidad según tipo de operación
            cantidad = transaction_data['cantidad']
            if transaction_data['tipo_operacion'] == 'RECEPCION':
                nueva_cantidad = current_stock + cantidad
            elif transaction_data['tipo_operacion'] == 'PICKING':
                if current_stock < cantidad:
                    return {'error': 'Stock insuficiente', 'status': 400}
                nueva_cantidad = current_stock - cantidad
            elif transaction_data['tipo_operacion'] == 'DEVOLUCION':
                nueva_cantidad = current_stock + cantidad
            else:
                return {'error': 'Tipo de operación inválido', 'status': 400}
            
            # Ejecutar transacción
            params = (
                transaction_id,
                transaction_data['producto_id'],
                transaction_data['tipo_operacion'],
                cantidad,
                current_stock,
                nueva_cantidad,
                transaction_data['ubicacion'],
                transaction_data['operario_id'],
                datetime.now()
            )
            
            # Usar transacción de BD para consistencia
            connection = self.get_connection()
            connection.start_transaction()
            
            try:
                cursor = connection.cursor()
                
                # 1. Insertar transacción
                cursor.execute(insert_query, params)
                
                # 2. Actualizar stock del producto
                update_stock_query = """
                UPDATE productos_inventario 
                SET cantidad = %s, fecha_actualizacion = %s 
                WHERE producto_id = %s AND ubicacion = %s
                """
                cursor.execute(update_stock_query, (nueva_cantidad, datetime.now(), 
                                                  transaction_data['producto_id'], 
                                                  transaction_data['ubicacion']))
                
                # 3. Marcar transacción como completada
                cursor.execute(
                    "UPDATE transacciones_inventario SET estado = 'COMPLETADA' WHERE id = %s",
                    (transaction_id,)
                )
                
                connection.commit()
                cursor.close()
                
                # Limpiar caché para este producto
                cache_key = f"stock_{transaction_data['producto_id']}_{transaction_data['ubicacion']}"
                if cache_key in self.cache:
                    del self.cache[cache_key]
                
                # Calcular tiempo de respuesta
                response_time = (time.time() - start_time) * 1000
                
                # Enviar evento de cambio de inventario (para notificar a otros servicios)
                self.publish_inventory_event({
                    'transaction_id': transaction_id,
                    'producto_id': transaction_data['producto_id'],
                    'tipo_operacion': transaction_data['tipo_operacion'],
                    'cantidad_anterior': current_stock,
                    'cantidad_nueva': nueva_cantidad,
                    'ubicacion': transaction_data['ubicacion'],
                    'timestamp': datetime.now().isoformat(),
                    'response_time_ms': response_time
                })
                
                return {
                    'transaction_id': transaction_id,
                    'status': 'COMPLETADA',
                    'cantidad_anterior': current_stock,
                    'cantidad_nueva': nueva_cantidad,
                    'response_time_ms': response_time,
                    'status_code': 201
                }
                
            except Exception as e:
                connection.rollback()
                raise e
            finally:
                connection.close()
                
        except Exception as e:
            return {'error': str(e), 'status': 500}
    
    def get_product_stock(self, producto_id, ubicacion):
        """Obtener stock actual con caché"""
        cache_key = f"stock_{producto_id}_{ubicacion}"
        
        # Verificar caché primero
        if cache_key in self.cache:
            cache_data = self.cache[cache_key]
            if time.time() - cache_data['timestamp'] < 30:  # Caché válido por 30 segundos
                return cache_data['cantidad']
        
        # Consultar base de datos
        query = """
        SELECT cantidad FROM productos_inventario 
        WHERE producto_id = %s AND ubicacion = %s
        """
        
        result = self.execute_with_retry(query, (producto_id, ubicacion))
        
        if result:
            cantidad = result[0]['cantidad']
            # Actualizar caché
            self.cache[cache_key] = {
                'cantidad': cantidad,
                'timestamp': time.time()
            }
            return cantidad
        else:
            # Producto no existe, crear registro inicial
            self.create_product_record(producto_id, ubicacion)
            return 0
    
    def create_product_record(self, producto_id, ubicacion):
        """Crear registro inicial de producto"""
        query = """
        INSERT INTO productos_inventario (producto_id, ubicacion, cantidad, fecha_creacion)
        VALUES (%s, %s, 0, %s)
        ON DUPLICATE KEY UPDATE fecha_actualizacion = %s
        """
        timestamp = datetime.now()
        self.execute_with_retry(query, (producto_id, ubicacion, timestamp, timestamp))
    
    def update_inventory(self, transaction_id, update_data):
        """
        Actualizar transacción existente
        PUT /api/inventory/transactions/{transaction_id}/
        """
        start_time = time.time()
        
        try:
            query = """
            UPDATE transacciones_inventario 
            SET estado = %s, observaciones = %s, fecha_actualizacion = %s
            WHERE id = %s
            """
            
            result = self.execute_with_retry(query, (
                update_data.get('estado', 'ACTUALIZADA'),
                update_data.get('observaciones', ''),
                datetime.now(),
                transaction_id
            ))
            
            response_time = (time.time() - start_time) * 1000
            
            if result > 0:
                return {
                    'transaction_id': transaction_id,
                    'status': 'ACTUALIZADA',
                    'response_time_ms': response_time,
                    'status_code': 200
                }
            else:
                return {'error': 'Transacción no encontrada', 'status': 404}
                
        except Exception as e:
            return {'error': str(e), 'status': 500}
    
    def cancel_transaction(self, transaction_id):
        """
        Cancelar/revertir transacción
        DELETE /api/inventory/transactions/{transaction_id}/
        """
        start_time = time.time()
        
        try:
            # Obtener datos de la transacción original
            get_query = """
            SELECT producto_id, tipo_operacion, cantidad, ubicacion, estado
            FROM transacciones_inventario 
            WHERE id = %s
            """
            
            transaction_data = self.execute_with_retry(get_query, (transaction_id,))
            
            if not transaction_data:
                return {'error': 'Transacción no encontrada', 'status': 404}
            
            transaction = transaction_data[0]
            
            if transaction['estado'] != 'COMPLETADA':
                return {'error': 'Solo se pueden cancelar transacciones completadas', 'status': 400}
            
            # Crear transacción inversa
            inverse_operation = {
                'RECEPCION': 'PICKING',
                'PICKING': 'RECEPCION',
                'DEVOLUCION': 'PICKING'
            }
            
            reversal_data = {
                'producto_id': transaction['producto_id'],
                'tipo_operacion': inverse_operation[transaction['tipo_operacion']],
                'cantidad': transaction['cantidad'],
                'ubicacion': transaction['ubicacion'],
                'operario_id': 'SYSTEM_REVERSAL',
                'observaciones': f'Reversión de transacción {transaction_id}'
            }
            
            # Crear la transacción de reversión
            reversal_result = self.create_inventory_transaction(reversal_data)
            
            if 'error' not in reversal_result:
                # Marcar transacción original como cancelada
                cancel_query = """
                UPDATE transacciones_inventario 
                SET estado = 'CANCELADA', observaciones = %s, fecha_actualizacion = %s
                WHERE id = %s
                """
                
                self.execute_with_retry(cancel_query, (
                    f"Cancelada - Reversión: {reversal_result['transaction_id']}",
                    datetime.now(),
                    transaction_id
                ))
            
            response_time = (time.time() - start_time) * 1000
            
            return {
                'original_transaction_id': transaction_id,
                'reversal_transaction_id': reversal_result.get('transaction_id'),
                'status': 'CANCELADA',
                'response_time_ms': response_time,
                'status_code': 200
            }
            
        except Exception as e:
            return {'error': str(e), 'status': 500}
    
    def get_inventory_status(self, producto_id=None, ubicacion=None):
        """
        Consultar estado del inventario
        GET /api/inventory/status/
        """
        start_time = time.time()
        
        try:
            base_query = """
            SELECT pi.producto_id, pi.ubicacion, pi.cantidad, pi.fecha_actualizacion,
                   COUNT(ti.id) as transacciones_pendientes
            FROM productos_inventario pi
            LEFT JOIN transacciones_inventario ti ON pi.producto_id = ti.producto_id 
                AND pi.ubicacion = ti.ubicacion AND ti.estado = 'PROCESANDO'
            """
            
            conditions = []
            params = []
            
            if producto_id:
                conditions.append("pi.producto_id = %s")
                params.append(producto_id)
            
            if ubicacion:
                conditions.append("pi.ubicacion = %s")
                params.append(ubicacion)
            
            if conditions:
                base_query += " WHERE " + " AND ".join(conditions)
            
            base_query += " GROUP BY pi.producto_id, pi.ubicacion ORDER BY pi.fecha_actualizacion DESC"
            
            result = self.execute_with_retry(base_query, params if params else None)
            
            response_time = (time.time() - start_time) * 1000
            
            return {
                'inventory': result,
                'total_records': len(result),
                'response_time_ms': response_time,
                'status_code': 200
            }
            
        except Exception as e:
            return {'error': str(e), 'status': 500}
    
    def publish_inventory_event(self, event_data):
        """Publicar evento de cambio de inventario (para integración con otros microservicios)"""
        try:
            # En un ambiente real, esto se enviaría a un message broker (RabbitMQ, Kafka, SQS)
            # Por ahora, lo guardamos en una tabla de eventos
            event_query = """
            INSERT INTO eventos_inventario (evento_id, tipo_evento, datos, timestamp)
            VALUES (%s, 'INVENTORY_CHANGED', %s, %s)
            """
            
            event_id = f"EVT_{int(time.time() * 1000000)}"
            
            self.execute_with_retry(event_query, (
                event_id,
                json.dumps(event_data),
                datetime.now()
            ))
            
        except Exception as e:
            print(f"Error publicando evento: {e}")

# Instancia global del servicio
inventory_service = InventoryService()

# =============================================================================
# API ENDPOINTS
# =============================================================================

@csrf_exempt
@require_http_methods(["POST"])
def create_inventory_transaction(request):
    """
    POST /api/inventory/transactions/
    Crear nueva transacción de inventario (recepción, picking, devolución)
    """
    try:
        data = json.loads(request.body)
        result = inventory_service.create_inventory_transaction(data)
        
        status_code = result.get('status_code', result.get('status', 500))
        return JsonResponse(result, status=status_code)
        
    except json.JSONDecodeError:
        return JsonResponse({'error': 'Invalid JSON'}, status=400)
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)

@csrf_exempt
@require_http_methods(["PUT"])
def update_inventory_transaction(request, transaction_id):
    """
    PUT /api/inventory/transactions/{transaction_id}/
    Actualizar transacción existente
    """
    try:
        data = json.loads(request.body)
        result = inventory_service.update_inventory(transaction_id, data)
        
        status_code = result.get('status_code', result.get('status', 500))
        return JsonResponse(result, status=status_code)
        
    except json.JSONDecodeError:
        return JsonResponse({'error': 'Invalid JSON'}, status=400)
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)

@csrf_exempt
@require_http_methods(["DELETE"])
def cancel_inventory_transaction(request, transaction_id):
    """
    DELETE /api/inventory/transactions/{transaction_id}/
    Cancelar/revertir transacción
    """
    try:
        result = inventory_service.cancel_transaction(transaction_id)
        
        status_code = result.get('status_code', result.get('status', 500))
        return JsonResponse(result, status=status_code)
        
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)

@require_http_methods(["GET"])
def get_inventory_status(request):
    """
    GET /api/inventory/status/
    Consultar estado actual del inventario
    """
    try:
        producto_id = request.GET.get('producto_id')
        ubicacion = request.GET.get('ubicacion')
        
        result = inventory_service.get_inventory_status(producto_id, ubicacion)
        
        status_code = result.get('status_code', 200)
        return JsonResponse(result, status=status_code)
        
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)

@require_http_methods(["GET"])
def inventory_health_check(request):
    """
    GET /api/inventory/health/
    Health check específico para el microservicio de inventario
    """
    try:
        # Verificar conexión a base de datos
        test_result = inventory_service.execute_with_retry("SELECT 1 as test")
        
        # Verificar pool de conexiones
        pool_status = {
            'pool_size': connection_pool.pool_size,
            'connections_in_use': len([conn for conn in connection_pool._cnx_queue.queue if conn.is_connected()])
        }
        
        # Métricas de rendimiento
        metrics = {
            'cache_size': len(inventory_service.cache),
            'pool_status': pool_status,
            'database_test': 'OK' if test_result else 'FAILED'
        }
        
        return JsonResponse({
            'service': 'inventory-microservice',
            'status': 'healthy',
            'timestamp': datetime.now().isoformat(),
            'metrics': metrics
        })
        
    except Exception as e:
        return JsonResponse({
            'service': 'inventory-microservice',
            'status': 'unhealthy',
            'error': str(e),
            'timestamp': datetime.now().isoformat()
        }, status=503)