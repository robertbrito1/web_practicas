

from django.contrib import admin
from .models import Contacto

@admin.register(Contacto)
class ContactoAdmin(admin.ModelAdmin):
    list_display = ('nombre', 'apellido', 'email', 'numero_tlf')
    search_fields = ('nombre', 'apellido', 'email')
