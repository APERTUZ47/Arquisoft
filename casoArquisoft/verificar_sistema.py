"""
Script para verificar la configuración de MySQL y Django
"""

import mysql.connector
from mysql.connector import Error
import sys
import os

def verificar_mysql():
    """Verifica que MySQL esté funcionando correctamente"""
    print("🔍 Verificando conexión a MySQL...")
    
    try:
        conexion = mysql.connector.connect(
            host='localhost',
            database='rutasbodega',
            user='django_user',
            password='django123',
            charset='utf8mb4'
        )
        
        if conexion.is_connected():
            cursor = conexion.cursor()
            
            # Verificar que la base de datos existe
            cursor.execute("SHOW DATABASES;")
            databases = cursor.fetchall()
            print("✅ Conexión exitosa a MySQL")
            print(f"📚 Bases de datos disponibles: {[db[0] for db in databases]}")
            
            # Verificar tablas en rutasbodega
            cursor.execute("SHOW TABLES;")
            tablas = cursor.fetchall()
            if tablas:
                print(f"📋 Tablas existentes: {[tabla[0] for tabla in tablas]}")
                
                # Contar registros en objetos si existe
                try:
                    cursor.execute("SELECT COUNT(*) FROM objetos;")
                    count = cursor.fetchone()[0]
                    print(f"📊 Objetos en base de datos: {count}")
                except:
                    print("ℹ️ Tabla 'objetos' no existe aún (se creará automáticamente)")
            else:
                print("ℹ️ No hay tablas creadas aún (se crearán automáticamente)")
            
            cursor.close()
            conexion.close()
            return True
            
    except Error as e:
        print(f"❌ Error conectando a MySQL: {e}")
        print("\n🔧 Posibles soluciones:")
        print("1. Verificar que MySQL esté ejecutándose: sudo systemctl status mysqld")
        print("2. Ejecutar script de configuración: bash setup_mysql.sh")
        print("3. Verificar credenciales de usuario")
        return False

def verificar_django():
    """Verifica que Django esté configurado correctamente"""
    print("\n🔍 Verificando configuración de Django...")
    
    try:
        # Verificar que Django esté instalado
        import django
        print(f"✅ Django instalado: versión {django.get_version()}")
        
        # Verificar mysql-connector-python
        import mysql.connector
        print("✅ mysql-connector-python instalado")
        
        # Verificar settings.py (si existe)
        if os.path.exists('casoArquisoft/settings.py'):
            print("✅ Archivo settings.py encontrado")
        else:
            print("⚠️ Archivo settings.py no encontrado en la ruta esperada")
        
        return True
        
    except ImportError as e:
        print(f"❌ Error en dependencias de Django: {e}")
        print("\n🔧 Instalar dependencias:")
        print("pip3 install django mysql-connector-python")
        return False

def ejecutar_migraciones():
    """Ejecuta las migraciones de Django"""
    print("\n🔍 Ejecutando migraciones de Django...")
    
    try:
        import subprocess
        
        # Ejecutar makemigrations
        result1 = subprocess.run(['python3', 'manage.py', 'makemigrations'], 
                               capture_output=True, text=True)
        
        if result1.returncode == 0:
            print("✅ makemigrations ejecutado correctamente")
        else:
            print(f"⚠️ makemigrations: {result1.stderr}")
        
        # Ejecutar migrate
        result2 = subprocess.run(['python3', 'manage.py', 'migrate'], 
                               capture_output=True, text=True)
        
        if result2.returncode == 0:
            print("✅ migrate ejecutado correctamente")
            return True
        else:
            print(f"❌ Error en migrate: {result2.stderr}")
            return False
            
    except Exception as e:
        print(f"❌ Error ejecutando migraciones: {e}")
        return False

def main():
    """Función principal de verificación"""
    print("🚀 Verificación del Sistema de Rutas de Bodega")
    print("=" * 50)
    
    # Verificar MySQL
    mysql_ok = verificar_mysql()
    
    # Verificar Django
    django_ok = verificar_django()
    
    # Si todo está bien, ejecutar migraciones
    if mysql_ok and django_ok:
        print("\n🎯 Configuración básica correcta, ejecutando migraciones...")
        migraciones_ok = ejecutar_migraciones()
        
        if migraciones_ok:
            print("\n✅ ¡Sistema configurado correctamente!")
            print("\n🚀 Comandos para ejecutar la aplicación:")
            print("   python3 manage.py runserver 0.0.0.0:8000")
            print("\n🌐 Acceder desde:")
            print("   http://tu-ip-publica:8000/consultarRutasBodega/")
        else:
            print("\n⚠️ Problemas con las migraciones, revisar configuración")
    else:
        print("\n❌ Hay problemas en la configuración básica")
        print("Revisa los errores anteriores y ejecuta las soluciones sugeridas")

if __name__ == "__main__":
    main()