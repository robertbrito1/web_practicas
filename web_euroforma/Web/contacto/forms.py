from django import forms

from django import forms
from .models import Contacto

class Formulario(forms.ModelForm):
    class Meta:
        model = Contacto
        fields = ['nombre', 'apellido', 'email', 'numero_tlf', 'asunto']
