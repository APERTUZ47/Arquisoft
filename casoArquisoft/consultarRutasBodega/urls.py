from django.urls import path
from django.views.generic import RedirectView
from . import views

app_name = 'consultarRutasBodega'

urlpatterns = [
    path('', views.index, name='index'),
    path('objetos/', views.consultar_rutas, name='consultar_rutas'),
    path('buscar/', views.buscar_ruta, name='buscar_ruta'),
    path('api/objetos/', views.obtener_objetos_json, name='obtener_objetos_json'),
    # Compatibilidad hacia atrás - redirige rutas/ a objetos/
    path('rutas/', RedirectView.as_view(pattern_name='consultarRutasBodega:consultar_rutas', permanent=True), name='rutas_redirect'),
]