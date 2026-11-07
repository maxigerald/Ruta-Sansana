import os
from django.conf import settings
from django.shortcuts import render, get_object_or_404
from django.http import JsonResponse
from django.utils import timezone
from datetime import timedelta

# Importamos todos los modelos
from .models import Micro, CategoriaRuta, Paradero, Reporte

def mapa_micros(request):
    # 1. Obtener parámetros GET
    categoria_id = request.GET.get('categoria')
    micro_id = request.GET.get('micro')
    paradero_id = request.GET.get('paradero')
    ver_todas = request.GET.get('todas')  # Parámetro para listar todas

    # 2. Consultas Base
    categorias = CategoriaRuta.objects.all()
    paraderos = Paradero.objects.all()
    
    # 3. Variables de estado
    micros_filtradas = Micro.objects.none()
    micros_en_paradero = []
    micro_seleccionada = None
    paradero_seleccionado = None
    coords_recorrido = []
    estado_reportes = None

    # 4. Lógica Principal de Filtrado (Categorías o Todas)
    if ver_todas:
        micros_filtradas = Micro.objects.all().order_by('numero')
    elif categoria_id:
        micros_filtradas = Micro.objects.filter(categorias__id=categoria_id)

    # 5. Lógica de Paraderos
    if paradero_id:
        try:
            paradero_seleccionado = Paradero.objects.get(id=paradero_id)
            micros_en_paradero = paradero_seleccionado.micros.all()
            
            # Si estamos viendo "todas", mantenemos la lista de todas y no la reemplazamos por el paradero
            if ver_todas:
                pass
            elif categoria_id:
                micros_coincidentes = micros_filtradas.filter(paraderos=paradero_seleccionado)
                micros_filtradas = micros_coincidentes if micros_coincidentes.exists() else micros_en_paradero
            else:
                micros_filtradas = micros_en_paradero
        except Paradero.DoesNotExist:
            pass

    # 6. Lógica Principal de Micro (Leyendo el LineString exacto de la BD / Supabase)
    if micro_id:
        try:
            micro_seleccionada = Micro.objects.get(id=micro_id)
            if micro_seleccionada.recorrido:
                # Extraemos las coordenadas del campo LineString de PostGIS
                coords_recorrido = list(micro_seleccionada.recorrido.coords)
        except Micro.DoesNotExist:
            pass

    # 7. Lógica de Reportes en Tiempo Real
    if micro_seleccionada and paradero_seleccionado:
        tiempo_limite = timezone.now() - timedelta(minutes=5)
        reportes_activos = Reporte.objects.filter(
            micro=micro_seleccionada,
            paradero=paradero_seleccionado,
            fecha_creacion__gte=tiempo_limite,
            es_fiable=True
        )

        hay_incertidumbre = reportes_activos.count() < 2

        if reportes_activos.exists():
            ocupaciones = [r.nivel_ocupacion for r in reportes_activos]
            promedio_ocupacion = round(sum(ocupaciones) / len(ocupaciones), 1)

            ultimo_reporte = reportes_activos.order_by('-fecha_creacion').first()
            minutos_faltantes = ultimo_reporte.minutos_estimados

            comentarios = [r.comentario for r in reportes_activos if r.comentario]
            alerta = "Precaución: reportes de aglomeración o demora." if any("lenta" in c.lower() or "llena" in c.lower() for c in comentarios) else "Normal"

            estado_reportes = {
                "activo": True,
                "minutos": minutos_faltantes,
                "ocupacion": promedio_ocupacion,
                "alerta": alerta,
                "incertidumbre": hay_incertidumbre,
                "mensaje_incertidumbre": "Pocos reportes recientes; los datos pueden variar." if hay_incertidumbre else ""
            }
        else:
            estado_reportes = {
                "activo": False,
                "mensaje": "No hay reportes recientes para este paradero.",
                "incertidumbre": True
            }

    # 8. Contexto final para la plantilla (Token seguro desde settings)
    context = {
        'categorias': categorias,
        'micros_filtradas': micros_filtradas,
        'categoria_activa': int(categoria_id) if categoria_id else None,
        'coords_recorrido': coords_recorrido,
        'mapbox_token': settings.MAPBOX_TOKEN,
        'paraderos': paraderos,
        'paradero_seleccionado': paradero_seleccionado,
        'micros_en_paradero': micros_en_paradero,
        'micro_seleccionada': micro_seleccionada,
        'estado_reportes': estado_reportes,
        'ver_todas': ver_todas,  # Pasamos la variable a la plantilla
    }
    
    return render(request, 'rutasansana/maps.html', context)


def api_detalle_micro(request, micro_id):
    micro = get_object_or_404(Micro, pk=micro_id)
    return JsonResponse({
        "id": micro.id,
        "numero": micro.numero,
        "linea_nombre": micro.linea_nombre,
        "color": micro.color,
    })