import logging

from asgiref.sync import async_to_sync
from channels.layers import get_channel_layer
from django.db.models.signals import post_save
from django.dispatch import receiver

from .models import Alerta
from .services import grupo_categoria, serializar_alerta

logger = logging.getLogger(__name__)


@receiver(post_save, sender=Alerta)
def difundir_alerta(sender, instance, created, **kwargs):
    """Al crear una alerta activa, se empuja en vivo a los chats que corresponden."""
    if not (created and instance.activa):
        return
    layer = get_channel_layer()
    if layer is None:
        return
    evento = {"type": "alerta.nueva", "alerta": serializar_alerta(instance)}
    for categoria_id in instance.ids_categorias_destino():
        try:
            async_to_sync(layer.group_send)(grupo_categoria(categoria_id), evento)
        except Exception:  # el chat nunca debe impedir guardar una alerta
            logger.exception("No se pudo difundir la alerta %s", instance.pk)
