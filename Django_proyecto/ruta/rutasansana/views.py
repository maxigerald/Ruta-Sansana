import requests
from django.conf import settings
from django.shortcuts import render
from .models import Micro, CategoriaRuta

def mapa_micros(request):
    categoria_id = request.GET.get('categoria')
    micro_id = request.GET.get('micro')

    categorias = CategoriaRuta.objects.all()
    micros_filtradas = []
    micro_seleccionada = None
    coords_recorrido = []

    if categoria_id:
        micros_filtradas = Micro.objects.filter(categorias__id=categoria_id)

    if micro_id:
        try:
            micro_seleccionada = Micro.objects.get(id=micro_id)
            
            # Si es la micro 505 (o puedes aplicar esto según el ID o número de la micro)
            if micro_seleccionada.numero == 505 or micro_seleccionada.id == int(micro_id):
                
                # LISTA DE PUNTOS CLAVE (LONGITUD, LATITUD)
                # Puedes agregar tantos puntos como quieras ordenados desde el inicio hasta el final
                puntos_clave = [
                "-71.64741866446157,-33.03684018534808",
                "-71.64584861148558,-33.03834383833594",
                "-71.64654169616931,-33.04027837993849",
                "-71.64559588842447,-33.04132523439357",
                "-71.64377538436919,-33.04041081277655",
                "-71.64403335053208,-33.036796283061896",
                "-71.64215678471813,-33.034272808403294",
                "-71.63630394090376,-33.029961615203455",
                "-71.64030833732657,-33.02495177010322",

            ]
                
                # Unimos todos los puntos con punto y coma para la URL de OSRM
                waypoints = ";".join(puntos_clave)
                
                # Petición a OSRM para que una todos estos puntos por las calles reales
                url = f"http://router.project-osrm.org/route/v1/driving/{waypoints}?overview=full&geometries=geojson"
                response = requests.get(url)
                data = response.json()
                
                if "routes" in data and len(data["routes"]) > 0:
                    coords_recorrido = data["routes"][0]["geometry"]["coordinates"]
                    
        except Micro.DoesNotExist:
            pass

    context = {
        'categorias': categorias,
        'micros_filtradas': micros_filtradas,
        'micro_seleccionada': micro_seleccionada,
        'coords_recorrido': coords_recorrido,
        'categoria_activa': int(categoria_id) if categoria_id else None,
        'mapbox_token': settings.MAPBOX_TOKEN,
    }
    return render(request, 'rutasansana/maps.html', context)