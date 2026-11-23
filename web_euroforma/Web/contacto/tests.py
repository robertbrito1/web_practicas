from django.core import mail
from django.core.cache import cache
from django.test import TestCase, override_settings
from django.urls import reverse

from .models import Contacto
from . import views


def datos_validos(**cambios):
    datos = {
        "nombre": "Ana",
        "apellido": "García",
        "email": "ana@example.com",
        "numero_tlf": "600 123 456",
        "asunto": "Hola, quiero información sobre los cursos de FP.",
        "privacidad": "on",
        "sitio_web": "",
    }
    datos.update(cambios)
    return datos


@override_settings(CONTACT_RECIPIENT="destino@example.com")
class ContactoSeguridadTests(TestCase):
    def setUp(self):
        cache.clear()  # los contadores del límite de envíos viven en la caché
        self.url = reverse("contacto")

    # --- caso normal ---------------------------------------------------------
    def test_envio_valido_guarda_y_envia(self):
        r = self.client.post(self.url, datos_validos())
        self.assertRedirects(r, "/contacto/?valido", fetch_redirect_response=False)
        self.assertEqual(Contacto.objects.count(), 1)
        self.assertEqual(len(mail.outbox), 1)
        self.assertEqual(mail.outbox[0].to, ["destino@example.com"])
        self.assertEqual(mail.outbox[0].reply_to, ["ana@example.com"])

    # --- bots ----------------------------------------------------------------
    def test_honeypot_rellenado_no_guarda_ni_envia(self):
        r = self.client.post(self.url, datos_validos(sitio_web="http://spam.example"))
        self.assertRedirects(r, "/contacto/?valido", fetch_redirect_response=False)  # no se avisa al bot
        self.assertEqual(Contacto.objects.count(), 0)
        self.assertEqual(len(mail.outbox), 0)

    def test_limite_por_ip(self):
        for _ in range(views.LIMITE_POR_IP):
            self.client.post(self.url, datos_validos())
        r = self.client.post(self.url, datos_validos())
        self.assertRedirects(r, "/contacto/?limite", fetch_redirect_response=False)
        self.assertEqual(len(mail.outbox), views.LIMITE_POR_IP)
        self.assertEqual(Contacto.objects.count(), views.LIMITE_POR_IP)

    def test_limite_global_protege_el_buzon(self):
        for i in range(views.LIMITE_GLOBAL):
            self.client.post(self.url, datos_validos(), REMOTE_ADDR=f"10.0.{i // 250}.{i % 250 + 1}")
        r = self.client.post(self.url, datos_validos(), REMOTE_ADDR="192.168.9.9")
        self.assertRedirects(r, "/contacto/?limite", fetch_redirect_response=False)
        self.assertEqual(len(mail.outbox), views.LIMITE_GLOBAL)

    def test_envios_invalidos_no_gastan_el_limite(self):
        for _ in range(views.LIMITE_POR_IP + 2):
            self.client.post(self.url, datos_validos(email="no-es-un-email"))
        r = self.client.post(self.url, datos_validos())
        self.assertRedirects(r, "/contacto/?valido", fetch_redirect_response=False)

    # --- validación en servidor ------------------------------------------------
    def assert_rechazado(self, **cambios):
        r = self.client.post(self.url, datos_validos(**cambios))
        self.assertEqual(r.status_code, 200)  # vuelve al formulario con errores
        self.assertEqual(Contacto.objects.count(), 0)
        self.assertEqual(len(mail.outbox), 0)

    def test_privacidad_obligatoria_en_servidor(self):
        datos = datos_validos()
        del datos["privacidad"]  # alguien se salta la casilla del navegador
        r = self.client.post(self.url, datos)
        self.assertEqual(r.status_code, 200)
        self.assertEqual(Contacto.objects.count(), 0)

    def test_mensaje_demasiado_corto(self):
        self.assert_rechazado(asunto="hola")

    def test_mensaje_demasiado_largo(self):
        self.assert_rechazado(asunto="a" * 2001)

    def test_demasiados_enlaces(self):
        self.assert_rechazado(asunto="Mira http://a.com y http://b.com y http://c.com para ganar dinero")

    def test_telefono_invalido(self):
        self.assert_rechazado(numero_tlf="abc<script>")

    def test_email_invalido(self):
        self.assert_rechazado(email="no-es-un-email")

    # --- inyección -----------------------------------------------------------------
    def test_inyeccion_de_cabeceras_en_email(self):
        self.assert_rechazado(email="victima@example.com\nBcc: otro@example.com")

    def test_saltos_de_linea_en_nombre(self):
        self.assert_rechazado(nombre="Ana\r\nBcc: otro@example.com")

    def test_html_se_envia_como_texto_plano_y_se_escapa_en_pantalla(self):
        self.client.post(self.url, datos_validos(asunto="<script>alert(1)</script> mensaje de prueba"))
        correo = mail.outbox[0]
        self.assertEqual(correo.content_subtype, "plain")  # el correo no interpreta HTML
        # y la pantalla de contacto no refleja HTML sin escapar
        r = self.client.post(self.url, datos_validos(asunto="<script>alert(1)</script>", numero_tlf="abc"))
        self.assertNotContains(r, "<script>alert(1)</script>")

    # --- fallos de envío ----------------------------------------------------------------
    def test_si_falla_el_correo_se_avisa_y_no_se_pierde_el_mensaje(self):
        with override_settings(EMAIL_BACKEND="contacto.tests.BackendQueFalla"):
            r = self.client.post(self.url, datos_validos())
        self.assertRedirects(r, "/contacto/?error", fetch_redirect_response=False)
        self.assertEqual(Contacto.objects.count(), 1)  # queda guardado en la base de datos

    def test_pagina_muestra_aviso_de_error_y_de_limite(self):
        self.assertContains(self.client.get(self.url + "?error"), "No hemos podido enviar")
        self.assertContains(self.client.get(self.url + "?limite"), "demasiados mensajes")


class BackendQueFalla:
    """Simula un SMTP caído."""

    def __init__(self, *args, **kwargs):
        pass

    def send_messages(self, mensajes):
        raise ConnectionError("SMTP caído")

    def open(self):
        pass

    def close(self):
        pass
