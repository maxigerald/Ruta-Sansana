from django.contrib import admin
from django.forms import Textarea
from django.contrib.gis.db import models as gis_models
from .models import CategoriaRuta, Micro, Paradero, Reporte

@admin.register(Micro)
class MicroAdmin(admin.ModelAdmin):
    formfield_overrides = {
        gis_models.LineStringField: {'widget': Textarea(attrs={'rows': 5, 'cols': 50})},
    }

@admin.register(CategoriaRuta)
class CategoriaRutaAdmin(admin.ModelAdmin):
    pass

@admin.register(Paradero)
class ParaderoAdmin(admin.ModelAdmin):
    list_display = ('nombre',)
    search_fields = ('nombre',)
    formfield_overrides = {
        gis_models.PointField: {'widget': Textarea(attrs={'rows': 2, 'cols': 40})},
    }

@admin.register(Reporte)
class ReporteAdmin(admin.ModelAdmin):
    list_display = ('micro', 'paradero', 'nivel_ocupacion', 'minutos_estimados', 'es_fiable', 'fecha_creacion')
    list_filter = ('es_fiable', 'fecha_creacion')