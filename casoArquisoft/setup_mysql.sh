#!/bin/bash
# Script para configurar MySQL en la instancia EC2 para la aplicación Django

echo "🚀 Configurando MySQL para Django - Sistema de Rutas de Bodega"
echo "=" * 60

# Actualizar sistema
echo "📦 Actualizando sistema..."
sudo yum update -y

# Instalar MySQL Server
echo "🗄️ Instalando MySQL Server..."
sudo yum install -y mysql-server

# Iniciar y habilitar MySQL
echo "▶️ Iniciando MySQL..."
sudo systemctl start mysqld
sudo systemctl enable mysqld

# Configurar MySQL (crear base de datos y usuario)
echo "🔧 Configurando base de datos..."
sudo mysql -e "
CREATE DATABASE IF NOT EXISTS rutasbodega CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
CREATE USER IF NOT EXISTS 'django_user'@'localhost' IDENTIFIED BY 'django123';
GRANT ALL PRIVILEGES ON rutasbodega.* TO 'django_user'@'localhost';
CREATE USER IF NOT EXISTS 'django_user'@'%' IDENTIFIED BY 'django123';
GRANT ALL PRIVILEGES ON rutasbodega.* TO 'django_user'@'%';
FLUSH PRIVILEGES;
"

# Verificar conexión
echo "✅ Verificando conexión..."
mysql -u django_user -pdjango123 -e "SELECT 'Conexión exitosa' as status;"

# Instalar dependencias Python
echo "🐍 Instalando dependencias Python..."
pip3 install mysql-connector-python mysqlclient

echo "✅ Configuración de MySQL completada!"
echo ""
echo "📋 Detalles de conexión:"
echo "  Host: localhost"
echo "  Database: rutasbodega"
echo "  User: django_user"
echo "  Password: django123"
echo ""
echo "🚀 Ahora puedes ejecutar tu aplicación Django"