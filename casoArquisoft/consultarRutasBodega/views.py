from django.shortcuts import render
from django.http import HttpResponse, JsonResponse
from django.db import connection
import mysql.connector
from mysql.connector import Error
import time
from datetime import datetime
import os


def obtener_conexion_mysql():
    """Obtiene conexión a MySQL local en la instancia"""
    try:
        conexion = mysql.connector.connect(
            host='localhost',
            database='rutasbodega',
            user='django_user',
            password='django123',
            charset='utf8mb4'
        )
        return conexion
    except Error as e:
        print(f"Error conectando a MySQL local: {e}")
        return None

def crear_tablas_si_no_existen():
    """Crea las tablas necesarias si no existen"""
    conexion = obtener_conexion_mysql()
    if not conexion:
        return False
    
    cursor = conexion.cursor()
    try:
        # Tabla de objetos
        crear_objetos = """
        CREATE TABLE IF NOT EXISTS objetos (
            id INT AUTO_INCREMENT PRIMARY KEY,
            nombre VARCHAR(50) UNIQUE NOT NULL,
            descripcion VARCHAR(10) NOT NULL,
            ubicacion VARCHAR(20) NOT NULL,
            activo BOOLEAN DEFAULT TRUE,
            fecha_creacion TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
        """
        cursor.execute(crear_objetos)
        
        # Tabla de consultas
        crear_consultas = """
        CREATE TABLE IF NOT EXISTS consultas_rutas (
            id INT AUTO_INCREMENT PRIMARY KEY,
            objeto_origen VARCHAR(50) NOT NULL,
            objeto_destino VARCHAR(50) NOT NULL,
            ruta_resultado VARCHAR(100) NOT NULL,
            tiempo_frontend DECIMAL(10,2),
            tiempo_backend DECIMAL(10,2) NOT NULL,
            tiempo_aws_obj1 DECIMAL(10,2) DEFAULT 0,
            tiempo_aws_obj2 DECIMAL(10,2) DEFAULT 0,
            tiempo_concatenacion DECIMAL(10,2) DEFAULT 0,
            ip_cliente VARCHAR(45),
            fecha_consulta TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            INDEX idx_fecha (fecha_consulta),
            INDEX idx_objetos (objeto_origen, objeto_destino)
        )
        """
        cursor.execute(crear_consultas)
        
        conexion.commit()
        return True
        
    except Error as e:
        print(f"Error creando tablas: {e}")
        return False
    finally:
        cursor.close()
        conexion.close()

def poblar_datos_iniciales():
    """Puebla la tabla de objetos con datos iniciales si está vacía"""
    conexion = obtener_conexion_mysql()
    if not conexion:
        return False
    
    cursor = conexion.cursor()
    try:
        # Verificar si ya hay datos
        cursor.execute("SELECT COUNT(*) FROM objetos")
        count = cursor.fetchone()[0]
        
        if count == 0:
            # Insertar datos iniciales
            objetos_iniciales = [
                ('zapatos', 'Z', 'A1-B1'),
                ('caja', 'C', 'A2-B1'),
                ('libro', 'L', 'A3-B1'),
                ('mesa', 'M', 'A4-B1'),
                ('silla', 'S', 'A5-B1'),
                ('computadora', 'CO', 'A6-B1'),
                ('telefono', 'T', 'A7-B1'),
                ('reloj', 'R', 'A8-B1'),
            ]
            
            insert_query = "INSERT INTO objetos (nombre, descripcion, ubicacion) VALUES (%s, %s, %s)"
            cursor.executemany(insert_query, objetos_iniciales)
            conexion.commit()
            print(f"✅ Insertados {len(objetos_iniciales)} objetos iniciales")
            
        return True
        
    except Error as e:
        print(f"Error poblando datos: {e}")
        return False
    finally:
        cursor.close()
        conexion.close()

def index(request):
    """Vista principal para consultar rutas de bodega"""
    # Inicializar base de datos si es necesario
    crear_tablas_si_no_existen()
    poblar_datos_iniciales()
    
    # Obtener estadísticas básicas
    conexion = obtener_conexion_mysql()
    total_objetos = 0
    total_consultas = 0
    
    if conexion:
        cursor = conexion.cursor()
        try:
            cursor.execute("SELECT COUNT(*) FROM objetos WHERE activo = TRUE")
            total_objetos = cursor.fetchone()[0]
            
            cursor.execute("SELECT COUNT(*) FROM consultas_rutas")
            total_consultas = cursor.fetchone()[0]
        except:
            pass
        finally:
            cursor.close()
            conexion.close()
    
    return render(request, 'consultarRutasBodega/index.html', {
        'titulo': 'Consultar Rutas de Bodega',
        'mensaje': 'Bienvenido al sistema de consulta de rutas de bodega',
        'total_objetos': total_objetos,
        'total_consultas': total_consultas
    })

def consultar_rutas(request):
    """Vista para mostrar las rutas disponibles desde la base de datos local"""
    conexion = obtener_conexion_mysql()
    objetos_ejemplo = []
    
    if conexion:
        cursor = conexion.cursor()
        try:
            cursor.execute("""
                SELECT id, nombre, descripcion, ubicacion, fecha_creacion 
                FROM objetos 
                WHERE activo = TRUE 
                ORDER BY nombre
            """)
            
            resultados = cursor.fetchall()
            
            for id_obj, nombre, descripcion, ubicacion, fecha_creacion in resultados:
                objetos_ejemplo.append({
                    'id': id_obj,
                    'objeto': nombre,
                    'descripcion': descripcion,
                    'ubicacion': ubicacion,
                    'fecha_creacion': fecha_creacion
                })
                
        except Error as e:
            print(f"Error consultando objetos: {e}")
        finally:
            cursor.close()
            conexion.close()
    
    # Si no hay datos en BD, usar datos por defecto
    if not objetos_ejemplo:
        objetos_ejemplo = [
            {'id': 1, 'objeto': 'zapatos', 'descripcion': 'Z', 'ubicacion': 'A1-B1'},
            {'id': 2, 'objeto': 'caja', 'descripcion': 'C', 'ubicacion': 'A2-B1'},
            {'id': 3, 'objeto': 'libro', 'descripcion': 'L', 'ubicacion': 'A3-B1'},
            {'id': 4, 'objeto': 'mesa', 'descripcion': 'M', 'ubicacion': 'A4-B1'},
            {'id': 5, 'objeto': 'silla', 'descripcion': 'S', 'ubicacion': 'A5-B1'},
            {'id': 6, 'objeto': 'computadora', 'descripcion': 'CO', 'ubicacion': 'A6-B1'},
            {'id': 7, 'objeto': 'telefono', 'descripcion': 'T', 'ubicacion': 'A7-B1'},
            {'id': 8, 'objeto': 'reloj', 'descripcion': 'R', 'ubicacion': 'A8-B1'},
        ]
    
    return render(request, 'consultarRutasBodega/rutas.html', {
        'objetos': objetos_ejemplo
    })

def buscar_ruta(request):
    """Vista para buscar ruta entre objetos usando base de datos local"""
    if request.method == 'POST':
        # Registrar tiempo de inicio del procesamiento
        inicio_backend = time.time()
        timestamp_inicio = datetime.now()
        
        objeto1 = request.POST.get('objeto1')
        objeto2 = request.POST.get('objeto2')
        tiempo_frontend = request.POST.get('tiempo_frontend', '0')
        
        # Obtener IP del cliente
        ip_cliente = obtener_ip_cliente(request)
        
        # Buscar objetos en la base de datos
        desc1, ubicacion1 = obtener_descripcion_objeto(objeto1)
        desc2, ubicacion2 = obtener_descripcion_objeto(objeto2)
        
        # Simular procesamiento de consulta
        time.sleep(0.1)  # Simula 100ms de procesamiento
        
        # Generar ruta resultado
        ruta_resultado = f"{desc1}-{desc2}"
        
        # Calcular tiempo total de procesamiento en backend
        fin_backend = time.time()
        tiempo_backend = round((fin_backend - inicio_backend) * 1000, 2)
        
        # Procesar tiempo del frontend
        tiempo_frontend_float = float(tiempo_frontend) if tiempo_frontend != '0' else None
        diferencia_tiempo = None
        if tiempo_frontend_float and tiempo_frontend_float > tiempo_backend:
            diferencia_tiempo = round(tiempo_frontend_float - tiempo_backend, 2)
        
        # Calcular tiempos simulados para consultas BD
        tiempo_get_objeto1 = round(tiempo_backend * 0.3, 1)
        tiempo_get_objeto2 = round(tiempo_backend * 0.3, 1)
        tiempo_concatenacion = round(tiempo_backend * 0.4, 1)
        
        # Guardar consulta en base de datos
        guardar_consulta_en_bd(
            objeto1, objeto2, ruta_resultado,
            tiempo_frontend_float, tiempo_backend,
            tiempo_get_objeto1, tiempo_get_objeto2, tiempo_concatenacion,
            ip_cliente
        )
        
        return render(request, 'consultarRutasBodega/resultado_ruta.html', {
            'objeto1': objeto1,
            'objeto2': objeto2,
            'ruta': ruta_resultado,
            'tiempo_frontend': tiempo_frontend_float,
            'tiempo_backend': tiempo_backend,
            'diferencia_tiempo': diferencia_tiempo,
            'tiempo_get_objeto1': tiempo_get_objeto1,
            'tiempo_get_objeto2': tiempo_get_objeto2,
            'tiempo_concatenacion': tiempo_concatenacion,
            'timestamp_inicio': timestamp_inicio.strftime('%H:%M:%S.%f')[:-3],
            'timestamp_fin': datetime.now().strftime('%H:%M:%S.%f')[:-3],
            'ubicacion1': ubicacion1,
            'ubicacion2': ubicacion2
        })
    
    return render(request, 'consultarRutasBodega/buscar_ruta.html')

def obtener_ip_cliente(request):
    """Obtiene la IP real del cliente"""
    x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
    if x_forwarded_for:
        ip = x_forwarded_for.split(',')[0]
    else:
        ip = request.META.get('REMOTE_ADDR')
    return ip

def obtener_descripcion_objeto(nombre_objeto):
    """Obtiene descripción y ubicación de un objeto desde la BD"""
    conexion = obtener_conexion_mysql()
    if not conexion:
        return nombre_objeto[0].upper(), 'N/A'
    
    cursor = conexion.cursor()
    try:
        cursor.execute(
            "SELECT descripcion, ubicacion FROM objetos WHERE nombre = %s AND activo = TRUE",
            (nombre_objeto,)
        )
        resultado = cursor.fetchone()
        
        if resultado:
            return resultado[0], resultado[1]
        else:
            # Si no existe, crearlo con valores por defecto
            desc_default = 'CO' if nombre_objeto.lower() == 'computadora' else nombre_objeto[0].upper()
            cursor.execute(
                "INSERT INTO objetos (nombre, descripcion, ubicacion) VALUES (%s, %s, %s)",
                (nombre_objeto, desc_default, 'N/A')
            )
            conexion.commit()
            return desc_default, 'N/A'
            
    except Error as e:
        print(f"Error obteniendo descripción de {nombre_objeto}: {e}")
        return nombre_objeto[0].upper(), 'N/A'
    finally:
        cursor.close()
        conexion.close()

def guardar_consulta_en_bd(objeto1, objeto2, ruta_resultado, tiempo_frontend, 
                          tiempo_backend, tiempo_obj1, tiempo_obj2, tiempo_concat, ip_cliente):
    """Guarda la consulta realizada en la base de datos"""
    conexion = obtener_conexion_mysql()
    if not conexion:
        return
    
    cursor = conexion.cursor()
    try:
        insert_query = """
        INSERT INTO consultas_rutas 
        (objeto_origen, objeto_destino, ruta_resultado, tiempo_frontend, tiempo_backend,
         tiempo_aws_obj1, tiempo_aws_obj2, tiempo_concatenacion, ip_cliente)
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
        """
        
        cursor.execute(insert_query, (
            objeto1, objeto2, ruta_resultado, tiempo_frontend, tiempo_backend,
            tiempo_obj1, tiempo_obj2, tiempo_concat, ip_cliente
        ))
        conexion.commit()
        
    except Error as e:
        print(f"Error guardando consulta: {e}")
    finally:
        cursor.close()
        conexion.close()

def obtener_objetos_json(request):
    """API endpoint para autocompletado de objetos desde base de datos"""
    term = request.GET.get('term', '').lower()
    objetos_lista = []
    
    conexion = obtener_conexion_mysql()
    if conexion:
        cursor = conexion.cursor()
        try:
            if term:
                cursor.execute(
                    "SELECT nombre FROM objetos WHERE nombre LIKE %s AND activo = TRUE ORDER BY nombre LIMIT 10",
                    (f'%{term}%',)
                )
            else:
                cursor.execute(
                    "SELECT nombre FROM objetos WHERE activo = TRUE ORDER BY nombre LIMIT 8"
                )
            
            resultados = cursor.fetchall()
            objetos_lista = [row[0] for row in resultados]
            
        except Error as e:
            print(f"Error obteniendo objetos para autocompletado: {e}")
        finally:
            cursor.close()
            conexion.close()
    
    # Si no hay datos en BD, usar datos por defecto
    if not objetos_lista:
        objetos_todos = ['zapatos', 'caja', 'libro', 'mesa', 'silla', 'computadora', 'telefono', 'reloj']
        if term:
            objetos_lista = [obj for obj in objetos_todos if term in obj.lower()]
        else:
            objetos_lista = objetos_todos[:8]
    
    return JsonResponse(objetos_lista, safe=False)

def obtener_estadisticas_bd():
    """Obtiene estadísticas de consultas desde la base de datos"""
    conexion = obtener_conexion_mysql()
    if not conexion:
        return {}
    
    cursor = conexion.cursor()
    estadisticas = {}
    
    try:
        # Total de consultas
        cursor.execute("SELECT COUNT(*) FROM consultas_rutas")
        estadisticas['total_consultas'] = cursor.fetchone()[0]
        
        # Tiempo promedio backend
        cursor.execute("SELECT AVG(tiempo_backend) FROM consultas_rutas")
        resultado = cursor.fetchone()[0]
        estadisticas['tiempo_promedio_backend'] = round(float(resultado), 2) if resultado else 0
        
        # Consulta más frecuente
        cursor.execute("""
            SELECT ruta_resultado, COUNT(*) as frecuencia 
            FROM consultas_rutas 
            GROUP BY ruta_resultado 
            ORDER BY frecuencia DESC 
            LIMIT 1
        """)
        resultado = cursor.fetchone()
        estadisticas['consulta_mas_frecuente'] = resultado[0] if resultado else 'N/A'
        
        # Consultas del día
        cursor.execute("""
            SELECT COUNT(*) FROM consultas_rutas 
            WHERE DATE(fecha_consulta) = CURDATE()
        """)
        estadisticas['consultas_hoy'] = cursor.fetchone()[0]
        
    except Error as e:
        print(f"Error obteniendo estadísticas: {e}")
    finally:
        cursor.close()
        conexion.close()
    
    return estadisticas

def vista_estadisticas(request):
    """Vista para mostrar estadísticas del sistema"""
    estadisticas = obtener_estadisticas_bd()
    
    # Obtener consultas recientes
    conexion = obtener_conexion_mysql()
    consultas_recientes = []
    
    if conexion:
        cursor = conexion.cursor()
        try:
            cursor.execute("""
                SELECT objeto_origen, objeto_destino, ruta_resultado, 
                       tiempo_backend, fecha_consulta, ip_cliente
                FROM consultas_rutas 
                ORDER BY fecha_consulta DESC 
                LIMIT 10
            """)
            
            resultados = cursor.fetchall()
            for resultado in resultados:
                consultas_recientes.append({
                    'origen': resultado[0],
                    'destino': resultado[1],
                    'ruta': resultado[2],
                    'tiempo': resultado[3],
                    'fecha': resultado[4],
                    'ip': resultado[5]
                })
                
        except Error as e:
            print(f"Error obteniendo consultas recientes: {e}")
        finally:
            cursor.close()
            conexion.close()
    
    context = {
        'estadisticas': estadisticas,
        'consultas_recientes': consultas_recientes
    }
    
    return render(request, 'consultarRutasBodega/estadisticas.html', context)

# Funciones AWS opcionales (mantener por compatibilidad)
def obtener_cliente_aws_academy():
    """
    Configura cliente AWS usando credenciales de AWS Academy (OPCIONAL)
    Si no está configurado, el sistema usará solo la base de datos local
    """
    try:
        import boto3
        import os
        
        # Solo intentar conexión si las credenciales están configuradas
        if not os.environ.get('AWS_ACCESS_KEY_ID'):
            print("AWS no configurado, usando solo base de datos local")
            return None
        
        client = boto3.client(
            'dynamodb',
            region_name='us-east-1',
            aws_access_key_id=os.environ.get('AWS_ACCESS_KEY_ID'),
            aws_secret_access_key=os.environ.get('AWS_SECRET_ACCESS_KEY'),
            aws_session_token=os.environ.get('AWS_SESSION_TOKEN')
        )
        
        # Verificar conexión
        client.list_tables()
        return client
        
    except ImportError:
        print("boto3 no instalado, usando solo base de datos local")
        return None
    except Exception as e:
        print(f"AWS no disponible: {e}")
        return None

def crear_tabla_objetos_academy():
    """Crea la tabla DynamoDB en AWS Academy (OPCIONAL)"""
    client = obtener_cliente_aws_academy()
    if not client:
        return "AWS no configurado, usando solo base de datos local"
    
    try:
        response = client.create_table(
            TableName='objetos-bodega',
            KeySchema=[{'AttributeName': 'objeto', 'KeyType': 'HASH'}],
            AttributeDefinitions=[{'AttributeName': 'objeto', 'AttributeType': 'S'}],
            BillingMode='PAY_PER_REQUEST'
        )
        return f"Tabla AWS creada: {response['TableDescription']['TableName']}"
    except Exception as e:
        return f"Error creando tabla AWS: {e}"

def poblar_tabla_academy():
    """Pobla la tabla DynamoDB con datos de prueba (OPCIONAL)"""
    client = obtener_cliente_aws_academy()
    if not client:
        return "AWS no configurado, datos en base de datos local"
    
    objetos_laboratorio = [
        {'objeto': 'zapatos', 'descripcion': 'Z', 'ubicacion': 'A1-B1'},
        {'objeto': 'caja', 'descripcion': 'C', 'ubicacion': 'A2-B1'},
        {'objeto': 'libro', 'descripcion': 'L', 'ubicacion': 'A3-B1'},
        {'objeto': 'mesa', 'descripcion': 'M', 'ubicacion': 'A4-B1'},
        {'objeto': 'silla', 'descripcion': 'S', 'ubicacion': 'A5-B1'},
        {'objeto': 'computadora', 'descripcion': 'CO', 'ubicacion': 'A6-B1'},
        {'objeto': 'telefono', 'descripcion': 'T', 'ubicacion': 'A7-B1'},
        {'objeto': 'reloj', 'descripcion': 'R', 'ubicacion': 'A8-B1'},
    ]
    
    try:
        for obj in objetos_laboratorio:
            client.put_item(
                TableName='objetos-bodega',
                Item={
                    'objeto': {'S': obj['objeto']},
                    'descripcion': {'S': obj['descripcion']},
                    'ubicacion': {'S': obj['ubicacion']}
                }
            )
        return f"Se poblaron {len(objetos_laboratorio)} objetos en AWS DynamoDB"
    except Exception as e:
        return f"Error poblando AWS: {e}"

def consultar_objeto_aws_academy(nombre_objeto):
    """Consulta un objeto en DynamoDB (OPCIONAL - solo si AWS está configurado)"""
    client = obtener_cliente_aws_academy()
    if not client:
        return {'descripcion': nombre_objeto[0].upper(), 'ubicacion': 'N/A'}
    
    try:
        response = client.get_item(
            TableName='objetos-bodega',
            Key={'objeto': {'S': nombre_objeto}}
        )
        
        if 'Item' in response:
            return {
                'descripcion': response['Item']['descripcion']['S'],
                'ubicacion': response['Item'].get('ubicacion', {}).get('S', 'N/A')
            }
        else:
            return {'descripcion': nombre_objeto[0].upper(), 'ubicacion': 'N/A'}
    except Exception as e:
        print(f"Error consultando AWS {nombre_objeto}: {e}")
        return {'descripcion': nombre_objeto[0].upper(), 'ubicacion': 'N/A'}

def obtener_objetos_aws_academy():
    """Obtiene lista de objetos desde AWS Academy (OPCIONAL)"""
    client = obtener_cliente_aws_academy()
    if not client:
        return []
    
    try:
        response = client.scan(
            TableName='objetos-bodega',
            ProjectionExpression='objeto'
        )
        objetos = [item['objeto']['S'] for item in response.get('Items', [])]
        return objetos
    except Exception as e:
        print(f"Error escaneando AWS tabla: {e}")
        return []
