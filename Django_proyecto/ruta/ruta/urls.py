from django.contrib import admin
from django.urls import path
from rutasansana import views

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', views.mapa_micros, name='mapa_micros'), # <-- Cambiado de shop_list a mapa_micros
]