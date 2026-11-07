import time
from urllib.parse import parse_qs

from channels.db import database_sync_to_async
from channels.generic.websocket import AsyncJsonWebsocketConsumer
from rutasansana.models import CategoriaRuta

from .models import MensajeChat
from .services import grupo_categoria

MAX_TEXTO = 300
MAX_ALIAS = 20
INTERVALO_MIN_SEG = 1.0   # anti-flood por conexión


class ChatCategoriaConsumer(AsyncJsonWebsocketConsumer):
    """Chat de difusión por tipo de micro (CategoriaRuta). Anónimo, con alias opcional."""

    async def connect(self):
        self.categoria_id = int(self.scope["url_route"]["kwargs"]["categoria_id"])
        if not await self._categoria_existe():
            await self.close(code=4404)
            return
        qs = parse_qs(self.scope.get("query_string", b"").decode())
        alias = (qs.get("alias", [""])[0]).strip()[:MAX_ALIAS]
        self.alias = alias or "Anónimo"
        self.grupo = grupo_categoria(self.categoria_id)
        self._ultimo_envio = 0.0

        await self.channel_layer.group_add(self.grupo, self.channel_name)
        await self.accept()
        await self.send_json({"tipo": "historial", "mensajes": await self._historial()})

    async def disconnect(self, code):
        if hasattr(self, "grupo"):
            await self.channel_layer.group_discard(self.grupo, self.channel_name)

    async def receive_json(self, content, **kwargs):
        texto = str(content.get("texto", "")).strip()[:MAX_TEXTO]
        ahora = time.monotonic()
        if not texto or ahora - self._ultimo_envio < INTERVALO_MIN_SEG:
            return
        self._ultimo_envio = ahora
        await self._guardar(texto)
        await self.channel_layer.group_send(self.grupo, {
            "type": "chat.mensaje", "alias": self.alias, "texto": texto,
        })

    # --- eventos que llegan desde el grupo ---
    async def chat_mensaje(self, event):
        await self.send_json({"tipo": "mensaje", "alias": event["alias"], "texto": event["texto"]})

    async def alerta_nueva(self, event):
        await self.send_json({"tipo": "alerta", **event["alerta"]})

    # --- base de datos ---
    @database_sync_to_async
    def _categoria_existe(self):
        return CategoriaRuta.objects.filter(pk=self.categoria_id).exists()

    @database_sync_to_async
    def _historial(self):
        ultimos = MensajeChat.objects.filter(categoria_id=self.categoria_id).order_by("-creado")[:30]
        return [{"alias": m.alias, "texto": m.texto} for m in reversed(list(ultimos))]

    @database_sync_to_async
    def _guardar(self, texto):
        MensajeChat.objects.create(categoria_id=self.categoria_id, alias=self.alias, texto=texto)
