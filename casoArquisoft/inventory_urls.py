"""
URLs del Microservicio de Gestión de Inventario
===============================================
"""

from django.urls import path
import inventory_microservice_simple as inventory_views

app_name = 'inventory'

# URLs principales del microservicio de inventario (versión simplificada)
urlpatterns = [
    # API endpoints para transacciones de inventario
    path('transactions/', inventory_views.TransactionView.as_view(), name='transactions'),
    
    # API endpoints para consulta de stock
    path('status/<str:producto_id>/', inventory_views.StockStatusView.as_view(), name='stock_status'),
    path('status/<str:producto_id>/<str:ubicacion>/', inventory_views.StockStatusView.as_view(), name='stock_status_location'),
    
    # API endpoints para métricas y salud del sistema
    path('health/', inventory_views.HealthCheckView.as_view(), name='health_check'),
    path('metrics/', inventory_views.MetricsView.as_view(), name='metrics'),
]