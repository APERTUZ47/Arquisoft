# Guía de Configuración OAuth0 (Auth0)

## Resumen
Se ha implementado una integración OAuth0 completa en el `authMicroservice`. Los usuarios pueden ahora:
1. Hacer clic en "Login con Auth0" en la navegación principal
2. Ser redirigidos a la pantalla de login de Auth0
3. Autenticarse con Auth0
4. Ser redirigidos de vuelta a la aplicación con una sesión activa

## Configuración Requerida

### 1. Actualizar las URLs en el Dashboard de Auth0

**Importante:** Necesitas configurar TANTO la Callback URL como la Logout URL en el Dashboard de Auth0.

1. Ve a [Auth0 Dashboard](https://manage.auth0.com)
2. Selecciona tu aplicación (dev-v1wpfcpcvvftp5oi.us.auth0.com)
3. Ve a **Settings** → **Application URIs**

#### Allowed Callback URLs
En **Allowed Callback URLs**, agrega:
```
http://localhost:8000/auth/oauth0/callback
```

Para producción, usa tu dominio real:
```
https://tudominio.com/auth/oauth0/callback
```

#### Allowed Logout URLs
En **Allowed Logout URLs**, agrega:
```
http://localhost:8000/
```

Para producción:
```
https://tudominio.com/
```

5. Haz clic en **Save Changes**

### 2. Actualizar la Callback URL en el Código

Edita `authMicroservice/oauth0.py` y actualiza:

```python
AUTH0_CALLBACK_URL = 'http://localhost:8000/auth/oauth0/callback'  # Desarrollo
# O para producción:
AUTH0_CALLBACK_URL = 'https://tudominio.com/auth/oauth0/callback'
```

### 3. Actualizar el Client ID (Opcional)

**⚠️ IMPORTANTE:** El valor que proporcionaste como Client ID parece duplicar el dominio. 

Verifica el Client ID correcto en Auth0 Dashboard:
1. Ve a tu aplicación en el Dashboard
2. Copia el valor de **Client ID** (debería ser una cadena como `abc123XYZ...`)
3. Reemplaza el valor en `authMicroservice/oauth0.py`:

```python
AUTH0_CLIENT_ID = 'TU_CLIENT_ID_REAL'
```

## Estructura del Código

### Archivos Creados/Modificados

#### `authMicroservice/oauth0.py` (NUEVO)
- `get_auth0_login_url(request)` - Genera la URL de login de Auth0
- `exchange_code_for_token(code)` - Intercambia código por token
- `get_user_info(access_token)` - Obtiene información del usuario desde Auth0
- `create_or_update_user(user_info)` - Crea/actualiza usuario en la BD

#### `authMicroservice/views.py` (MODIFICADO)
- `register_view()` - Vista de registro (existente, sin cambios en lógica)
- `oauth0_login_view()` - Nueva vista que redirige a Auth0
- `oauth0_callback_view()` - Nueva vista que maneja el callback de Auth0

#### `authMicroservice/urls.py` (MODIFICADO)
- Agregadas rutas:
  - `path('oauth0/login/', oauth0_login_view, name='oauth0_login')`
  - `path('oauth0/callback/', oauth0_callback_view, name='oauth0_callback')`

#### `authMicroservice/templates/auth/login.html` (ACTUALIZADO)
- Nuevo template con botón "Login con Auth0"
- También proporciona opción de registrarse

#### `requirements.txt` (MODIFICADO)
- Agregado: `python-jose[cryptography]==3.3.0` (para JWT)
- `requests` ya estaba presente

#### `consultarRutasBodega/templates/consultarRutasBodega/base.html` (MODIFICADO)
- Agregado botón "Login con Auth0" en la navegación principal

### Tests Añadidos

Se agregaron 2 nuevos tests en `authMicroservice/tests.py`:

1. `test_oauth0_login_view_redirects_to_auth0()` - Verifica que la vista redirige correctamente
2. `test_oauth0_login_stores_state_in_session()` - Verifica protección CSRF con state

**Resultado:** 6 tests pasando (4 de register + 2 de OAuth0)

## Flujo de Autenticación OAuth0

```
1. Usuario hace clic en "Login con Auth0"
   ↓
2. Aplicación genera un state aleatorio y lo guarda en sesión (CSRF protection)
   ↓
3. Aplicación redirige a: 
   https://dev-v1wpfcpcvvftp5oi.us.auth0.com/authorize?
   client_id=xxx&
   redirect_uri=http://localhost:8000/auth/oauth0/callback&
   response_type=code&
   scope=openid%20profile%20email&
   state=xxx
   ↓
4. Usuario se autentica en Auth0 y autoriza
   ↓
5. Auth0 redirige a: http://localhost:8000/auth/oauth0/callback?code=xxx&state=xxx
   ↓
6. Aplicación:
   - Valida el state (CSRF)
   - Intercambia el código por un access token
   - Obtiene información del usuario
   - Crea o actualiza el usuario en la BD
   - Guarda el token en la sesión
   ↓
7. Usuario es redirigido a la página principal (index)
```

## Datos del Usuario desde Auth0

El sistema extrae los siguientes datos de Auth0:

- `email` - Email del usuario
- `nickname` - Usado como username (alternativa: parte anterior al @ del email)
- `name` - Nombre completo del usuario

## Logs de Acceso

Se crea un registro en `LogAcceso` con:
- `tipo_evento: 'LOGIN_OAUTH0'`
- IP address
- User Agent
- Timestamp

## Variantes de Implementación

### Opción 1: JWT Token (Recomendado para APIs)
Cambiar para guardar el token en un JWT cookie en lugar de sesión:

```python
response.set_cookie('oauth_token', access_token, max_age=86400, httponly=True)
```

### Opción 2: Refresh Token
Implementar refresh tokens para renovar el acceso automáticamente.

### Opción 3: Integración con Django Auth
Usar `django.contrib.auth` para integrar mejor con el sistema de permisos de Django.

## Troubleshooting

### Error: "invalid_grant"
- Verifica que el Client ID y Client Secret sean correctos
- Asegúrate de que la Callback URL está registrada en Auth0

### Error: "CSRF validation failed"
- El state no coincide - intenta de nuevo desde el principio
- Asegúrate de que las cookies de sesión están habilitadas

### Error: "invalid_client"
- El Client ID no es válido
- Verifica que usas el Client ID correcto de Auth0 Dashboard

## Testing

Para probar localmente:

```bash
# Instalar dependencias
pip install -r requirements.txt

# Ejecutar tests
python manage.py test authMicroservice

# Iniciar servidor
python manage.py runserver
```

Luego navega a `http://localhost:8000/` y haz clic en "Login con Auth0".

## Próximos Pasos

1. Configurar la Callback URL en Auth0 Dashboard (IMPORTANTE)
2. Verificar que el Client ID sea correcto
3. Probar el flujo de login completo
4. Implementar protección de vistas con `@login_required` si es necesario
5. Agregar middleware para gestionar sesiones expiradas
