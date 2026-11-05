import os
import django
import json

# Configurar el entorno de Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'ruta.settings')
django.setup()

# Importamos todos los modelos necesarios
from rutasansana.models import Micro, CategoriaRuta, Paradero
from django.contrib.gis.geos import LineString, Point

archivo_path = 'Rutas de micros/505.geojson'

if not os.path.exists(archivo_path):
    print(f"Error: No se encuentra el archivo {archivo_path}.")
else:
    with open(archivo_path, 'r', encoding='utf-8') as f:
        geojson_data = json.load(f)

    # 1. Buscamos (o creamos) la categoría para no tener que hacerla a mano
    categoria_usm, _ = CategoriaRuta.objects.get_or_create(nombre="Viña del Mar - USM")

    for feature in geojson_data.get("features", []):
        geom_type = feature["geometry"]["type"]
        coords = feature["geometry"]["coordinates"]
        
        if geom_type == "LineString":
            line_geom = LineString(coords)
            
            # 2. Usamos update_or_create para que si ya existe la 505, la actualice y NO explote
            micro, created = Micro.objects.update_or_create(
                numero="505",
                defaults={
                    "linea_nombre": "Nueva Aurora - Playa Ancha",
                    "recorrido": line_geom,
                    "color": "#003366"  # Color por defecto según tu modelo
                }
            )
            
            # 3. Le asignamos la categoría a la micro
            micro.categorias.add(categoria_usm)
            
            accion = "creada" if created else "actualizada"
            print(f"Línea de la micro 505 {accion} con éxito.")
            
        elif geom_type == "Point":
            point_geom = Point(coords)
            
            # 4. Guardamos el punto como Paradero
            paradero, created = Paradero.objects.update_or_create(
                ubicacion=point_geom,
                defaults={
                    "nombre": "Paradero Micro 505 (Importado)"
                }
            )
            print("Paradero guardado con éxito.")

    print("¡Proceso de importación completado al 100%!")