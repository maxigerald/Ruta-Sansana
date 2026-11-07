import os
import json
from django.conf import settings
from django.contrib.gis.db import models
from django.contrib.gis.geos import LineString, Point

class CategoriaRuta(models.Model):
    nombre = models.CharField(max_length=100, unique=True)

    def __str__(self):
        return self.nombre

class Micro(models.Model):
    numero = models.CharField(max_length=10, unique=True)
    linea_nombre = models.CharField(max_length=100)
    color = models.CharField(max_length=20, default='#003366', help_text="Ej: red, green, blue, yellow, o código HEX (#ff0000)")
    categorias = models.ManyToManyField(CategoriaRuta, related_name='micros')
    recorrido = models.LineStringField(srid=4326, null=True, blank=True)

    def save(self, *args, **kwargs):
        puntos_paraderos = []
        
        # 1. Si no tiene recorrido, buscamos el archivo .geojson en la carpeta
        if not self.recorrido:
            ruta_carpeta = os.path.join(settings.BASE_DIR, 'Rutas de micros')
            ruta_archivo = os.path.join(ruta_carpeta, f'{self.numero}.geojson')
            
            if os.path.exists(ruta_archivo):
                try:
                    with open(ruta_archivo, 'r', encoding='utf-8') as f:
                        geojson_data = json.load(f)
                        
                    for feature in geojson_data.get("features", []):
                        geom_type = feature.get("geometry", {}).get("type")
                        coords = feature.get("geometry", {}).get("coordinates")
                        
                        if geom_type == "LineString":
                            self.recorrido = LineString(coords)
                        elif geom_type == "Point":
                            puntos_paraderos.append(Point(coords))
                            
                except Exception as e:
                    print(f"Error cargando el archivo {self.numero}.geojson: {e}")

        # 2. Guardamos la Micro primero (necesita existir en la base de datos para enlazarle los paraderos)
        super().save(*args, **kwargs)

        # 3. Si encontramos paraderos (puntos), los creamos y vinculamos a esta micro
        if puntos_paraderos:
            for point_geom in puntos_paraderos:
                paradero, created = Paradero.objects.get_or_create(
                    ubicacion=point_geom,
                    defaults={"nombre": f"Paradero {self.numero} (Importado)"}
                )
                paradero.micros.add(self)

    def __str__(self):
        return f"Micro {self.numero}"

class Paradero(models.Model):
    nombre = models.CharField(max_length=150)
    ubicacion = models.PointField(srid=4326, null=True, blank=True)
    micros = models.ManyToManyField(Micro, related_name='paraderos', blank=True)
    
    def __str__(self):
        return self.nombre

class Reporte(models.Model):
    micro = models.ForeignKey(Micro, on_delete=models.CASCADE, related_name='reportes')
    paradero = models.ForeignKey(Paradero, on_delete=models.CASCADE, related_name='reportes')
    nivel_ocupacion = models.IntegerField(help_text="1: Vacío, 2: Medio, 3: Lleno")
    minutos_estimados = models.IntegerField(help_text="Minutos que faltan según el estudiante")
    comentario = models.TextField(blank=True, null=True)
    es_fiable = models.BooleanField(default=True)
    fecha_creacion = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Reporte Micro {self.micro.numero} en {self.paradero.nombre} ({self.fecha_creacion.strftime('%H:%M')})"