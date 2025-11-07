from django.shortcuts import render, redirect
from django.contrib import messages
from .models import Usuario
import logging
logger = logging.getLogger('authMicroservice')

def login_view(request):
    if request.method == 'POST':
        username = request.POST.get('username').strip()
        password = request.POST.get('password')

        try:
            usuario = Usuario.objects.get(username=username)
        except Usuario.DoesNotExist:
            messages.error(request, "Usuario no encontrado")
            return render(request, 'auth/login.html')

        if usuario.check_password(password):
            messages.success(request, "Inicio de sesión exitoso")
            return redirect('home')

        messages.error(request, "Contraseña incorrecta")
    
    return render(request, 'auth/login.html')
