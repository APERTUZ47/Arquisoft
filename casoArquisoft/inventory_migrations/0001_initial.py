# Generated migration for inventory microservice
from django.db import migrations, models

class Migration(migrations.Migration):

    initial = True

    dependencies = []

    operations = [
        # Nota: Las tablas se crean directamente en la base de datos
        # usando el script SQL setup_inventory_db.sql
        # Esta migración es solo para registro en Django
        migrations.RunSQL(
            "SELECT 1;",  # No-op SQL
            reverse_sql="SELECT 1;",
        ),
    ]
