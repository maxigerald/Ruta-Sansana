from django.urls import re_path

from .consumers import ChatCategoriaConsumer

websocket_urlpatterns = [
    re_path(r"^ws/alertas/chat/(?P<categoria_id>\d+)/$", ChatCategoriaConsumer.as_asgi()),
]
