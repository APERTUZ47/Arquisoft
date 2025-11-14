"""
Auth0 OAuth2 integration for Django authentication.
"""
import os
import json
import requests
from urllib.parse import urlencode, quote
from django.conf import settings
from django.shortcuts import redirect
from django.http import JsonResponse


# Auth0 configuration
AUTH0_DOMAIN = 'dev-v1wpfcpcvvftp5oi.us.auth0.com'
AUTH0_CLIENT_ID = 'rQtjppy7HeQlix5rRmpIcYx4boBZUcqs'  # Asegúrate de usar el client_id correcto
AUTH0_CLIENT_SECRET = 'hGFBMMpwdjE6NXU0d6R3NPURIOCxNbdNHBZq8vi-uGkfMr0O99dVtaodwZzZnj-4'
AUTH0_CALLBACK_URL = 'http://localhost:8000/auth/oauth0/callback'  # Cambiar a la URL pública en producción


def get_auth0_login_url(request):
    """
    Genera la URL de login de Auth0.
    """
    params = {
        'client_id': AUTH0_CLIENT_ID,
        'redirect_uri': AUTH0_CALLBACK_URL,
        'response_type': 'code',
        'scope': 'openid profile email',
        'state': request.session.get('oauth_state', 'state_default'),
    }
    
    auth0_url = f'https://{AUTH0_DOMAIN}/authorize?{urlencode(params)}'
    return auth0_url


def exchange_code_for_token(code):
    """
    Intercambia el código de autorización por un token de acceso.
    """
    token_url = f'https://{AUTH0_DOMAIN}/oauth/token'
    
    payload = {
        'client_id': AUTH0_CLIENT_ID,
        'client_secret': AUTH0_CLIENT_SECRET,
        'audience': f'https://{AUTH0_DOMAIN}/api/v2/',
        'grant_type': 'authorization_code',
        'code': code,
        'redirect_uri': AUTH0_CALLBACK_URL,
    }
    
    headers = {'Content-Type': 'application/json'}
    
    try:
        response = requests.post(token_url, json=payload, headers=headers, timeout=5)
        response.raise_for_status()
        return response.json()
    except requests.RequestException as e:
        return {'error': str(e)}


def get_user_info(access_token):
    """
    Obtiene la información del usuario desde Auth0 usando el access token.
    """
    userinfo_url = f'https://{AUTH0_DOMAIN}/userinfo'
    headers = {'Authorization': f'Bearer {access_token}'}
    
    try:
        response = requests.get(userinfo_url, headers=headers, timeout=5)
        response.raise_for_status()
        return response.json()
    except requests.RequestException as e:
        return {'error': str(e)}


def create_or_update_user(user_info):
    """
    Crea o actualiza un usuario en la base de datos basado en la información de Auth0.
    Retorna la instancia de Usuario.
    """
    from .models import Usuario
    
    email = user_info.get('email')
    username = user_info.get('nickname') or user_info.get('email', '').split('@')[0]
    name = user_info.get('name', '')
    
    if not email or not username:
        return None
    
    usuario, created = Usuario.objects.get_or_create(
        email=email,
        defaults={
            'username': username,
            'nombre_completo': name,
            'activo': True,
        }
    )
    
    # Actualizar información si el usuario ya existe
    if not created:
        usuario.nombre_completo = name
        usuario.save(update_fields=['nombre_completo'])
    
    return usuario
