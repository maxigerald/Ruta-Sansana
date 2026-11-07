from django.db import models
from django.utils import timezone


class ReporteEstado(models.Model):
    """
    Reporte rápido de un estudiante sobre una micro: qué tan llena va, si el
    micrero realmente paró y la condición física del vehículo.
    Complementa (no reemplaza) al modelo Reporte de rutasansana.
    """
    class Ocupacion(models.IntegerChoices):  # misma escala 1-3 que rutasansana.Reporte
        VACIA = 1, "Vacía"
        MEDIA = 2, "Media"
        LLENA = 3, "Llena"

    class Parada(models.TextChoices):
        PARO = "paro", "Paró"
        NO_PARO = "no_paro", "No paró"
        SIN_DATO = "sin_dato", "Sin dato"

    class EstadoFisico(models.IntegerChoices):
        SIN_DATO = 0, "Sin dato"
        PESIMO = 1, "Pésimo"
        MALO = 2, "Malo"
        REGULAR = 3, "Regular"
        BUENO = 4, "Bueno"
        EXCELENTE = 5, "Excelente"

    micro = models.ForeignKey("rutasansana.Micro", on_delete=models.CASCADE, related_name="reportes_estado")
    paradero = models.ForeignKey("rutasansana.Paradero", null=True, blank=True,
                                 on_delete=models.SET_NULL, related_name="reportes_estado")
    ocupacion = models.PositiveSmallIntegerField(choices=Ocupacion.choices)
    parada = models.CharField(max_length=10, choices=Parada.choices, default=Parada.SIN_DATO)
    estado_fisico = models.SmallIntegerField(choices=EstadoFisico.choices, default=EstadoFisico.SIN_DATO)
    sesion = models.CharField(max_length=40, blank=True, db_index=True,
                              help_text="Clave de sesión anónima, solo para limitar spam")
    creado = models.DateTimeField(auto_now_add=True, db_index=True)

    class Meta:
        ordering = ["-creado"]

    def __str__(self):
        return f"Micro {self.micro.numero}: {self.get_ocupacion_display()} / {self.get_parada_display()}"


class Alerta(models.Model):
    """
    Aviso importante. Si no se indica micro ni categoría, es una alerta general
    y le llega a todos los chats.
    """
    class Severidad(models.TextChoices):
        INFO = "info", "Informativa"
        ADVERTENCIA = "warn", "Advertencia"
        CRITICA = "crit", "Crítica"

    micro = models.ForeignKey("rutasansana.Micro", null=True, blank=True,
                              on_delete=models.CASCADE, related_name="alertas")
    categoria = models.ForeignKey("rutasansana.CategoriaRuta", null=True, blank=True,
                                  on_delete=models.CASCADE, related_name="alertas")
    titulo = models.CharField(max_length=120)
    mensaje = models.TextField(blank=True)
    severidad = models.CharField(max_length=5, choices=Severidad.choices, default=Severidad.INFO)
    activa = models.BooleanField(default=True)
    expira_en = models.DateTimeField(null=True, blank=True)
    automatica = models.BooleanField(default=False, help_text="Generada por el sistema a partir de reportes")
    creado = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-creado"]

    def __str__(self):
        return f"[{self.get_severidad_display()}] {self.titulo}"

    @property
    def vigente(self):
        return self.activa and (self.expira_en is None or self.expira_en > timezone.now())

    def ids_categorias_destino(self):
        """IDs de las categorías (salas de chat) a las que debe llegar esta alerta."""
        from rutasansana.models import CategoriaRuta
        if self.micro_id:
            return list(self.micro.categorias.values_list("id", flat=True))
        if self.categoria_id:
            return [self.categoria_id]
        return list(CategoriaRuta.objects.values_list("id", flat=True))


class MensajeChat(models.Model):
    """Mensaje del chat de difusión de un tipo de micro (CategoriaRuta)."""
    categoria = models.ForeignKey("rutasansana.CategoriaRuta", on_delete=models.CASCADE, related_name="mensajes_chat")
    alias = models.CharField(max_length=20, default="Anónimo")
    texto = models.CharField(max_length=300)
    creado = models.DateTimeField(auto_now_add=True, db_index=True)

    class Meta:
        ordering = ["creado"]

    def __str__(self):
        return f"{self.alias}: {self.texto[:30]}"