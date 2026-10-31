from django.contrib.gis.db import models

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