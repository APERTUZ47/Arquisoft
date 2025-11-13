from django.shortcuts import render, redirect
from django.contrib import messages
from .models import Usuario, LogAcceso
import logging
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
