from django.urls import path

from . import views

app_name = "alertas"

urlpatterns = [
    path("", views.indice, name="indice"),
    path("chat/<int:categoria_id>/", views.sala, name="sala"),
    path("api/micro/<int:micro_id>/estado/", views.api_estado, name="api_estado"),
    path("api/micro/<int:micro_id>/reportar/", views.api_reportar, name="api_reportar"),
    path("api/alertas/", views.api_alertas, name="api_alertas"),
]
