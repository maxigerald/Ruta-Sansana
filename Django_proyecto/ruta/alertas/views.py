from datetime import timedelta
from django.conf import settings
from django.core import serializers
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, render
from django.utils import timezone
from django.views.decorators.http import require_GET, require_POST

from rutasansana.models import CategoriaRuta, Micro, Paradero
from alertas.models import ReporteEstado
from alertas.services import alertas_activas, estado_micro, evaluar_no_para, serializar_alerta

COOLDOWN_MIN = 3

@require_GET
def indice(request):
    categorias = CategoriaRuta.objects.all()
    
    micros_data = []
    for m in Micro.objects.all():
        cat = m.categorias.first()
        micros_data.append({
            "id": m.id,
            "numero": str(m.numero),
            "linea": m.linea_nombre,
            "color": getattr(m, 'color', '#003366'),
            "categoria_id": cat.id if cat else 1
        })

    paraderos_data = []
    for p in Paradero.objects.all():
        paraderos_data.append({
            "id": p.id,
            "nombre": p.nombre
        })

    return render(request, "alertas/index.html", {
        "categorias": categorias,
        "micros_json": micros_data,
        "paraderos_json": paraderos_data,
        "alertas": alertas_activas(),
    })

@require_GET
def mapa_micros(request):
    categoria_id = request.GET.get("categoria")
    micro_id = request.GET.get("micro")
    paradero_id = request.GET.get("paradero")
    ver_todas = request.GET.get("todas") == "true"

    categorias = CategoriaRuta.objects.all()
    paraderos = Paradero.objects.all().order_by('nombre')
    
    micros_filtradas = Micro.objects.none()
    if ver_todas:
        micros_filtradas = Micro.objects.all().order_by('numero')
    elif categoria_id:
        cat = CategoriaRuta.objects.filter(pk=categoria_id).first()
        if cat:
            micros_filtradas = cat.micros.all().order_by('numero')
    elif paradero_id:
        par = Paradero.objects.filter(pk=paradero_id).first()
        if par and hasattr(par, 'micros'):
            micros_filtradas = par.micros.all().order_by('numero')
    else:
        primera_cat = categorias.first()
        if primera_cat:
            micros_filtradas = primera_cat.micros.all().order_by('numero')

    micro_seleccionada = Micro.objects.filter(pk=micro_id).first() if micro_id else None
    paradero_seleccionado = Paradero.objects.filter(pk=paradero_id).first() if paradero_id else None

    coords_recorrido = []
    start_coord = None
    end_coord = None
    estado_actual_micro = None

    if micro_seleccionada:
        estado_actual_micro = estado_micro(micro_seleccionada, paradero_seleccionado)
        if hasattr(micro_seleccionada, 'recorrido') and micro_seleccionada.recorrido:
            raw_coords = list(micro_seleccionada.recorrido.coords)
            if len(raw_coords) > 400:
                step = len(raw_coords) // 250
                coords_recorrido = raw_coords[::step]
            else:
                coords_recorrido = raw_coords

            if raw_coords:
                start_coord = [raw_coords[0][1], raw_coords[0][0]]
                end_coord = [raw_coords[-1][1], raw_coords[-1][0]]

    if request.headers.get('x-requested-with') == 'XMLHttpRequest':
        cat_id = micro_seleccionada.categorias.first().id if micro_seleccionada and micro_seleccionada.categorias.exists() else 1
        return JsonResponse({
            "id": micro_seleccionada.id if micro_seleccionada else None,
            "numero": str(micro_seleccionada.numero) if micro_seleccionada else "--",
            "linea_nombre": micro_seleccionada.linea_nombre if micro_seleccionada else "General",
            "color": micro_seleccionada.color if micro_seleccionada and hasattr(micro_seleccionada, 'color') and micro_seleccionada.color else "#003366",
            "coords": [[c[1], c[0]] for c in coords_recorrido],
            "start_coord": start_coord,
            "end_coord": end_coord,
            "categoria_id": cat_id,
            "estado": estado_actual_micro,
        })

    return render(request, "rutasansana/maps.html", {
        "categorias": categorias,
        "paraderos": paraderos,
        "micros_filtradas": micros_filtradas,
        "micro_seleccionada": micro_seleccionada,
        "paradero_seleccionado": paradero_seleccionado,
        "ver_todas": ver_todas,
        "coords_recorrido": coords_recorrido,
        "start_coord": start_coord,
        "end_coord": end_coord,
        "estado_micro": estado_actual_micro,
        "mapbox_token": getattr(settings, 'MAPBOX_TOKEN', ''),
    })


@require_GET
def api_detalle_micro(request, micro_id):
    micro = get_object_or_404(Micro, pk=micro_id)
    paradero_id = request.GET.get("paradero")
    paradero = Paradero.objects.filter(pk=paradero_id).first() if paradero_id else None
    
    coords = []
    start_coord = None
    end_coord = None

    if hasattr(micro, 'recorrido') and micro.recorrido:
        raw_coords = list(micro.recorrido.coords)
        if len(raw_coords) > 400:
            step = len(raw_coords) // 250
            sampled = raw_coords[::step]
        else:
            sampled = raw_coords
        coords = [[c[1], c[0]] for c in sampled]

        if raw_coords:
            start_coord = [raw_coords[0][1], raw_coords[0][0]]
            end_coord = [raw_coords[-1][1], raw_coords[-1][0]]

    cat = micro.categorias.first()
    est = estado_micro(micro, paradero)

    return JsonResponse({
        "id": micro.id,
        "numero": str(micro.numero),
        "linea_nombre": micro.linea_nombre,
        "color": micro.color if hasattr(micro, 'color') and micro.color else "#003366",
        "coords": coords,
        "start_coord": start_coord,
        "end_coord": end_coord,
        "categoria_id": cat.id if cat else 1,
        "estado": est,
    })


@require_GET
def sala(request, categoria_id):
    categoria = get_object_or_404(CategoriaRuta, pk=categoria_id)
    paraderos = Paradero.objects.all().order_by('nombre')
    paradero = None
    if request.GET.get("paradero"):
        paradero = Paradero.objects.filter(pk=request.GET["paradero"]).first()
    
    micros_con_estado = []
    for micro in categoria.micros.all():
        est = estado_micro(micro, paradero)
        micros_con_estado.append({
            'micro': micro,
            'estado': est
        })

    return render(request, "alertas/sala.html", {
        "categoria": categoria,
        "micros_con_estado": micros_con_estado,
        "paraderos": paraderos,
        "alertas": alertas_activas(categoria=categoria),
    })


@require_GET
def api_estado(request, micro_id):
    micro = get_object_or_404(Micro, pk=micro_id)
    paradero = None
    if request.GET.get("paradero"):
        paradero = Paradero.objects.filter(pk=request.GET["paradero"]).first()
    return JsonResponse(estado_micro(micro, paradero))


@require_GET
def api_estados_categoria(request, categoria_id):
    categoria = get_object_or_404(CategoriaRuta, pk=categoria_id)
    paradero = None
    if request.GET.get("paradero"):
        paradero = Paradero.objects.filter(pk=request.GET["paradero"]).first()
    
    estados = {}
    for micro in categoria.micros.all():
        estados[micro.id] = estado_micro(micro, paradero)
    return JsonResponse(estados)


@require_GET
def api_alertas(request):
    micro = Micro.objects.filter(pk=request.GET.get("micro")).first() if request.GET.get("micro") else None
    categoria = CategoriaRuta.objects.filter(pk=request.GET.get("categoria")).first() if request.GET.get("categoria") else None
    return JsonResponse({"alertas": [serializar_alerta(a) for a in alertas_activas(micro=micro, categoria=categoria)]})


@require_POST
def api_reportar(request, micro_id):
    micro = get_object_or_404(Micro, pk=micro_id)

    try:
        ocupacion = int(request.POST.get("ocupacion", ""))
        ReporteEstado.Ocupacion(ocupacion)
    except ValueError:
        return JsonResponse({"error": "Ocupación inválida (1, 2 o 3)"}, status=400)

    parada = request.POST.get("parada", ReporteEstado.Parada.SIN_DATO)
    if parada not in ReporteEstado.Parada.values:
        return JsonResponse({"error": "Valor de parada inválido"}, status=400)

    try:
        estado_fisico = int(request.POST.get("estado_fisico", ReporteEstado.EstadoFisico.SIN_DATO))
        ReporteEstado.EstadoFisico(estado_fisico)
    except ValueError:
        return JsonResponse({"error": "Estado físico inválido (0 al 5)"}, status=400)

    paradero = None
    if request.POST.get("paradero"):
        paradero = Paradero.objects.filter(pk=request.POST["paradero"]).first()
        if paradero is None:
            return JsonResponse({"error": "Paradero inexistente"}, status=400)

    if not request.session.session_key:
        request.session.create()
    sesion = request.session.session_key

    reciente = ReporteEstado.objects.filter(
        micro=micro, sesion=sesion, creado__gte=timezone.now() - timedelta(minutes=COOLDOWN_MIN)
    ).exists()
    if reciente:
        return JsonResponse({"error": f"Ya reportaste esta micro hace menos de {COOLDOWN_MIN} min"}, status=429)

    ReporteEstado.objects.create(
        micro=micro,
        paradero=paradero,
        ocupacion=ocupacion,
        parada=parada,
        estado_fisico=estado_fisico,
        sesion=sesion,
    )
    evaluar_no_para(micro)
    return JsonResponse(estado_micro(micro, paradero), status=201)