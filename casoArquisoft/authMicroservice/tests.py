from django.test import TestCase, Client
from django.urls import reverse
from .models import Usuario

class LoginSecurityTests(TestCase):
    def setUp(self):
        self.client = Client()
        # usuario de prueba
        u = Usuario(username='testuser', email='test@example.com')
        u.set_password('Testpass123')
        u.save()

    def test_login_with_unusual_input_does_not_crash(self):
        url = reverse('auth:login')  
        suspicious_inputs = [
            "normaluser",
            "admin' OR '1'='1",  
            "áéíóú; DROP TABLE users;",
            "<script>alert(1)</script>",
            ""  # empty
        ]
        for val in suspicious_inputs:
            response = self.client.post(url, {'username': val, 'password': 'whatever'})
            self.assertNotEqual(response.status_code, 500)
            self.assertIn(response.status_code, (200, 302))
