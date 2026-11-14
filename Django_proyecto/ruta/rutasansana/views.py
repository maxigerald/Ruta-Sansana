import os
from django.conf import settings
from django.shortcuts import render, get_object_or_404
from django.http import JsonResponse
from django.utils import timezone
from datetime import timedelta

# Importamos los modelos
from .models import Micro, CategoriaRuta, Paradero, Reporte

def mapa_micros(request):
    # 1. Obtener parámetros GET
    categoria_id = request.GET.get('categoria')
    micro_id = request.GET.get('micro')
    paradero_id = request.GET.get('paradero')
    ver_todas = request.GET.get('todas')

    # 2. Consultas Base
    categorias = CategoriaRuta.objects.all()
    paraderos = Paradero.objects.all()
    
    # 3. Variables de estado por defecto
    micros_en_paradero = []
    micro_seleccionada = None
    paradero_seleccionado = None
    coords_recorrido = []
    estado_reportes = None

    # 4. Lógica de Filtrado de Micros
    if ver_todas:
        micros_filtradas = Micro.objects.all().order_by('numero')
    elif categoria_id:
        micros_filtradas = Micro.objects.filter(categorias__id=categoria_id).order_by('numero')
    else:
        micros_filtradas = Micro.objects.all().order_by('numero')

    # 5. Lógica de Paraderos
    if paradero_id:
        try:
            paradero_seleccionado = Paradero.objects.get(id=paradero_id)
            micros_en_paradero = paradero_seleccionado.micros.all()
            micros_filtradas = micros_en_paradero
            ver_todas = None 
        except Paradero.DoesNotExist:
            pass

    # 6. Selección de Micro
    if micro_id:
        try:
            micro_seleccionada = Micro.objects.get(id=micro_id)
        except (Micro.DoesNotExist, ValueError):
            micro_seleccionada = None

    # Si no se especificó o no se encontró la micro pedida, tomar la primera de la lista o la primera de la BD
    if not micro_seleccionada:
        micro_seleccionada = micros_filtradas.first() or Micro.objects.first()

    # 🛡️ OBJETO DE RESPALDO (Si no hay micros en la base de datos)
    if not micro_seleccionada:
        class DummyMicro:
            id = 0
            numero = 'N/A'
            linea_nombre = 'Sin micros'
            color = '#10b981'
            recorrido = None
        micro_seleccionada = DummyMicro()

    # Extraer coordenadas si la micro posee LineString en PostGIS
    if hasattr(micro_seleccionada, 'recorrido') and micro_seleccionada.recorrido:
        coords_recorrido = list(micro_seleccionada.recorrido.coords)

    # 7. Lógica de Reportes
    if isinstance(micro_seleccionada, Micro) and paradero_seleccionado:
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

    # 8. Contexto final enviado a la plantilla
    context = {
        'categorias': categorias,
        'micros_filtradas': micros_filtradas,
        'categoria_activa': int(categoria_id) if categoria_id and categoria_id.isdigit() else None,
        'coords_recorrido': coords_recorrido,
        'mapbox_token': getattr(settings, 'MAPBOX_TOKEN', ''),
        'paraderos': paraderos,
        'paradero_seleccionado': paradero_seleccionado,
        'micros_en_paradero': micros_en_paradero,
        'micro_seleccionada': micro_seleccionada,
        'estado_reportes': estado_reportes,
        'ver_todas': ver_todas,
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