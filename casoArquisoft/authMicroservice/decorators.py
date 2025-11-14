"""
Decoradores de autenticación para proteger vistas.
"""
from functools import wraps
from django.http import JsonResponse, HttpResponseRedirect
from django.urls import reverse


def login_required_simple(view_func):
    """
    Decorator simple que verifica si el usuario está logeado.
    Verifica la sesión para 'usuario_id'.
    Si no está logeado, redirige al login de Auth0.
    """
    @wraps(view_func)
    def wrapper(request, *args, **kwargs):
        # Verificar si hay usuario_id en la sesión
        usuario_id = request.session.get('usuario_id')
        
        if not usuario_id:
            # Si es una request AJAX/API, retornar JSON
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                return JsonResponse({
                    'error': 'No autorizado',
                    'message': 'Debe iniciar sesión primero',
                    'status': 'unauthorized'
                }, status=401)
            
            # Si es una request normal, redirigir al login
            return HttpResponseRedirect(reverse('auth:oauth0_login'))
        
        # Si está logeado, ejecutar la vista
        return view_func(request, *args, **kwargs)
    
    return wrapper


def login_required_json(view_func):
    """
    Decorator para API endpoints que devuelven JSON.
    Retorna 401 JSON si no está logeado, sin redirigir.
    """
    @wraps(view_func)
    def wrapper(request, *args, **kwargs):
        usuario_id = request.session.get('usuario_id')
        
        if not usuario_id:
            return JsonResponse({
                'error': 'Unauthorized',
                'message': 'Authentication required',
                'status': 'error'
            }, status=401)
        
        # Pasar usuario_id al request para que la vista lo use
        request.usuario_id = usuario_id
        request.username = request.session.get('username', 'Unknown')
        
        return view_func(request, *args, **kwargs)
    
    return wrapper


def check_session(request):
    """
    Función helper para verificar si el usuario está en sesión.
    Retorna (bool, usuario_id, username) - (está_logeado, id, nombre)
    """
    usuario_id = request.session.get('usuario_id')
    username = request.session.get('username')
    
    if usuario_id:
        return True, usuario_id, username
    return False, None, None
