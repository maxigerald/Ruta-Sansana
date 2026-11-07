from django.contrib import admin

from .models import Alerta, MensajeChat, ReporteEstado


@admin.register(Alerta)
class AlertaAdmin(admin.ModelAdmin):
    list_display = ("titulo", "micro", "categoria", "severidad", "activa", "automatica", "expira_en", "creado")
    list_filter = ("severidad", "activa", "automatica")
    search_fields = ("titulo", "mensaje")


@admin.register(ReporteEstado)
class ReporteEstadoAdmin(admin.ModelAdmin):
    list_display = ("micro", "paradero", "ocupacion", "parada", "creado")
    list_filter = ("parada", "ocupacion", "creado")


@admin.register(MensajeChat)
class MensajeChatAdmin(admin.ModelAdmin):
    list_display = ("categoria", "alias", "texto", "creado")
    list_filter = ("categoria",)
