import os
import json
from django.conf import settings
from django.contrib.gis.db import models
from django.contrib.gis.geos import LineString, Point


class CategoriaRuta(models.Model):
    nombre = models.CharField(max_length=100, unique=True)

    def __str__(self):
        return self.nombre


class Paradero(models.Model):
    nombre = models.CharField(max_length=150)
    ubicacion = models.PointField(srid=4326, null=True, blank=True)
    color = models.CharField(max_length=50, default="#0284c7")  # Color propio del Paradero

    def __str__(self):
        return self.nombre


class Micro(models.Model):
    numero = models.IntegerField()
    linea_nombre = models.CharField(max_length=100)
    color = models.CharField(max_length=50, default="#003366")
    categorias = models.ManyToManyField('CategoriaRuta', related_name='micros', blank=True)
    paraderos = models.ManyToManyField(Paradero, related_name='micros', blank=True)
    recorrido = models.LineStringField(srid=4326, null=True, blank=True)

    def __str__(self):
        return f"Micro {self.numero} - {self.linea_nombre}"

    @property
    def paraderos_colors_gradient(self):
        """Calcula un gradiente CSS con n divisiones iguales para los colores de los paraderos asociados."""
        paraderos_list = list(self.paraderos.all())
        n = len(paraderos_list)
        
        # Si no tiene paraderos, usa el color por defecto de la micro
        if n == 0:
            return self.color or "#003366"
        # Si tiene solo 1 paradero, devuelve color sólido
        if n == 1:
            return paraderos_list[0].color or "#0284c7"
        
        # Si tiene N paraderos, dividimos el 100% en n partes iguales con cortes precisos
        step = 100.0 / n
        stops = []
        for i, p in enumerate(paraderos_list):
            c = p.color or "#0284c7"
            start = i * step
            end = (i + 1) * step
            stops.append(f"{c} {start:.2f}%, {c} {end:.2f}%")
        
        return f"linear-gradient(to right, {', '.join(stops)})"

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

        # 2. Guardamos la Micro primero
        super().save(*args, **kwargs)

        # 3. Si encontramos paraderos (puntos), los creamos y vinculamos a esta micro
        if puntos_paraderos:
            for point_geom in puntos_paraderos:
                paradero, created = Paradero.objects.get_or_create(
                    ubicacion=point_geom,
                    defaults={"nombre": f"Paradero {self.numero} (Importado)"}
                )
                self.paraderos.add(paradero)


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