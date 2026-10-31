from django.contrib import admin
from django.forms import Textarea
from django.contrib.gis.db import models as gis_models
from .models import CategoriaRuta, Micro

@admin.register(Micro)
class MicroAdmin(admin.ModelAdmin):  # Cambiamos GISModelAdmin por admin.ModelAdmin normal
    formfield_overrides = {
        gis_models.LineStringField: {'widget': Textarea(attrs={'rows': 5, 'cols': 50})},
    }

@admin.register(CategoriaRuta)
class CategoriaRutaAdmin(admin.ModelAdmin):
    pass

"""from django.contrib import admin
from django.contrib.gis.admin import GISModelAdmin
from .models import CategoriaRuta, Micro

@admin.register(Micro)
class MicroAdmin(GISModelAdmin):
    pass  # Usa el mapa interactivo nativo de GeoDjango sin forzar widgets de texto

@admin.register(CategoriaRuta)
class CategoriaRutaAdmin(admin.ModelAdmin):
    pass"""