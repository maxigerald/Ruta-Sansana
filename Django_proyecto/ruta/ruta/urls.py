from django.contrib import admin
from django.urls import path, include  

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', include('rutasansana.urls')),
    path('alertas/', include('alertas.urls')),
]