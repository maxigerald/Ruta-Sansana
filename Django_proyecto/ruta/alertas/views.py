from datetime import timedelta
from django.core import serializers
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, render
from django.utils import timezone
from django.views.decorators.http import require_GET, require_POST

from rutasansana.models import CategoriaRuta, Micro, Paradero

from .models import ReporteEstado
from .services import alertas_activas, estado_micro, evaluar_no_para, serializar_alerta

COOLDOWN_MIN = 3   # un mismo navegador solo puede reportar una micro cada 3 min

@require_GET
def indice(request):
    micros_lista = [
        {
            "id": m.id, 
            "numero": str(m.numero), 
            "linea": m.linea_nombre,
            "color": m.color if hasattr(m, 'color') and m.color else '#dc2626', # NUEVO: Color asignado
            "categoria_id": m.categorias.first().id if m.categorias.exists() else 1
        } 
        for m in Micro.objects.all().order_by('numero')
    ]
    
    paraderos_lista = [
        {
            "id": p.id, 
            "nombre": p.nombre
        } 
        for p in Paradero.objects.all().order_by('nombre')
    ]

    return render(request, "alertas/index.html", {
        "categorias": CategoriaRuta.objects.all(),
        "alertas": alertas_activas(),
        "micros_json": micros_lista,
        "paraderos_json": paraderos_lista,
    })


@require_GET
def sala(request, categoria_id):
    categoria = get_object_or_404(CategoriaRuta, pk=categoria_id)
    return render(request, "alertas/sala.html", {
        "categoria": categoria,
        "micros": categoria.micros.all(),
        "alertas": alertas_activas(categoria=categoria),
    })


@require_GET
def api_estado(request, micro_id):
    micro = get_object_or_404(Micro, pk=micro_id)
    paradero = None
    if request.GET.get("paradero"):
        paradero = get_object_or_404(Paradero, pk=request.GET["paradero"])
    return JsonResponse(estado_micro(micro, paradero))


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

    # Validar el nuevo parámetro de estado físico (0 a 5)
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