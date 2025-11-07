from django.db import models
from django.contrib.auth.hashers import make_password, check_password
from django.utils import timezone
import re

class Usuario(models.Model):
    """Modelo de usuario personalizado con validaciones"""
    username = models.CharField(max_length=50, unique=True, db_index=True)
    email = models.EmailField(max_length=100, unique=True, db_index=True)
    password_hash = models.CharField(max_length=255)
    nombre_completo = models.CharField(max_length=100, blank=True)
    activo = models.BooleanField(default=True)
    fecha_registro = models.DateTimeField(default=timezone.now)
    ultimo_acceso = models.DateTimeField(null=True, blank=True)
    intentos_fallidos = models.IntegerField(default=0)
    bloqueado_hasta = models.DateTimeField(null=True, blank=True)
    
    class Meta:
        db_table = 'usuarios'
        verbose_name = 'Usuario'
        verbose_name_plural = 'Usuarios'
    
    def __str__(self):
        return self.username
    
    def set_password(self, raw_password):
        """Hash seguro de contraseña usando PBKDF2"""
        self.password_hash = make_password(raw_password)
    
    def check_password(self, raw_password):
        """Verifica contraseña hasheada"""
        return check_password(raw_password, self.password_hash)
    
    def actualizar_ultimo_acceso(self):
        """Actualiza timestamp de último acceso"""
        self.ultimo_acceso = timezone.now()
        self.intentos_fallidos = 0
        self.save(update_fields=['ultimo_acceso', 'intentos_fallidos'])
    
    def registrar_intento_fallido(self):
        """Registra intento fallido y bloquea si es necesario"""
        self.intentos_fallidos += 1
        
        # Bloquear cuenta después de 5 intentos fallidos (15 minutos)
        if self.intentos_fallidos >= 5:
            self.bloqueado_hasta = timezone.now() + timezone.timedelta(minutes=15)
        
        self.save(update_fields=['intentos_fallidos', 'bloqueado_hasta'])
    
    def esta_bloqueado(self):
        """Verifica si la cuenta está bloqueada"""
        if self.bloqueado_hasta and timezone.now() < self.bloqueado_hasta:
            return True
        elif self.bloqueado_hasta:
            # Desbloquear automáticamente si ya pasó el tiempo
            self.bloqueado_hasta = None
            self.intentos_fallidos = 0
            self.save(update_fields=['bloqueado_hasta', 'intentos_fallidos'])
        return False
    
    @staticmethod
    def validar_username(username):
        """Valida formato de username"""
        if len(username) < 3 or len(username) > 50:
            return False, "El username debe tener entre 3 y 50 caracteres"
        if not re.match(r'^[a-zA-Z0-9_]+$', username):
            return False, "El username solo puede contener letras, números y guión bajo"
        return True, ""
    
    @staticmethod
    def validar_email(email):
        """Valida formato de email"""
        patron = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        if not re.match(patron, email):
            return False, "Formato de email inválido"
        return True, ""
    
    @staticmethod
    def validar_password(password):
        """Valida fortaleza de contraseña"""
        if len(password) < 8:
            return False, "La contraseña debe tener al menos 8 caracteres"
        if not re.search(r'[A-Z]', password):
            return False, "La contraseña debe contener al menos una mayúscula"
        if not re.search(r'[a-z]', password):
            return False, "La contraseña debe contener al menos una minúscula"
        if not re.search(r'[0-9]', password):
            return False, "La contraseña debe contener al menos un número"
        return True, ""


class SesionUsuario(models.Model):
    """Modelo para tracking de sesiones activas"""
    usuario = models.ForeignKey(Usuario, on_delete=models.CASCADE, related_name='sesiones')
    session_key = models.CharField(max_length=40, unique=True, db_index=True)
    ip_address = models.GenericIPAddressField()
    user_agent = models.CharField(max_length=255, blank=True)
    fecha_inicio = models.DateTimeField(default=timezone.now)
    fecha_expiracion = models.DateTimeField()
    activa = models.BooleanField(default=True)
    
    class Meta:
        db_table = 'sesiones_usuario'
        verbose_name = 'Sesión de Usuario'
        verbose_name_plural = 'Sesiones de Usuario'
    
    def __str__(self):
        return f"{self.usuario.username} - {self.session_key[:8]}"
    
    def esta_expirada(self):
        """Verifica si la sesión expiró"""
        return timezone.now() > self.fecha_expiracion
    
    def cerrar_sesion(self):
        """Cierra la sesión"""
        self.activa = False
        self.save(update_fields=['activa'])


class LogAcceso(models.Model):
    """Modelo para auditoría de accesos"""
    TIPO_CHOICES = [
        ('LOGIN_EXITOSO', 'Login Exitoso'),
        ('LOGIN_FALLIDO', 'Login Fallido'),
        ('LOGOUT', 'Logout'),
        ('REGISTRO', 'Registro'),
        ('CAMBIO_PASSWORD', 'Cambio de Contraseña'),
    ]
    
    usuario = models.ForeignKey(Usuario, on_delete=models.CASCADE, null=True, blank=True, related_name='logs')
    username_intento = models.CharField(max_length=50)
    tipo_evento = models.CharField(max_length=20, choices=TIPO_CHOICES)
    ip_address = models.GenericIPAddressField()
    user_agent = models.CharField(max_length=255, blank=True)
    mensaje = models.TextField(blank=True)
    fecha_evento = models.DateTimeField(default=timezone.now, db_index=True)
    
    class Meta:
        db_table = 'logs_acceso'
        verbose_name = 'Log de Acceso'
        verbose_name_plural = 'Logs de Acceso'
        ordering = ['-fecha_evento']
    
    def __str__(self):
        return f"{self.tipo_evento} - {self.username_intento} - {self.fecha_evento}"