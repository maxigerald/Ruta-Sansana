from datetime import timedelta

from django.db.models import Q
from django.utils import timezone

from rutasansana.models import Reporte  # solo lectura: se aprovechan los reportes que ya existen

from .models import Alerta, ReporteEstado

VENTANA_MIN = 10          # minutos que cuenta un reporte
MIN_REPORTES = 2          # bajo esto el dato se marca como poco confiable
VENTANA_NO_PARA_MIN = 15  # ventana para detectar "no está parando"
UMBRAL_NO_PARA = 3        # mínimo de reportes "no paró"...
PCT_NO_PARA = 60          # ...y que sean al menos este % de los reportes de parada
TEXTO_OCUPACION = {1: "Vacía", 2: "Media", 3: "Llena"}
TEXTO_OCUPACION = {1: "Vacía", 2: "Media", 3: "Llena"}
# NUEVO DICCIONARIO:
TEXTO_ESTADO_FISICO = {1: "Pésimo (Riesgoso)", 2: "Malo", 3: "Regular", 4: "Bueno", 5: "Excelente"}


def estado_micro(micro, paradero=None):
    
    ocupaciones = [r.ocupacion for r in nuevos] + [r.nivel_ocupacion for r in existentes]
    n = len(ocupaciones)
    prom = round(sum(ocupaciones) / n, 1) if n else None
    nivel = min(3, max(1, round(prom))) if prom is not None else None

    con_estado = [r.estado_fisico for r in nuevos if r.estado_fisico != ReporteEstado.EstadoFisico.SIN_DATO]
    m = len(con_estado)
    prom_estado = round(sum(con_estado) / m) if m else None

    con_parada = [r for r in nuevos if r.parada != ReporteEstado.Parada.SIN_DATO]

    return {
        "micro_id": micro.id,
        "micro": micro.numero,
        "ocupacion": prom,
        "ocupacion_texto": TEXTO_OCUPACION.get(nivel),
        "pct_no_paro": pct_no_paro,
        "estado_fisico_texto": TEXTO_ESTADO_FISICO.get(prom_estado, "Sin datos"), # <- NUEVO DATO ENVIADO AL HTML
        "reportes": n,
        "confiable": n >= MIN_REPORTES,
        "alertas": [serializar_alerta(a) for a in alertas_activas(micro=micro)],
    }

def grupo_categoria(categoria_id):
    """Nombre del grupo de Channels (sala de chat) de una categoría."""
    return f"alertas_cat_{categoria_id}"


def alertas_activas(micro=None, categoria=None):
    """Alertas vigentes que aplican a una micro, a una categoría o generales."""
    ahora = timezone.now()
    qs = Alerta.objects.filter(activa=True).filter(Q(expira_en__isnull=True) | Q(expira_en__gt=ahora))
    general = Q(micro__isnull=True, categoria__isnull=True)
    if micro is not None:
        qs = qs.filter(Q(micro=micro) | Q(categoria__in=micro.categorias.all()) | general)
    elif categoria is not None:
        qs = qs.filter(Q(categoria=categoria) | Q(micro__categorias=categoria) | general)
    return qs.distinct()


def serializar_alerta(a):
    return {"id": a.id, "titulo": a.titulo, "mensaje": a.mensaje, "severidad": a.severidad}


def estado_micro(micro, paradero=None):
    """Ocupación, % de 'no paró' y alertas de una micro (opcionalmente en un paradero)."""
    desde = timezone.now() - timedelta(minutes=VENTANA_MIN)

    nuevos = ReporteEstado.objects.filter(micro=micro, creado__gte=desde)
    existentes = Reporte.objects.filter(micro=micro, fecha_creacion__gte=desde, es_fiable=True)
    if paradero is not None:
        nuevos = nuevos.filter(Q(paradero=paradero) | Q(paradero__isnull=True))
        existentes = existentes.filter(paradero=paradero)

    ocupaciones = [r.ocupacion for r in nuevos] + [r.nivel_ocupacion for r in existentes]
    n = len(ocupaciones)
    prom = round(sum(ocupaciones) / n, 1) if n else None
    nivel = min(3, max(1, round(prom))) if prom is not None else None

    con_parada = [r for r in nuevos if r.parada != ReporteEstado.Parada.SIN_DATO]
    no_paro = sum(r.parada == ReporteEstado.Parada.NO_PARO for r in con_parada)
    pct_no_paro = round(100 * no_paro / len(con_parada)) if con_parada else None

    return {
        "micro_id": micro.id,
        "micro": micro.numero,
        "ocupacion": prom,
        "ocupacion_texto": TEXTO_OCUPACION.get(nivel),
        "pct_no_paro": pct_no_paro,
        "reportes": n,
        "confiable": n >= MIN_REPORTES,
        "alertas": [serializar_alerta(a) for a in alertas_activas(micro=micro)],
    }


def evaluar_no_para(micro):
    """
    Si varios estudiantes reportan que la micro no paró, genera una alerta
    automática (una sola cada 30 min por micro). Devuelve la alerta o None.
    """
    desde = timezone.now() - timedelta(minutes=VENTANA_NO_PARA_MIN)
    reps = [r for r in ReporteEstado.objects.filter(micro=micro, creado__gte=desde)
            if r.parada != ReporteEstado.Parada.SIN_DATO]
    no_paro = sum(r.parada == ReporteEstado.Parada.NO_PARO for r in reps)
    if not reps or no_paro < UMBRAL_NO_PARA or 100 * no_paro / len(reps) < PCT_NO_PARA:
        return None

    ya_existe = Alerta.objects.filter(
        micro=micro, automatica=True, creado__gte=timezone.now() - timedelta(minutes=30)
    ).exists()
    if ya_existe:
        return None

    return Alerta.objects.create(
        micro=micro,
        titulo=f"Micro {micro.numero}: reportan que no está parando",
        mensaje=f"{no_paro} estudiantes reportaron en los últimos {VENTANA_NO_PARA_MIN} min que no se detuvo.",
        severidad=Alerta.Severidad.ADVERTENCIA,
        expira_en=timezone.now() + timedelta(minutes=30),
        automatica=True,
    )
