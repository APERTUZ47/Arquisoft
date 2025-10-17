"""
Microservicio de Gestión de Inventario - Versión Simplificada
============================================================
Para demostración del ASR sin dependencias externas
"""

import json
import time
import uuid
from datetime import datetime
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
from django.utils.decorators import method_decorator
from django.views import View

# =============================================================================
# SIMULADOR DE BASE DE DATOS EN MEMORIA (para demostración)
# =============================================================================

# Stock simulado en memoria
INVENTORY_STOCK = {
    'zapatos_A1-B1': {'producto_id': 'zapatos', 'ubicacion': 'A1-B1', 'cantidad': 100, 'reservada': 10},
    'zapatos_A2-B1': {'producto_id': 'zapatos', 'ubicacion': 'A2-B1', 'cantidad': 75, 'reservada': 5},
    'caja_A2-B1': {'producto_id': 'caja', 'ubicacion': 'A2-B1', 'cantidad': 200, 'reservada': 20},
    'libro_A3-B1': {'producto_id': 'libro', 'ubicacion': 'A3-B1', 'cantidad': 300, 'reservada': 30},
    'mesa_A4-B1': {'producto_id': 'mesa', 'ubicacion': 'A4-B1', 'cantidad': 50, 'reservada': 2},
    'silla_A5-B1': {'producto_id': 'silla', 'ubicacion': 'A5-B1', 'cantidad': 80, 'reservada': 8},
}

# Transacciones en memoria
TRANSACTIONS = {}

# Métricas en memoria
METRICS = []

# =============================================================================
# SIMULADOR DE SERVICIOS DEL MICROSERVICIO
# =============================================================================

class InventoryServiceSimulator:
    """Simulador del servicio de inventario para demostración"""
    
    @staticmethod
    def create_transaction(producto_id, tipo_operacion, cantidad, ubicacion, operario_id):
        """Simula la creación de una transacción de inventario"""
        start_time = time.time()
        
        # Generar ID único de transacción
        transaction_id = f"TXN_{int(time.time() * 1000)}_{uuid.uuid4().hex[:8]}"
        
        # Clave para el stock
        stock_key = f"{producto_id}_{ubicacion}"
        
        # Verificar si existe el producto en la ubicación
        if stock_key not in INVENTORY_STOCK:
            return {
                'success': False,
                'error': 'Producto no encontrado en la ubicación especificada',
                'processing_time_ms': (time.time() - start_time) * 1000
            }
        
        stock_info = INVENTORY_STOCK[stock_key].copy()
        cantidad_anterior = stock_info['cantidad']
        
        # Procesar según tipo de operación
        if tipo_operacion == 'RECEPCION':
            nueva_cantidad = cantidad_anterior + cantidad
        elif tipo_operacion == 'PICKING':
            if cantidad_anterior < cantidad:
                return {
                    'success': False,
                    'error': 'Stock insuficiente',
                    'stock_actual': cantidad_anterior,
                    'cantidad_solicitada': cantidad,
                    'processing_time_ms': (time.time() - start_time) * 1000
                }
            nueva_cantidad = cantidad_anterior - cantidad
        elif tipo_operacion == 'DEVOLUCION':
            nueva_cantidad = cantidad_anterior + cantidad
        else:
            return {
                'success': False,
                'error': 'Tipo de operación inválido',
                'processing_time_ms': (time.time() - start_time) * 1000
            }
        
        # Simular pequeño retraso de procesamiento (para realismo)
        time.sleep(0.01)  # 10ms
        
        # Actualizar stock
        INVENTORY_STOCK[stock_key]['cantidad'] = nueva_cantidad
        
        # Registrar transacción
        transaction = {
            'id': transaction_id,
            'producto_id': producto_id,
            'tipo_operacion': tipo_operacion,
            'cantidad': cantidad,
            'cantidad_anterior': cantidad_anterior,
            'cantidad_nueva': nueva_cantidad,
            'ubicacion': ubicacion,
            'operario_id': operario_id,
            'estado': 'COMPLETADA',
            'timestamp': datetime.now().isoformat(),
            'processing_time_ms': (time.time() - start_time) * 1000
        }
        
        TRANSACTIONS[transaction_id] = transaction
        
        # Registrar métrica
        processing_time = (time.time() - start_time) * 1000
        METRICS.append({
            'operation': 'CREATE_TRANSACTION',
            'processing_time_ms': processing_time,
            'timestamp': datetime.now().isoformat(),
            'success': True,
            'asr_compliant': processing_time <= 500
        })
        
        return {
            'success': True,
            'transaction_id': transaction_id,
            'processing_time_ms': processing_time,
            'stock_anterior': cantidad_anterior,
            'stock_nuevo': nueva_cantidad,
            'asr_compliant': processing_time <= 500
        }
    
    @staticmethod
    def get_stock_status(producto_id, ubicacion=None):
        """Obtiene el estado del stock de un producto"""
        start_time = time.time()
        
        if ubicacion:
            # Consultar stock específico por ubicación
            stock_key = f"{producto_id}_{ubicacion}"
            if stock_key in INVENTORY_STOCK:
                stock = INVENTORY_STOCK[stock_key]
                result = {
                    'producto_id': producto_id,
                    'ubicacion': ubicacion,
                    'cantidad': stock['cantidad'],
                    'cantidad_reservada': stock['reservada'],
                    'cantidad_disponible': stock['cantidad'] - stock['reservada'],
                    'processing_time_ms': (time.time() - start_time) * 1000
                }
            else:
                result = {
                    'error': 'Producto no encontrado en la ubicación especificada',
                    'processing_time_ms': (time.time() - start_time) * 1000
                }
        else:
            # Consultar stock consolidado del producto
            stock_items = [v for k, v in INVENTORY_STOCK.items() if v['producto_id'] == producto_id]
            if stock_items:
                total_cantidad = sum(item['cantidad'] for item in stock_items)
                total_reservada = sum(item['reservada'] for item in stock_items)
                result = {
                    'producto_id': producto_id,
                    'total_cantidad': total_cantidad,
                    'total_reservada': total_reservada,
                    'total_disponible': total_cantidad - total_reservada,
                    'ubicaciones': len(stock_items),
                    'detalle_ubicaciones': stock_items,
                    'processing_time_ms': (time.time() - start_time) * 1000
                }
            else:
                result = {
                    'error': 'Producto no encontrado',
                    'processing_time_ms': (time.time() - start_time) * 1000
                }
        
        # Registrar métrica
        processing_time = (time.time() - start_time) * 1000
        METRICS.append({
            'operation': 'GET_STOCK_STATUS',
            'processing_time_ms': processing_time,
            'timestamp': datetime.now().isoformat(),
            'success': 'error' not in result,
            'asr_compliant': processing_time <= 500
        })
        
        return result
    
    @staticmethod
    def get_transaction_history(limit=50):
        """Obtiene el historial de transacciones"""
        start_time = time.time()
        
        # Obtener las últimas transacciones
        transactions = list(TRANSACTIONS.values())
        transactions.sort(key=lambda x: x['timestamp'], reverse=True)
        
        result = {
            'transactions': transactions[:limit],
            'total_count': len(transactions),
            'processing_time_ms': (time.time() - start_time) * 1000
        }
        
        # Registrar métrica
        processing_time = (time.time() - start_time) * 1000
        METRICS.append({
            'operation': 'GET_TRANSACTION_HISTORY',
            'processing_time_ms': processing_time,
            'timestamp': datetime.now().isoformat(),
            'success': True,
            'asr_compliant': processing_time <= 500
        })
        
        return result

# =============================================================================
# VISTAS DEL API DEL MICROSERVICIO
# =============================================================================

@method_decorator(csrf_exempt, name='dispatch')
class TransactionView(View):
    """API para gestión de transacciones de inventario"""
    
    def get(self, request):
        """Obtiene el historial de transacciones"""
        try:
            limit = int(request.GET.get('limit', 50))
            result = InventoryServiceSimulator.get_transaction_history(limit)
            
            return JsonResponse({
                'status': 'success',
                'data': result,
                'asr_compliant': result['processing_time_ms'] <= 500
            })
            
        except Exception as e:
            return JsonResponse({
                'status': 'error',
                'error': str(e)
            }, status=500)
    
    def post(self, request):
        """Crea una nueva transacción de inventario"""
        try:
            data = json.loads(request.body)
            
            # Validar campos requeridos
            required_fields = ['producto_id', 'tipo_operacion', 'cantidad', 'ubicacion', 'operario_id']
            for field in required_fields:
                if field not in data:
                    return JsonResponse({
                        'status': 'error',
                        'error': f'Campo requerido faltante: {field}'
                    }, status=400)
            
            # Validar tipo de operación
            if data['tipo_operacion'] not in ['RECEPCION', 'PICKING', 'DEVOLUCION']:
                return JsonResponse({
                    'status': 'error',
                    'error': 'Tipo de operación inválido. Debe ser: RECEPCION, PICKING, o DEVOLUCION'
                }, status=400)
            
            # Validar cantidad
            if not isinstance(data['cantidad'], int) or data['cantidad'] <= 0:
                return JsonResponse({
                    'status': 'error',
                    'error': 'La cantidad debe ser un número entero positivo'
                }, status=400)
            
            # Crear transacción
            result = InventoryServiceSimulator.create_transaction(
                producto_id=data['producto_id'],
                tipo_operacion=data['tipo_operacion'],
                cantidad=data['cantidad'],
                ubicacion=data['ubicacion'],
                operario_id=data['operario_id']
            )
            
            if result['success']:
                return JsonResponse({
                    'status': 'success',
                    'data': result
                }, status=201)
            else:
                return JsonResponse({
                    'status': 'error',
                    'error': result['error'],
                    'processing_time_ms': result['processing_time_ms']
                }, status=400)
            
        except json.JSONDecodeError:
            return JsonResponse({
                'status': 'error',
                'error': 'JSON inválido'
            }, status=400)
        except Exception as e:
            return JsonResponse({
                'status': 'error',
                'error': str(e)
            }, status=500)

@method_decorator(csrf_exempt, name='dispatch')
class StockStatusView(View):
    """API para consulta de estado de stock"""
    
    def get(self, request, producto_id, ubicacion=None):
        """Obtiene el estado del stock"""
        try:
            result = InventoryServiceSimulator.get_stock_status(producto_id, ubicacion)
            
            if 'error' in result:
                return JsonResponse({
                    'status': 'error',
                    'error': result['error'],
                    'processing_time_ms': result['processing_time_ms']
                }, status=404)
            else:
                return JsonResponse({
                    'status': 'success',
                    'data': result,
                    'asr_compliant': result['processing_time_ms'] <= 500
                })
                
        except Exception as e:
            return JsonResponse({
                'status': 'error',
                'error': str(e)
            }, status=500)

class HealthCheckView(View):
    """Health check del microservicio"""
    
    def get(self, request):
        """Verifica el estado del microservicio"""
        start_time = time.time()
        
        # Calcular estadísticas rápidas
        recent_metrics = [m for m in METRICS if 'timestamp' in m][-100:]  # Últimas 100 operaciones
        
        if recent_metrics:
            avg_response_time = sum(m['processing_time_ms'] for m in recent_metrics) / len(recent_metrics)
            success_rate = (sum(1 for m in recent_metrics if m['success']) / len(recent_metrics)) * 100
            asr_compliance_rate = (sum(1 for m in recent_metrics if m.get('asr_compliant', False)) / len(recent_metrics)) * 100
        else:
            avg_response_time = 0
            success_rate = 100
            asr_compliance_rate = 100
        
        processing_time = (time.time() - start_time) * 1000
        
        return JsonResponse({
            'status': 'healthy',
            'service': 'inventory_microservice',
            'version': '1.0.0',
            'timestamp': datetime.now().isoformat(),
            'processing_time_ms': processing_time,
            'asr_compliant': processing_time <= 500,
            'stats': {
                'total_transactions': len(TRANSACTIONS),
                'total_operations': len(METRICS),
                'avg_response_time_ms': round(avg_response_time, 2),
                'success_rate_percent': round(success_rate, 2),
                'asr_compliance_rate_percent': round(asr_compliance_rate, 2),
                'asr_target_ms': 500,
                'concurrent_users_target': 1500
            },
            'inventory_summary': {
                'total_products': len(set(v['producto_id'] for v in INVENTORY_STOCK.values())),
                'total_locations': len(INVENTORY_STOCK),
                'total_stock': sum(v['cantidad'] for v in INVENTORY_STOCK.values()),
                'total_reserved': sum(v['reservada'] for v in INVENTORY_STOCK.values())
            }
        })

class MetricsView(View):
    """API para métricas del microservicio"""
    
    def get(self, request):
        """Obtiene métricas de rendimiento"""
        try:
            limit = int(request.GET.get('limit', 100))
            recent_metrics = METRICS[-limit:] if METRICS else []
            
            # Calcular estadísticas
            if recent_metrics:
                operations = {}
                for metric in recent_metrics:
                    op = metric['operation']
                    if op not in operations:
                        operations[op] = {
                            'count': 0,
                            'total_time': 0,
                            'success_count': 0,
                            'asr_compliant_count': 0
                        }
                    
                    operations[op]['count'] += 1
                    operations[op]['total_time'] += metric['processing_time_ms']
                    if metric.get('success', False):
                        operations[op]['success_count'] += 1
                    if metric.get('asr_compliant', False):
                        operations[op]['asr_compliant_count'] += 1
                
                # Calcular promedios
                for op_data in operations.values():
                    op_data['avg_response_time_ms'] = round(op_data['total_time'] / op_data['count'], 2)
                    op_data['success_rate_percent'] = round((op_data['success_count'] / op_data['count']) * 100, 2)
                    op_data['asr_compliance_rate_percent'] = round((op_data['asr_compliant_count'] / op_data['count']) * 100, 2)
            else:
                operations = {}
            
            return JsonResponse({
                'status': 'success',
                'metrics': {
                    'operations': operations,
                    'recent_metrics': recent_metrics,
                    'total_operations': len(METRICS),
                    'asr_target_ms': 500
                }
            })
            
        except Exception as e:
            return JsonResponse({
                'status': 'error',
                'error': str(e)
            }, status=500)