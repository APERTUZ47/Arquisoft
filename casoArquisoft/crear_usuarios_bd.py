"""
Script para crear usuarios en la base de datos según el Laboratorio de Pruebas de Carga
"""

import mysql.connector
from mysql.connector import Error
import sys

def conectar_bd():
    """Conecta a la base de datos MySQL"""
    try:
        conexion = mysql.connector.connect(
            host='tu-rds-endpoint.amazonaws.com',  # Cambiar por tu endpoint RDS
            database='rutasbodega',
            user='admin',
            password='tu-password'  # Cambiar por tu password
        )
        
        if conexion.is_connected():
            print("✅ Conexión exitosa a MySQL")
            return conexion
            
    except Error as e:
        print(f"❌ Error conectando a MySQL: {e}")
        return None

def crear_usuarios_prueba(conexion):
    """Crea usuarios de prueba para el laboratorio"""
    cursor = conexion.cursor()
    
    try:
        # Crear tabla de usuarios si no existe
        crear_tabla_usuarios = """
        CREATE TABLE IF NOT EXISTS usuarios (
            id INT AUTO_INCREMENT PRIMARY KEY,
            username VARCHAR(50) UNIQUE NOT NULL,
            password VARCHAR(100) NOT NULL,
            email VARCHAR(100),
            activo BOOLEAN DEFAULT TRUE,
            fecha_creacion TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
        """
        cursor.execute(crear_tabla_usuarios)
        print("✅ Tabla 'usuarios' verificada/creada")
        
        # Lista de usuarios para pruebas de carga
        usuarios_prueba = [
            ('usuario1', 'password123', 'usuario1@test.com'),
            ('usuario2', 'password123', 'usuario2@test.com'),
            ('usuario3', 'password123', 'usuario3@test.com'),
            ('usuario4', 'password123', 'usuario4@test.com'),
            ('usuario5', 'password123', 'usuario5@test.com'),
            ('admin_test', 'admin123', 'admin@test.com'),
            ('guest_test', 'guest123', 'guest@test.com'),
            ('load_test_user', 'load123', 'loadtest@test.com'),
        ]
        
        # Insertar usuarios
        insert_query = "INSERT INTO usuarios (username, password, email) VALUES (%s, %s, %s)"
        
        for username, password, email in usuarios_prueba:
            try:
                cursor.execute(insert_query, (username, password, email))
                print(f"✅ Usuario creado: {username}")
            except mysql.connector.IntegrityError:
                print(f"⚠️  Usuario ya existe: {username}")
        
        conexion.commit()
        print(f"✅ Proceso completado. {len(usuarios_prueba)} usuarios procesados")
        
    except Error as e:
        print(f"❌ Error creando usuarios: {e}")
    finally:
        cursor.close()

def verificar_usuarios(conexion):
    """Verifica que los usuarios se crearon correctamente"""
    cursor = conexion.cursor()
    
    try:
        cursor.execute("SELECT username, email, fecha_creacion FROM usuarios ORDER BY id")
        usuarios = cursor.fetchall()
        
        print("\n📊 Usuarios en la base de datos:")
        print("-" * 50)
        for username, email, fecha in usuarios:
            print(f"Usuario: {username:<15} Email: {email:<20} Creado: {fecha}")
        
        print(f"\n📈 Total usuarios: {len(usuarios)}")
        
    except Error as e:
        print(f"❌ Error verificando usuarios: {e}")
    finally:
        cursor.close()

def main():
    """Función principal"""
    print("🚀 Iniciando script de creación de usuarios para pruebas de carga")
    print("=" * 60)
    
    # Conectar a la base de datos
    conexion = conectar_bd()
    if not conexion:
        print("❌ No se pudo establecer conexión. Verifica:")
        print("   - Endpoint de RDS correcto")
        print("   - Credenciales correctas")
        print("   - Security Groups configurados")
        sys.exit(1)
    
    try:
        # Crear usuarios de prueba
        crear_usuarios_prueba(conexion)
        
        # Verificar usuarios creados
        verificar_usuarios(conexion)
        
        print("\n✅ Script ejecutado exitosamente")
        print("Los usuarios están listos para las pruebas de carga")
        
    except Exception as e:
        print(f"❌ Error general: {e}")
    
    finally:
        if conexion.is_connected():
            conexion.close()
            print("🔌 Conexión cerrada")

if __name__ == "__main__":
    main()