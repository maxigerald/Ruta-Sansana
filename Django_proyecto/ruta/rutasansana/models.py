from django.contrib.gis.db import models

class CategoriaRuta(models.Model):
    #Recorridos
    nombre = models.CharField(max_length=100, unique=True)

    def __str__(self):
        return self.nombre

class Micro(models.Model):
    numero = models.CharField(max_length=10, unique=True)  # Ej: "401", "214", etc.
    linea_nombre = models.CharField(max_length=100)        # Ej: "Lineas Gran Valparaíso"
    
    #Una micro puede estar en muchas categorías
    categorias = models.ManyToManyField(CategoriaRuta, related_name='micros')
    
    #Recorrido en formato vectorial (Línea geográfica de la ruta)
    recorrido = models.LineStringField(srid=4326, null=True, blank=True)

    def __str__(self):
        return f"Micro {self.numero}"