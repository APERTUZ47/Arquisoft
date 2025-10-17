# =============================================================================
# Configuración del Microservicio de Inventario
# Para integración con Django principal y cumplimiento del ASR
# =============================================================================

import os

# =============================================================================
# CONFIGURACIÓN DE BASE DE DATOS PARA MICROSERVICIO
# =============================================================================

# Configuración de la base de datos dedicada para inventario
INVENTORY_DATABASE_CONFIG = {
    'ENGINE': 'django.db.backends.mysql',
    'NAME': 'inventario_db',
    'USER': 'inventory_user',
    'PASSWORD': 'inventory123',
    'HOST': os.getenv('INVENTORY_DB_HOST', 'localhost'),
    'PORT': os.getenv('INVENTORY_DB_PORT', '3306'),
    'OPTIONS': {
        'charset': 'utf8mb4',
        'init_command': "SET sql_mode='STRICT_TRANS_TABLES'",
        'isolation_level': 'read committed',
        # Configuración para alta concurrencia
        'connect_timeout': 10,
        'read_timeout': 30,
        'write_timeout': 30,
    },
    'CONN_MAX_AGE': 600,  # Reutilizar conexiones por 10 minutos
}

# Pool de conexiones para el microservicio
INVENTORY_CONNECTION_POOL = {
    'pool_name': 'inventory_pool',
    'pool_size': 20,  # Para soportar 1500 usuarios concurrentes
    'pool_reset_session': True,
    'pool_pre_ping': True,  # Verificar conexiones antes de usar
    'max_overflow': 10,     # Conexiones adicionales si es necesario
}

# =============================================================================
# CONFIGURACIÓN DE CACHE PARA INVENTARIO
# =============================================================================

INVENTORY_CACHE_CONFIG = {
    'default_timeout': 300,  # 5 minutos
    'stock_timeout': 60,     # 1 minuto para datos de stock
    'transactions_timeout': 1800,  # 30 minutos para transacciones
    'key_prefix': 'inventory_',
}

# =============================================================================
# CONFIGURACIÓN DEL ASR (Architecture Significant Requirements)
# =============================================================================

ASR_CONFIG = {
    'max_response_time_ms': 500,  # Máximo 0.5 segundos por operación
    'concurrent_users': 1500,     # Usuarios concurrentes objetivo
    'operations_per_second': 300, # Operaciones por segundo esperadas
    'availability': 99.9,         # 99.9% de disponibilidad
    'error_rate_threshold': 0.1,  # Máximo 0.1% de errores
}

# =============================================================================
# CONFIGURACIÓN DE MONITOREO Y MÉTRICAS
# =============================================================================

MONITORING_CONFIG = {
    'enable_metrics': True,
    'metrics_retention_hours': 168,  # 7 días de retención
    'alert_thresholds': {
        'response_time_ms': 400,     # Alertar antes de violar ASR
        'error_rate_percent': 0.05,  # Alertar con 0.05% de errores
        'concurrent_connections': 1800,  # Alertar cerca del límite
    },
    'health_check_interval_seconds': 30,
}

# =============================================================================
# CONFIGURACIÓN DE EVENTOS PARA INTEGRACIÓN
# =============================================================================

EVENT_CONFIG = {
    'enable_events': True,
    'event_retention_hours': 72,  # 3 días de retención
    'event_types': [
        'INVENTORY_CREATED',
        'INVENTORY_UPDATED', 
        'INVENTORY_DELETED',
        'STOCK_LOW_WARNING',
        'TRANSACTION_COMPLETED',
        'TRANSACTION_FAILED',
    ],
    'publish_to_queue': False,  # Cambiar a True para RabbitMQ/SQS
}

# =============================================================================
# CONFIGURACIÓN DE SEGURIDAD
# =============================================================================

SECURITY_CONFIG = {
    'require_authentication': True,
    'api_key_header': 'X-API-Key',
    'rate_limiting': {
        'requests_per_minute': 1000,  # Por usuario
        'burst_limit': 100,           # Ráfagas permitidas
    },
    'allowed_origins': [
        'http://localhost:8000',      # Django principal
        'https://yourdomain.com',     # Producción
    ],
}

# =============================================================================
# CONFIGURACIÓN DE LOGGING
# =============================================================================

LOGGING_CONFIG = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'verbose': {
            'format': '{levelname} {asctime} {module} {process:d} {thread:d} {message}',
            'style': '{',
        },
        'simple': {
            'format': '{levelname} {message}',
            'style': '{',
        },
    },
    'handlers': {
        'file': {
            'level': 'INFO',
            'class': 'logging.handlers.RotatingFileHandler',
            'filename': 'logs/inventory_microservice.log',
            'maxBytes': 15728640,  # 15MB
            'backupCount': 5,
            'formatter': 'verbose',
        },
        'console': {
            'level': 'DEBUG',
            'class': 'logging.StreamHandler',
            'formatter': 'simple',
        },
        'metrics': {
            'level': 'INFO',
            'class': 'logging.handlers.RotatingFileHandler',
            'filename': 'logs/inventory_metrics.log',
            'maxBytes': 10485760,  # 10MB
            'backupCount': 3,
            'formatter': 'verbose',
        },
    },
    'loggers': {
        'inventory_microservice': {
            'handlers': ['file', 'console'],
            'level': 'INFO',
            'propagate': True,
        },
        'inventory_metrics': {
            'handlers': ['metrics'],
            'level': 'INFO',
            'propagate': False,
        },
    },
}

# =============================================================================
# FUNCIÓN PARA INTEGRAR CON DJANGO SETTINGS
# =============================================================================

def configure_django_for_inventory():
    """
    Configura Django para trabajar con el microservicio de inventario
    """
    try:
        from django.conf import settings
        
        # Agregar base de datos de inventario a Django
        if hasattr(settings, 'DATABASES'):
            settings.DATABASES['inventory'] = INVENTORY_DATABASE_CONFIG
        
        # Configurar cache para inventario si no existe
        if hasattr(settings, 'CACHES'):
            settings.CACHES['inventory'] = {
                'BACKEND': 'django.core.cache.backends.redis.RedisCache',
                'LOCATION': f"redis://{os.getenv('REDIS_HOST', 'localhost')}:6379/2",
                'OPTIONS': {
                    'CLIENT_CLASS': 'django_redis.client.DefaultClient',
                },
                'KEY_PREFIX': INVENTORY_CACHE_CONFIG['key_prefix'],
                'TIMEOUT': INVENTORY_CACHE_CONFIG['default_timeout'],
            }
        
        # Configurar logging si no está configurado
        if not hasattr(settings, 'LOGGING') or not settings.LOGGING:
            settings.LOGGING = LOGGING_CONFIG
        
        # Agregar aplicaciones necesarias
        inventory_apps = [
            'corsheaders',  # Para CORS si es necesario
        ]
        
        if hasattr(settings, 'INSTALLED_APPS'):
            for app in inventory_apps:
                if app not in settings.INSTALLED_APPS:
                    settings.INSTALLED_APPS.append(app)
        
        # Configurar middleware para métricas
        inventory_middleware = [
            'corsheaders.middleware.CorsMiddleware',
        ]
        
        if hasattr(settings, 'MIDDLEWARE'):
            for middleware in inventory_middleware:
                if middleware not in settings.MIDDLEWARE:
                    settings.MIDDLEWARE.insert(0, middleware)
                    
    except ImportError:
        # Django no está configurado aún
        pass

# =============================================================================
# CONFIGURACIÓN DE URLS PARA EL MICROSERVICIO
# =============================================================================

def get_inventory_urls():
    """
    Retorna las URLs del microservicio de inventario para incluir en Django
    """
    from django.urls import path, include
    from django.http import JsonResponse
    from django.utils import timezone
    
    return [
        path('api/inventory/', include('inventory_urls')),
        path('health/inventory/', include([
            path('', lambda request: JsonResponse({
                'status': 'healthy',
                'timestamp': timezone.now().isoformat(),
                'version': '1.0.0'
            })),
        ])),
    ]

# =============================================================================
# FUNCIONES DE UTILIDAD
# =============================================================================

class InventoryDatabaseRouter:
    """
    Router para dirigir consultas de inventario a la base de datos correcta
    """
    def db_for_read(self, model, **hints):
        if hasattr(model, '_meta') and model._meta.app_label == 'inventory':
            return 'inventory'
        return None

    def db_for_write(self, model, **hints):
        if hasattr(model, '_meta') and model._meta.app_label == 'inventory':
            return 'inventory'
        return None

    def allow_migrate(self, db, app_label, model_name=None, **hints):
        if app_label == 'inventory':
            return db == 'inventory'
        elif db == 'inventory':
            return False
        return None

def check_asr_compliance(response_time_ms, concurrent_users):
    """
    Verifica si una operación cumple con los ASR definidos
    """
    return {
        'response_time_ok': response_time_ms <= ASR_CONFIG['max_response_time_ms'],
        'concurrency_ok': concurrent_users <= ASR_CONFIG['concurrent_users'],
        'asr_compliant': (
            response_time_ms <= ASR_CONFIG['max_response_time_ms'] and 
            concurrent_users <= ASR_CONFIG['concurrent_users']
        ),
        'margin_ms': ASR_CONFIG['max_response_time_ms'] - response_time_ms,
    }

def get_environment_config():
    """
    Obtiene configuración específica del entorno (dev, staging, prod)
    """
    env = os.getenv('DJANGO_ENV', 'development')
    
    if env == 'production':
        return {
            'DEBUG': False,
            'CONN_MAX_AGE': 3600,  # 1 hora en producción
            'CACHE_TIMEOUT': 600,  # 10 minutos en producción
            'LOG_LEVEL': 'WARNING',
        }
    elif env == 'staging':
        return {
            'DEBUG': False,
            'CONN_MAX_AGE': 300,   # 5 minutos en staging
            'CACHE_TIMEOUT': 300,  # 5 minutos en staging
            'LOG_LEVEL': 'INFO',
        }
    else:  # development
        return {
            'DEBUG': True,
            'CONN_MAX_AGE': 60,    # 1 minuto en desarrollo
            'CACHE_TIMEOUT': 60,   # 1 minuto en desarrollo
            'LOG_LEVEL': 'DEBUG',
        }