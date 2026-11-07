from django.contrib import admin
from django.forms import Textarea
from django.contrib.gis.db import models as gis_models
from .models import CategoriaRuta, Micro, Paradero, Reporte

@admin.register(Micro)
class MicroAdmin(admin.ModelAdmin):
    list_display = ('numero', 'linea_nombre', 'color')
    search_fields = ('numero', 'linea_nombre')
    filter_horizontal = ('categorias', 'paraderos')
    formfield_overrides = {
        gis_models.LineStringField: {'widget': Textarea(attrs={'rows': 5, 'cols': 50})},
    }

    def save_related(self, request, form, formsets, change):
        # 1. Primero guardamos la relación de la micro con sus paraderos elegidos
        super().save_related(request, form, formsets, change)
        
        # 2. Obtenemos la micro que acabamos de guardar
        micro = form.instance
        nombres_paraderos = [p.nombre for p in micro.paraderos.all()]
        
        nuevo_color = micro.color # Mantiene el color actual por defecto
        
        # 3. Asignamos el color fijo de la micro según el paradero vinculado
        for nombre in nombres_paraderos:
            if 'España' in nombre:
                nuevo_color = '#1d4ed8'  # <--- Azul más oscuro
                break
            elif 'Manuel Antonio' in nombre:
                nuevo_color = '#16a34a'  # Verde
                break
            elif 'San Luis' in nombre:
                nuevo_color = '#dc2626'  # Rojo
                break
                
        # 4. Si el color detectado es distinto, lo sobrescribimos en la base de datos
        if micro.color != nuevo_color:
            micro.color = nuevo_color
            micro.save(update_fields=['color'])

@admin.register(CategoriaRuta)
class CategoriaRutaAdmin(admin.ModelAdmin):
    list_display = ('nombre',)
    search_fields = ('nombre',)

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