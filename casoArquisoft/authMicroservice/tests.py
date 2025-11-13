from django.test import TestCase, Client
from django.urls import reverse
from .models import Usuario

class RegisterSecurityTests(TestCase):
    def setUp(self):
        self.client = Client()
        # usuario de prueba (existente)
        u = Usuario(username='testuser', email='test@example.com')
        u.set_password('Testpass123')
        u.save()

    def test_register_with_unusual_input_does_not_crash(self):
        url = reverse('auth:register')
        suspicious_inputs = [
            "normaluser",
            "admin' OR '1'='1",
            "áéíóú; DROP TABLE users;",
            "<script>alert(1)</script>",
            ""  # empty
        ]
        for val in suspicious_inputs:
            data = {'username': val, 'email': f'{val or "x"}@example.com', 'password': 'Whatever123', 'confirm_password': 'Whatever123'}
            response = self.client.post(url, data)
            self.assertNotEqual(response.status_code, 500)
            self.assertIn(response.status_code, (200, 302))

    def test_successful_registration_creates_user(self):
        url = reverse('auth:register')
        username = 'newuser123'
        email = 'newuser123@example.com'
        data = {'username': username, 'email': email, 'password': 'StrongPass1', 'confirm_password': 'StrongPass1'}
        count_before = Usuario.objects.count()
        response = self.client.post(url, data)
        # view may redirect or render; ensure no server error
        self.assertNotEqual(response.status_code, 500)
        # user created
        self.assertTrue(Usuario.objects.filter(username=username, email=email).exists())
        self.assertEqual(Usuario.objects.count(), count_before + 1)

    def test_sql_injection_attempt_does_not_delete_or_corrupt_db(self):
        url = reverse('auth:register')
        malicious_username = "injection'; DROP TABLE usuarios; --"
        email = 'sqli@example.com'
        data = {'username': malicious_username, 'email': email, 'password': 'StrongPass1', 'confirm_password': 'StrongPass1'}
        count_before = Usuario.objects.count()
        response = self.client.post(url, data)
        # no server error
        self.assertNotEqual(response.status_code, 500)
        # DB should not have been reduced (no table drop)
        count_after = Usuario.objects.count()
        self.assertGreaterEqual(count_after, count_before)
        # If malicious username was accepted, it will be stored as data; that's fine — the ORM prevents execution
