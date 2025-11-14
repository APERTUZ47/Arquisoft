from django.shortcuts import render, redirect
from django.contrib import messages
from django.http import JsonResponse
from django.views.decorators.http import require_http_methods
from .models import Usuario, LogAcceso
from .oauth0 import get_auth0_login_url, exchange_code_for_token, get_user_info, create_or_update_user
import logging
import secrets
logger = logging.getLogger('authMicroservice')


def register_view(request):
    """Vista para registro de usuarios (reemplaza la antigua login_view).

    - GET: renderiza el formulario de registro
    - POST: valida datos, crea Usuario y redirige a 'home' con mensaje de éxito
    """
    if request.method == 'POST':
        username = request.POST.get('username', '').strip()
        email = request.POST.get('email', '').strip()
        password = request.POST.get('password', '')
        confirm = request.POST.get('confirm_password', '')

        # Validaciones básicas usando los métodos del modelo
        ok, msg = Usuario.validar_username(username)
        if not ok:
            messages.error(request, msg)
            return render(request, 'auth/register.html', {'username': username, 'email': email})

        ok, msg = Usuario.validar_email(email)
        if not ok:
            messages.error(request, msg)
            return render(request, 'auth/register.html', {'username': username, 'email': email})

        ok, msg = Usuario.validar_password(password)
        if not ok:
            messages.error(request, msg)
            return render(request, 'auth/register.html', {'username': username, 'email': email})

        if password != confirm:
            messages.error(request, "Las contraseñas no coinciden")
            return render(request, 'auth/register.html', {'username': username, 'email': email})

        # Verificar que no exista el usuario o email
        if Usuario.objects.filter(username=username).exists():
            messages.error(request, "El username ya está en uso")
            return render(request, 'auth/register.html', {'username': username, 'email': email})

        if Usuario.objects.filter(email=email).exists():
            messages.error(request, "El email ya está registrado")
            return render(request, 'auth/register.html', {'username': username, 'email': email})

        # Crear usuario
        usuario = Usuario(username=username, email=email)
        usuario.set_password(password)
        usuario.save()

        # Registrar log de registro
        try:
            LogAcceso.objects.create(
                usuario=usuario,
                username_intento=username,
                tipo_evento='REGISTRO',
                ip_address=request.META.get('REMOTE_ADDR', '127.0.0.1'),
                user_agent=request.META.get('HTTP_USER_AGENT', '')
            )
        except Exception:
            logger.exception('No se pudo crear LogAcceso para registro')

        messages.success(request, "Registro exitoso. Ahora puedes iniciar sesión.")
        # Redirigir a la página principal del frontend de rutas (index)
        # Usamos el namespace 'consultarRutasBodega:index' que existe en urls.py
        return redirect('consultarRutasBodega:index')

    return render(request, 'auth/register.html')


@require_http_methods(["GET"])
def oauth0_login_view(request):
    """
    Inicia el flujo de OAuth0 (Auth0).
    Redirige al usuario a la pantalla de login de Auth0.
    """
    # Generar un estado aleatorio para protección CSRF
    state = secrets.token_urlsafe(32)
    request.session['oauth_state'] = state
    request.session.save()

    auth0_url = get_auth0_login_url(request)
    return redirect(auth0_url)


@require_http_methods(["GET"])
def oauth0_callback_view(request):
    """
    Callback después de que el usuario se autentica en Auth0.
    Intercambia el código de autorización por un token de acceso
    y crea/actualiza el usuario en la base de datos.
    """
    code = request.GET.get('code')
    state = request.GET.get('state')
    error = request.GET.get('error')
    error_description = request.GET.get('error_description', '')

    # Validar que no haya error en Auth0
    if error:
        messages.error(request, f"Error en Auth0: {error} - {error_description}")
        return redirect('consultarRutasBodega:index')

    # Validar el estado para protección CSRF
    session_state = request.session.get('oauth_state')
    if not state or state != session_state:
        messages.error(request, "Error de validación CSRF. Intenta de nuevo.")
        return redirect('consultarRutasBodega:index')

    # Intercambiar código por token
    if not code:
        messages.error(request, "No se recibió código de autorización de Auth0.")
        return redirect('consultarRutasBodega:index')

    token_response = exchange_code_for_token(code)

    if 'error' in token_response:
        messages.error(request, f"Error al intercambiar código: {token_response.get('error')}")
        return redirect('consultarRutasBodega:index')

    access_token = token_response.get('access_token')
    if not access_token:
        messages.error(request, "No se pudo obtener el token de acceso de Auth0.")
        return redirect('consultarRutasBodega:index')

    # Obtener información del usuario desde Auth0
    user_info = get_user_info(access_token)

    if 'error' in user_info:
        messages.error(request, f"Error al obtener información del usuario: {user_info.get('error')}")
        return redirect('consultarRutasBodega:index')

    # Crear o actualizar usuario en la base de datos
    usuario = create_or_update_user(user_info)

    if not usuario:
        messages.error(request, "No se pudo crear/actualizar el usuario.")
        return redirect('consultarRutasBodega:index')

    # Guardar el usuario en la sesión (simulando login)
    request.session['usuario_id'] = usuario.id
    request.session['username'] = usuario.username
    request.session['email'] = usuario.email
    request.session['oauth_token'] = access_token
    request.session.save()

    # Registrar el login exitoso
    try:
        LogAcceso.objects.create(
            usuario=usuario,
            username_intento=usuario.username,
            tipo_evento='LOGIN_OAUTH0',
            ip_address=request.META.get('REMOTE_ADDR', '127.0.0.1'),
            user_agent=request.META.get('HTTP_USER_AGENT', '')
        )
    except Exception:
        logger.exception('No se pudo crear LogAcceso para OAuth0 login')

    messages.success(request, f"Bienvenido {usuario.username}! Login exitoso vía Auth0.")
    return redirect('consultarRutasBodega:index')
