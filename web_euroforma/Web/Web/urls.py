"""
URL configuration for Web project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/5.1/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path, include
from django.conf.urls.static import static
from django.conf import settings

urlpatterns = [
    path('admin/', admin.site.urls),
    path('contacto/', include('contacto.urls')),  # Rutas de la app "contacto"
    path('nosotros/', include('inicio.urls')),
    path('equipo/', include('inicio.urls')), 
    path('preguntas/', include('inicio.urls')),   # Rutas de la app "inicio"
    path('politicas/', include('inicio.urls')),
    path('avisos/', include('inicio.urls')),
    path('cockies/', include('inicio.urls')),
    path('', include('inicio.urls')),           # Página de inicio
]

# Configuración para servir archivos estáticos y multimedia
urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)

