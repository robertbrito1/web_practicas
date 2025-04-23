from django.shortcuts import redirect, render
from .forms import Formulario
from django.core.mail import EmailMessage

def contacto(request):
    if request.method == "POST":
        formulario_contacto = Formulario(data=request.POST)
        if formulario_contacto.is_valid():
            # Guardar los datos en la base de datos
            formulario_contacto.save()

            # Obtener los datos del formulario
            nombre = formulario_contacto.cleaned_data.get("nombre")
            apellido = formulario_contacto.cleaned_data.get("apellido")
            email = formulario_contacto.cleaned_data.get("email")
            numero_tlf = formulario_contacto.cleaned_data.get("numero_tlf")
            asunto = formulario_contacto.cleaned_data.get("asunto")

            # Enviar el correo electrónico
            email_message = EmailMessage(
                "Mensaje desde app Django",
                f"El usuario con nombre: {nombre} {apellido}, con la dirección {email} y número de teléfono {numero_tlf}, escribe lo siguiente:\n\n{asunto}",
                "",
                ["britocanha@gmail.com"],
                reply_to=[email]
            )

            try:
                email_message.send()
                return redirect("/contacto/?valido")
            except:
                return redirect("/contacto/?error")
    else:
        formulario_contacto = Formulario()

    return render(request, "contacto/contacto.html", {'miformulario': formulario_contacto})
