from django.urls import path
from . import views
from django.conf.urls.static import static
from django.conf import settings


urlpatterns = [
    path('equipo', views.equipo, name='equipo'),
    path('profesor/<slug:slug>/', views.profesor_detalle, name='profesor_detalle'),
    path('nosotros', views.nosotros, name='nosotros'), 
    path('preguntas', views.preguntas, name='preguntas'), 
    path('politicas', views.politicas, name='politicas'), 
    path('avisos', views.avisos, name='avisos'), 
    path('cockies', views.cockies, name='cockies'), 
    path('', views.inicio, name='inicio'),
    
    
    
]
urlpatterns+=static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)