"""casoArquisoft URL Configuration

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/3.2/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path, include
from django.http import JsonResponse
from django.utils import timezone

def health_check(request):
    """Health check para todos los microservicios"""
    return JsonResponse({
        'status': 'healthy',
        'timestamp': timezone.now().isoformat(),
        'microservices': {
            'auth': 'active',
            'rutas': 'active',
        }
    })

urlpatterns = [
    path('admin/', admin.site.urls),
    
    # Health check general
    path('health/', health_check, name='health_check'),
    
    # Microservicio de Autenticación
    path('auth/', include('authMicroservice.urls')),
    
    # Microservicio de Rutas de Bodega
    path('', include('consultarRutasBodega.urls')),
]