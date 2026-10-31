from django.contrib import admin
from django.urls import path
from rutasansana import views

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', views.mapa_micros, name='mapa_micros'),
    path('api/micro/<int:micro_id>/', views.api_detalle_micro, name='api_detalle_micro'),
]