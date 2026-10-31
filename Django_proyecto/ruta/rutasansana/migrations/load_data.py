from django.db import migrations
import json
from django.contrib.gis.geos import fromstr
from pathlib import Path

DATA_FILENAME = 'data.json'

def load_data(apps, schema_editor):
    # Nota: Asegúrate de que el nombre de la app coincida ('rutasansana' en tu caso)
    Shop = apps.get_model('rutasansana', 'Shop')
    jsonfile = Path(__file__).parents[2] / DATA_FILENAME

    with open(str(jsonfile)) as datafile:
        objects = json.load(datafile)
        for obj in objects['elements']:
            try:
                objType = obj['type']
                if objType == 'node':
                    tags = obj['tags']
                    name = tags.get('name', 'no-name')
                    longitude = obj.get('lon', 0)
                    latitude = obj.get('lat', 0)
                    location = fromstr(f'POINT({longitude} {latitude})', srid=4326)
                    Shop(name=name, location=location).save()
            except KeyError:
                pass     

class Migration(migrations.Migration):

    dependencies = [
        ('rutasansana', '0001_initial'),  # Cambia por la dependencia real previa si es distinta
    ]

    operations = [
        migrations.RunPython(load_data),
    ]