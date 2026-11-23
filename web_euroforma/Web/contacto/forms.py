import re

from django import forms
from django.urls import reverse
from django.utils.html import format_html

from .models import Contacto

# Límites de validación (el servidor no se fía de lo que haga el navegador)
ASUNTO_MIN = 10
ASUNTO_MAX = 2000
MAX_ENLACES = 2

_CONTROL_CHARS = re.compile(r"[\x00-\x1f\x7f]")
_TELEFONO = re.compile(r"\+?[\d\s\-().]{6,15}")
_ENLACES = re.compile(r"https?://|www\.", re.IGNORECASE)


class Formulario(forms.ModelForm):
    # Campo trampa (honeypot): invisible para personas, los bots lo rellenan.
    sitio_web = forms.CharField(
        required=False,
        label="",
        widget=forms.TextInput(attrs={
            "class": "campo-trampa",
            "tabindex": "-1",
            "autocomplete": "off",
            "aria-hidden": "true",
        }),
    )

    # Consentimiento de privacidad validado en el servidor, no solo en el HTML.
    privacidad = forms.BooleanField(
        required=True,
        label="",
        label_suffix="",
        error_messages={"required": "Debes aceptar la política de privacidad."},
    )

    class Meta:
        model = Contacto
        fields = ['nombre', 'apellido', 'email', 'numero_tlf', 'asunto']
        widgets = {
            "asunto": forms.Textarea(attrs={"maxlength": ASUNTO_MAX}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["privacidad"].label = format_html(
            'Acepto la <a href="{}" target="_blank" rel="noopener">Política de Privacidad</a>',
            reverse("politicas"),
        )

    @staticmethod
    def _sin_control(valor, campo):
        if _CONTROL_CHARS.search(valor):
            raise forms.ValidationError(f"{campo} contiene caracteres no permitidos.")
        return valor

    def clean_nombre(self):
        return self._sin_control(self.cleaned_data["nombre"].strip(), "El nombre")

    def clean_apellido(self):
        return self._sin_control(self.cleaned_data["apellido"].strip(), "El apellido")

    def clean_numero_tlf(self):
        telefono = self.cleaned_data["numero_tlf"].strip()
        if not _TELEFONO.fullmatch(telefono):
            raise forms.ValidationError("Introduce un teléfono válido (solo números, espacios y +).")
        return telefono

    def clean_asunto(self):
        texto = self.cleaned_data["asunto"].strip()
        if len(texto) < ASUNTO_MIN:
            raise forms.ValidationError(f"El mensaje debe tener al menos {ASUNTO_MIN} caracteres.")
        if len(texto) > ASUNTO_MAX:
            raise forms.ValidationError(f"El mensaje no puede superar {ASUNTO_MAX} caracteres.")
        if len(_ENLACES.findall(texto)) > MAX_ENLACES:
            raise forms.ValidationError(f"El mensaje no puede contener más de {MAX_ENLACES} enlaces.")
        # Se eliminan caracteres de control salvo saltos de línea y tabulaciones.
        return re.sub(r"[\x00-\x08\x0b\x0c\x0e-\x1f\x7f]", "", texto)
