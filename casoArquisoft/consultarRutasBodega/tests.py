from django.test import TestCase, Client
from django.urls import reverse
from authMicroservice.models import Usuario


class InventarioAccessControlTests(TestCase):
    """Tests para verificar que el microservicio de inventario está protegido"""

    def setUp(self):
        self.client = Client()
        # Crear usuario de prueba
        self.usuario = Usuario(username='testuser', email='test@example.com')
        self.usuario.set_password('TestPass123')
        self.usuario.save()

    def test_inventario_microservicio_sin_login_redirige_a_auth0(self):
        """Verifica que acceso sin login redirige a Auth0"""
        url = reverse('consultarRutasBodega:inventario_microservicio')
        response = self.client.get(url, follow=False)
        
        # Debe ser un redirect (302)
        self.assertEqual(response.status_code, 302)
        
        # El redirect debe ser a oauth0_login
        self.assertIn('oauth0/login', response.url)

    def test_inventario_microservicio_con_login_permite_acceso(self):
        """Verifica que con login en sesión permite acceso"""
        url = reverse('consultarRutasBodega:inventario_microservicio')
        
        # Simular login poniendo usuario_id en sesión
        session = self.client.session
        session['usuario_id'] = self.usuario.id
        session['username'] = self.usuario.username
        session.save()
        
        # Acceder a la vista
        response = self.client.get(url)
        
        # Debe permitir acceso (200)
        self.assertEqual(response.status_code, 200)
        self.assertIn(b'inventario', response.content.lower())

    def test_inventario_ajax_request_sin_login_retorna_json(self):
        """Verifica que AJAX request sin login retorna JSON 401"""
        url = reverse('consultarRutasBodega:inventario_microservicio')
        
        # Hacer request AJAX
        response = self.client.get(
            url,
            HTTP_X_REQUESTED_WITH='XMLHttpRequest'
        )
        
        # Debe retornar 401
        self.assertEqual(response.status_code, 401)
        
        # Debe ser JSON
        data = response.json()
        self.assertEqual(data['status'], 'unauthorized')
        self.assertIn('debe iniciar sesión', data['message'].lower())

    def test_inventario_microservicio_con_sesion_expirada(self):
        """Verifica comportamiento cuando sesión está vacía"""
        url = reverse('consultarRutasBodega:inventario_microservicio')
        
        # Forzar sesión vacía
        session = self.client.session
        session['usuario_id'] = None
        session.save()
        
        response = self.client.get(url, follow=False)
        
        # Debe redirigir
        self.assertEqual(response.status_code, 302)
        self.assertIn('oauth0/login', response.url)
