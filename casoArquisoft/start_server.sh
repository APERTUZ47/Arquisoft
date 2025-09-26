#!/bin/bash
# Script para iniciar automáticamente la aplicación Django

# Navegar al directorio de la aplicación
cd /home/ec2-user/Arquisoft/casoArquisoft

# Iniciar MySQL si no está ejecutándose
sudo systemctl start mysqld

# Esperar a que MySQL esté listo
sleep 5

# Ejecutar servidor Django
echo "🚀 Iniciando servidor Django..."
python3 manage.py runserver 0.0.0.0:8000