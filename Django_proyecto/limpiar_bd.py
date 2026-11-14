import os
import sys
import django

# 1. Configuración del entorno Django
BASE_DIR = os.path.dirname(os.path.abspath(__file__))

for root, dirs, files in os.walk(BASE_DIR):
    if 'settings.py' in files and 'venv' not in root:
        parent_dir = os.path.dirname(root)
        if root not in sys.path:
            sys.path.insert(0, root)
        if parent_dir not in sys.path:
            sys.path.insert(0, parent_dir)
        if BASE_DIR not in sys.path:
            sys.path.insert(0, BASE_DIR)
        
        folder_name = os.path.basename(root)
        os.environ.setdefault('DJANGO_SETTINGS_MODULE', f'{folder_name}.settings')
        break

django.setup()

from django.apps import apps
from django.db import transaction

def obtener_modelo(nombre_modelo):
    for model in apps.get_models():
        if model.__name__.lower() == nombre_modelo.lower():
            return model
    raise LookupError(f"No se encontró el modelo '{nombre_modelo}'.")

Micro = obtener_modelo('Micro')
Paradero = obtener_modelo('Paradero')

with transaction.atomic():
    print("🧹 Limpiando trazados y desvinculando paraderos en Micros...", flush=True)
    for micro in Micro.objects.all():
        if hasattr(micro, 'recorrido'):
            micro.recorrido = None
        if hasattr(micro, 'geometria'):
            micro.geometria = None
        if hasattr(micro, 'paraderos'):
            micro.paraderos.clear()
        micro.save()

    # Conservar únicamente los paraderos originales de la zona USM
    paraderos_usm = [
        "Paradero Placeres - Manuel Antonio",
        "Paradero Placeres - San Luis",
        "Paradero USM Av. España",
    ]

    print("🧹 Eliminando paraderos automáticos fuera de zona...", flush=True)
    borrados, _ = Paradero.objects.exclude(nombre__in=paraderos_usm).delete()
    print(f"   ✅ Se eliminaron {borrados} paraderos de la base de datos.", flush=True)

print("✨ Purgado completo. El mapa ha vuelto a su estado original.", flush=True)