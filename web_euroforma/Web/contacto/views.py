import logging

from django.conf import settings
from django.core.cache import cache
from django.core.mail import EmailMessage
from django.shortcuts import redirect, render

from .forms import Formulario

logger = logging.getLogger(__name__)

# Límites anti-abuso: envíos válidos permitidos por ventana de tiempo.
LIMITE_POR_IP = 3          # por visitante
LIMITE_GLOBAL = 50         # en total, para proteger el buzón y la cuenta de Gmail
VENTANA_SEGUNDOS = 600     # 10 minutos


def _contar(clave):
    """Suma 1 al contador de `clave` (caduca a los VENTANA_SEGUNDOS) y lo devuelve."""
    if cache.add(clave, 1, VENTANA_SEGUNDOS):
        return 1
    try:
        return cache.incr(clave)
    except ValueError:  # la clave caducó justo ahora
        cache.set(clave, 1, VENTANA_SEGUNDOS)
        return 1


def _limite_superado(request):
    # REMOTE_ADDR: no se usa X-Forwarded-For porque el cliente puede falsificarlo.
    ip = request.META.get("REMOTE_ADDR", "desconocida")
    return _contar(f"contacto:ip:{ip}") > LIMITE_POR_IP or _contar("contacto:global") > LIMITE_GLOBAL


def contacto(request):
    if request.method == "POST":
        formulario_contacto = Formulario(data=request.POST)
        if formulario_contacto.is_valid():
            datos = formulario_contacto.cleaned_data

            # Un bot rellenó el campo trampa: se finge éxito y no se guarda ni envía nada.
            if datos.get("sitio_web"):
                logger.warning("Contacto descartado por honeypot (IP %s)", request.META.get("REMOTE_ADDR"))
                return redirect("/contacto/?valido")

            if _limite_superado(request):
                logger.warning("Contacto bloqueado por límite de envíos (IP %s)", request.META.get("REMOTE_ADDR"))
                return redirect("/contacto/?limite")

            # Guardar los datos en la base de datos
            formulario_contacto.save()

            # Enviar el correo electrónico (texto plano: no se interpreta HTML)
            email_message = EmailMessage(
                "Mensaje desde app Django",
                f"El usuario con nombre: {datos['nombre']} {datos['apellido']}, "
                f"con la dirección {datos['email']} y número de teléfono {datos['numero_tlf']}, "
                f"escribe lo siguiente:\n\n{datos['asunto']}",
                None,  # remitente: DEFAULT_FROM_EMAIL
                [settings.CONTACT_RECIPIENT],
                reply_to=[datos["email"]],
            )

            try:
                email_message.send()
                return redirect("/contacto/?valido")
            except Exception:
                logger.exception("No se pudo enviar el correo de contacto")
                return redirect("/contacto/?error")
    else:
        formulario_contacto = Formulario()

    return render(request, "contacto/contacto.html", {'miformulario': formulario_contacto})
