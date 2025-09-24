# Configuración AWS Academy para Django

## 1. Instalación de dependencias

```bash
# Activar entorno virtual
.\env\Scripts\Activate.ps1

# Instalar boto3 (SDK de AWS para Python)
pip install boto3
```

## 2. Obtener credenciales de AWS Academy

1. **Iniciar laboratorio** en AWS Academy
2. **Hacer clic en "AWS Details"**
3. **Copiar las credenciales**:
   - AWS CLI: 
     ```
     export AWS_ACCESS_KEY_ID=ASIA...
     export AWS_SECRET_ACCESS_KEY=...
     export AWS_SESSION_TOKEN=...
     ```

## 3. Configurar credenciales en Windows

### Opción A: Variables de entorno (PowerShell)
```powershell
$env:AWS_ACCESS_KEY_ID="ASIA..."
$env:AWS_SECRET_ACCESS_KEY="..."
$env:AWS_SESSION_TOKEN="..."
```

### Opción B: Archivo de credenciales
Crear archivo: `C:\Users\TuUsuario\.aws\credentials`
```ini
[default]
aws_access_key_id = ASIA...
aws_secret_access_key = ...
aws_session_token = ...
```

## 4. Configurar la tabla DynamoDB

### 4.1 Crear tabla (ejecutar una vez)
En Django shell:
```python
# Ejecutar en manage.py shell
python manage.py shell

# Importar función
from consultarRutasBodega.views import crear_tabla_objetos_academy

# Crear tabla
resultado = crear_tabla_objetos_academy()
print(resultado)
```

### 4.2 Poblar tabla con datos de prueba
```python
# En el mismo shell
from consultarRutasBodega.views import poblar_tabla_academy

# Poblar datos
resultado = poblar_tabla_academy()
print(resultado)
```

## 5. Verificar funcionamiento

### Probar conexión:
```python
# En manage.py shell
from consultarRutasBodega.views import obtener_cliente_aws_academy

client = obtener_cliente_aws_academy()
if client:
    print("✅ Conexión exitosa a AWS Academy")
    # Listar tablas
    tables = client.list_tables()
    print("Tablas disponibles:", tables['TableNames'])
else:
    print("❌ Error de conexión")
```

### Probar consulta:
```python
from consultarRutasBodega.views import consultar_objeto_aws_academy

# Consultar un objeto
resultado = consultar_objeto_aws_academy('zapatos')
print("Resultado:", resultado)
```

## 6. Uso en la aplicación

Una vez configurado todo:
1. **Ejecutar servidor**: `python manage.py runserver`
2. **Ir a**: http://127.0.0.1:8000/buscar/
3. **Probar autocompletado**: Escribir nombres de objetos
4. **Realizar búsqueda**: Seleccionar dos objetos y buscar ruta

## 7. Troubleshooting

### Error: "boto3 not found"
```bash
pip install boto3
```

### Error: "Unable to locate credentials"
- Verificar que las variables de entorno estén configuradas
- Las credenciales de AWS Academy expiran cada 4 horas
- Renovar credenciales desde AWS Details

### Error: "Table does not exist"
- Ejecutar `crear_tabla_objetos_academy()` primero
- Verificar que estés en la región us-east-1

### Error: "Access Denied"
- Verificar que el laboratorio esté iniciado
- Las credenciales pueden haber expirado
- Copiar nuevas credenciales desde AWS Details

## 8. Comandos útiles

### Resetear tabla (si es necesario):
```python
# En manage.py shell
import boto3
client = boto3.client('dynamodb', region_name='us-east-1')

# Eliminar tabla
client.delete_table(TableName='objetos-bodega')

# Esperar y recrear
# ... ejecutar crear_tabla_objetos_academy() de nuevo
```

### Ver todos los objetos:
```python
from consultarRutasBodega.views import obtener_objetos_aws_academy
objetos = obtener_objetos_aws_academy()
print("Objetos disponibles:", objetos)
```

## Notas importantes:
- **Las credenciales de AWS Academy expiran cada 4 horas**
- **Siempre iniciar el laboratorio antes de usar la aplicación**
- **La tabla DynamoDB solo existe mientras el laboratorio esté activo**
- **Los datos se conservan durante la sesión del laboratorio**