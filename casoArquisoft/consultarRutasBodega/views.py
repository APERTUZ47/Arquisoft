from django.shortcuts import render
from django.http import HttpResponse


def index(request):
    """Vista principal para consultar rutas de bodega"""
    return render(request, 'consultarRutasBodega/index.html', {
        'titulo': 'Consultar Rutas de Bodega',
        'mensaje': 'Bienvenido al sistema de consulta de rutas de bodega'
    })

def consultar_rutas(request):
    """Vista para mostrar las rutas disponibles"""
    # Obtener objetos desde AWS Academy con fallback
    try:
        objetos_aws = obtener_objetos_aws_academy()
        objetos_ejemplo = []
        
        for i, obj in enumerate(objetos_aws, 1):
            # Consultar información completa desde AWS
            info_obj = consultar_objeto_aws_academy(obj)
            objetos_ejemplo.append({
                'id': i,
                'objeto': obj,
                'descripcion': info_obj['descripcion']
            })
            
    except Exception as e:
        print(f"Error consultando AWS Academy: {e}")
        # Fallback a datos locales si AWS no está disponible
        objetos_ejemplo = [
            {'id': 1, 'objeto': 'zapatos', 'descripcion': 'Z'},
            {'id': 2, 'objeto': 'caja', 'descripcion': 'C'},
            {'id': 3, 'objeto': 'libro', 'descripcion': 'L'},
            {'id': 4, 'objeto': 'mesa', 'descripcion': 'M'},
            {'id': 5, 'objeto': 'silla', 'descripcion': 'S'},
            {'id': 6, 'objeto': 'computadora', 'descripcion': 'CO'},
            {'id': 7, 'objeto': 'telefono', 'descripcion': 'T'},
            {'id': 8, 'objeto': 'reloj', 'descripcion': 'R'},
        ]
    
    return render(request, 'consultarRutasBodega/rutas.html', {
        'objetos': objetos_ejemplo
    })

def buscar_ruta(request):
    """Vista para buscar ruta entre objetos"""
    if request.method == 'POST':
        import time
        from datetime import datetime
        
        # Registrar tiempo de inicio del procesamiento
        inicio_backend = time.time()
        timestamp_inicio = datetime.now()
        
        objeto1 = request.POST.get('objeto1')
        objeto2 = request.POST.get('objeto2')
        
        # Obtener tiempo del frontend si se envió
        tiempo_frontend = request.POST.get('tiempo_frontend', '0')
        
        # TODO: Aquí se harán las peticiones a AWS
        # ruta_resultado = consultar_aws(objeto1, objeto2)
        
        # Simular algo de procesamiento
        time.sleep(0.1)  # Simula 100ms de procesamiento
        
        # Por ahora simulamos la lógica
        ruta_simulada = simular_busqueda_ruta(objeto1, objeto2)
        
        # Calcular tiempo total de procesamiento en backend
        fin_backend = time.time()
        tiempo_backend = round((fin_backend - inicio_backend) * 1000, 2)
        
        # Calcular diferencia de tiempo para el análisis
        tiempo_frontend_float = float(tiempo_frontend) if tiempo_frontend != '0' else None
        diferencia_tiempo = None
        if tiempo_frontend_float and tiempo_frontend_float > tiempo_backend:
            diferencia_tiempo = round(tiempo_frontend_float - tiempo_backend, 2)
        
        # Calcular tiempos simulados para AWS (40% del tiempo backend cada consulta)
        tiempo_get_objeto1 = round(tiempo_backend * 0.4, 1)
        tiempo_get_objeto2 = round(tiempo_backend * 0.4, 1)
        tiempo_concatenacion = round(tiempo_backend * 0.2, 1)
        
        return render(request, 'consultarRutasBodega/resultado_ruta.html', {
            'objeto1': objeto1,
            'objeto2': objeto2,
            'ruta': ruta_simulada,
            'tiempo_frontend': tiempo_frontend_float,
            'tiempo_backend': tiempo_backend,
            'diferencia_tiempo': diferencia_tiempo,
            'tiempo_get_objeto1': tiempo_get_objeto1,
            'tiempo_get_objeto2': tiempo_get_objeto2,
            'tiempo_concatenacion': tiempo_concatenacion,
            'timestamp_inicio': timestamp_inicio.strftime('%H:%M:%S.%f')[:-3],
            'timestamp_fin': datetime.now().strftime('%H:%M:%S.%f')[:-3]
        })
    
    return render(request, 'consultarRutasBodega/buscar_ruta.html')

def obtener_objetos_json(request):
    """API endpoint para autocompletado de objetos"""
    import json
    from django.http import JsonResponse
    
    # Obtener objetos desde AWS Academy
    objetos_lista = obtener_objetos_aws_academy()
    
    term = request.GET.get('term', '').lower()
    if term:
        # Filtrar objetos que coincidan con el término de búsqueda
        objetos_filtrados = [obj for obj in objetos_lista if term in obj.lower()]
    else:
        objetos_filtrados = objetos_lista[:8]  # Mostrar solo 8 por defecto
    
    return JsonResponse(objetos_filtrados, safe=False)

def simular_busqueda_ruta(objeto1, objeto2):
    """Simula la búsqueda de ruta consultando AWS dinámicamente"""
    # TODO: Aquí se harían las consultas reales a AWS
    # response1 = consultar_aws_objeto(objeto1)
    # response2 = consultar_aws_objeto(objeto2)
    # desc1 = response1['descripcion']
    # desc2 = response2['descripcion']
    
    # Por ahora simulamos que consultamos AWS y obtenemos las descripciones
    # Usamos la primera letra en mayúscula como simulación simple
    desc1 = objeto1[0].upper() if objeto1 else '?'
    desc2 = objeto2[0].upper() if objeto2 else '?'
    
    # Si es computadora, usar "CO" para que sea más realista
    if objeto1.lower() == 'computadora':
        desc1 = 'CO'
    if objeto2.lower() == 'computadora':
        desc2 = 'CO'
    
    return f"{desc1}-{desc2}"

# Configuración para AWS Academy/School
def obtener_cliente_aws_academy():
    """
    Configura cliente AWS usando credenciales de AWS Academy
    Las credenciales temporales se obtienen del AWS Details en el laboratorio
    """
    try:
        import boto3
        import os
        
        # Opción 1: Variables de entorno (recomendado para AWS Academy)
        # Copiar desde AWS Details -> AWS CLI:
        # export AWS_ACCESS_KEY_ID=...
        # export AWS_SECRET_ACCESS_KEY=...
        # export AWS_SESSION_TOKEN=...
        
        client = boto3.client(
            'dynamodb',
            region_name='us-east-1',  # AWS Academy normalmente usa us-east-1
            aws_access_key_id=os.environ.get('AWS_ACCESS_KEY_ID'),
            aws_secret_access_key=os.environ.get('AWS_SECRET_ACCESS_KEY'),
            aws_session_token=os.environ.get('AWS_SESSION_TOKEN')  # Importante para Academy
        )
        
        # Verificar conexión
        client.list_tables()
        return client
        
    except ImportError:
        print("boto3 no instalado. Ejecutar: pip install boto3")
        return None
    except Exception as e:
        print(f"Error conectando AWS Academy: {e}")
        print("Verifica que las credenciales estén configuradas correctamente")
        return None

def crear_tabla_objetos_academy():
    """
    Crea la tabla DynamoDB en AWS Academy (ejecutar una sola vez)
    """
    client = obtener_cliente_aws_academy()
    if not client:
        return "Error: No se pudo conectar a AWS"
    
    try:
        # Crear tabla con configuración mínima para Academy
        response = client.create_table(
            TableName='objetos-bodega',
            KeySchema=[
                {
                    'AttributeName': 'objeto',
                    'KeyType': 'HASH'  # Clave de partición
                }
            ],
            AttributeDefinitions=[
                {
                    'AttributeName': 'objeto',
                    'AttributeType': 'S'  # String
                }
            ],
            # Configuración básica para laboratorio
            BillingMode='PAY_PER_REQUEST'  # Sin configurar capacidad
        )
        
        return f"Tabla creada: {response['TableDescription']['TableName']}"
        
    except client.exceptions.ResourceInUseException:
        return "La tabla ya existe"
    except Exception as e:
        return f"Error creando tabla: {e}"

def poblar_tabla_academy():
    """
    Pobla la tabla con datos de prueba para el laboratorio
    """
    client = obtener_cliente_aws_academy()
    if not client:
        return "Error: No se pudo conectar a AWS"
    
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
        
        return f"Se poblaron {len(objetos_laboratorio)} objetos en AWS Academy"
        
    except Exception as e:
        return f"Error poblando tabla: {e}"

def consultar_objeto_aws_academy(nombre_objeto):
    """Consulta un objeto en DynamoDB de AWS Academy"""
    client = obtener_cliente_aws_academy()
    if not client:
        # Fallback si no hay conexión
        return {'descripcion': nombre_objeto[0].upper()}
    
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
            return {'descripcion': nombre_objeto[0].upper()}
            
    except Exception as e:
        print(f"Error consultando {nombre_objeto}: {e}")
        return {'descripcion': nombre_objeto[0].upper()}

def obtener_objetos_aws_academy():
    """Obtiene lista de objetos desde AWS Academy"""
    client = obtener_cliente_aws_academy()
    if not client:
        # Fallback para desarrollo local
        return ['zapatos', 'caja', 'libro', 'mesa', 'silla', 'computadora', 'telefono', 'reloj']
    
    try:
        response = client.scan(
            TableName='objetos-bodega',
            ProjectionExpression='objeto'
        )
        
        objetos = [item['objeto']['S'] for item in response.get('Items', [])]
        return objetos if objetos else ['zapatos', 'caja', 'libro']
        
    except Exception as e:
        print(f"Error escaneando tabla: {e}")
        return ['zapatos', 'caja', 'libro', 'mesa', 'silla', 'computadora']

def consultar_aws(objeto1, objeto2):
    """
    Función principal para consultar AWS Academy
    """
    info_obj1 = consultar_objeto_aws_academy(objeto1)
    info_obj2 = consultar_objeto_aws_academy(objeto2)
    
    desc1 = info_obj1['descripcion']
    desc2 = info_obj2['descripcion']
    
    return f"{desc1}-{desc2}"
