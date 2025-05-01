from django.urls import path
from . import views
from django.conf.urls.static import static
from django.conf import settings


urlpatterns = [
    path('equipo', views.equipo, name='equipo'),
    path('profesor1/', views.profesor1, name='profesor1'),
    path('profesor2/', views.profesor2, name='profesor2'),
    path('profesor3/', views.profesor3, name='profesor3'),
    path('profesor4/', views.profesor4, name='profesor4'),
    path('profesor5/', views.profesor5, name='profesor5'),
    path('profesor6/', views.profesor6, name='profesor6'),
    path('profesor7/', views.profesor7, name='profesor7'),
    path('profesor8/', views.profesor8, name='profesor8'),
    path('nosotros', views.nosotros, name='nosotros'), 
    path('preguntas', views.preguntas, name='preguntas'), 
    path('', views.inicio, name='inicio'),
    
    
    
]
urlpatterns+=static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)