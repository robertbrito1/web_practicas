"""
Pruebas E2E (de extremo a extremo): un navegador real (Chromium, vía Playwright) usa la web
completa levantada en un servidor de pruebas, como lo haría una persona.

Qué cubren (lo que los tests unitarios y de integración no pueden ver):
  - Responsive: sin scroll horizontal en todas las páginas en móvil, tablet y escritorio.
  - Menú móvil: se abre, no tapa el logo, zonas táctiles, se cierra al tocar fuera / con Escape.
  - Consentimiento de cookies: YouTube, Google Maps y Elfsight NO se cargan hasta aceptar.
  - Formulario de contacto: envío correcto, errores visibles, honeypot.
  - Chat: botones, Enter, enlaces seguros, protección contra inyección de HTML, doble envío.
  - Acordeón de sedes y cabecera X-Frame-Options.

Cómo ejecutarlas (desde web_euroforma/Web):
    pip install -r requirements-dev.txt && playwright install chromium    # una sola vez
    python manage.py test e2e --pattern "e2e_*.py"

Si usas el Chrome ya instalado en tu equipo:  E2E_CHROME_PATH=/usr/bin/google-chrome
Requieren conexión a internet (Bootstrap se carga desde un CDN). Las peticiones a YouTube, Google
y Elfsight se bloquean y se registran: así las pruebas no dependen de esos servicios.
"""
import os
import unittest
import urllib.parse

# Playwright (API síncrona) y la base de datos de Django conviven en el mismo hilo de pruebas.
os.environ.setdefault("DJANGO_ALLOW_ASYNC_UNSAFE", "true")

from django.contrib.staticfiles.testing import StaticLiveServerTestCase  # noqa: E402
from django.core import mail  # noqa: E402
from django.core.cache import cache  # noqa: E402

from contacto.models import Contacto  # noqa: E402
from inicio.models import Profesor  # noqa: E402

try:
    from playwright.sync_api import sync_playwright
except ImportError:  # pragma: no cover
    sync_playwright = None

TERCEROS = ("youtube.com", "ytimg.com", "ggpht.com", "googlevideo.com", "google.com",
            "gstatic.com", "googleapis.com", "elfsight.com", "elfsightcdn.com")
PAGINAS = ["/", "/equipo", "/nosotros", "/preguntas", "/politicas", "/avisos", "/cockies", "/rsc",
           "/contacto/", "/profesor/ana-ruiz/"]


@unittest.skipIf(sync_playwright is None,
                 "Instala Playwright: pip install -r requirements-dev.txt && playwright install chromium")
class E2EBase(StaticLiveServerTestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls._playwright = sync_playwright().start()
        opciones = {"args": ["--no-sandbox"]}
        if os.environ.get("E2E_CHROME_PATH"):
            opciones["executable_path"] = os.environ["E2E_CHROME_PATH"]
        try:
            cls.navegador = cls._playwright.chromium.launch(**opciones)
        except Exception as exc:  # navegador no instalado
            cls._playwright.stop()
            super().tearDownClass()
            raise unittest.SkipTest(f"No se pudo abrir Chromium ({exc.__class__.__name__}). "
                                    "Ejecuta: playwright install chromium") from exc

    @classmethod
    def tearDownClass(cls):
        cls.navegador.close()
        cls._playwright.stop()
        super().tearDownClass()

    def setUp(self):
        cache.clear()  # los límites anti-abuso viven en la caché
        Profesor.objects.create(nombre="Ana", apellido="Ruiz", slug="ana-ruiz", experiencia=7,
                                asignaturas="Programación", fp="euroformac", imagen="x.jpg",
                                centros_trabajo="Madrid", formacion="DAM")

    # --- utilidades ------------------------------------------------------------------------------
    def url(self, ruta="/"):
        return self.live_server_url + ruta

    def pagina(self, ancho=1280, alto=800, tactil=False):
        """Pestaña nueva con cookies limpias. Registra y bloquea las peticiones a terceros."""
        contexto = self.navegador.new_context(viewport={"width": ancho, "height": alto},
                                              has_touch=tactil, is_mobile=tactil)
        self.addCleanup(contexto.close)
        pagina = contexto.new_page()
        pagina.tactil = tactil
        pagina.terceros = []

        def filtro(ruta):
            host = urllib.parse.urlparse(ruta.request.url).hostname or ""
            if host.endswith(TERCEROS):
                pagina.terceros.append(ruta.request.url)
                ruta.abort()
            else:
                ruta.continue_()

        pagina.route("**/*", filtro)
        return pagina

    def tocar(self, pagina, selector):
        (pagina.tap if pagina.tactil else pagina.click)(selector)

    def abrir(self, pagina, ruta="/", rechazar_cookies=True):
        pagina.goto(self.url(ruta), wait_until="load")
        if rechazar_cookies and pagina.locator("#cookie-banner").is_visible():
            self.tocar(pagina, "#reject-cookies")
        return pagina

    def sin_scroll_horizontal(self, pagina):
        return pagina.evaluate("document.documentElement.scrollWidth <= document.documentElement.clientWidth")

    def esperar_respuestas(self, pagina, n):
        """Espera a que haya `n` mensajes del asistente ya escritos (sin contar el indicador 'escribiendo')."""
        pagina.wait_for_function(
            "n => document.querySelectorAll('#chat-box .chat-msg--bot:not(:has(.chat-escribiendo))').length >= n", arg=n)

    @staticmethod
    def respuesta_fija(estado, cuerpo):
        """Manejador de ruta que responde siempre lo mismo (simula al servidor)."""
        tipo = "application/json" if cuerpo.startswith("{") else "text/html"
        return lambda ruta: ruta.fulfill(status=estado, content_type=tipo, body=cuerpo)

    def burbujas(self, pagina):
        return pagina.eval_on_selector_all(
            "#chat-box .chat-msg",
            "els => els.map(e => [e.classList.contains('chat-msg--user') ? 'user' : 'bot', e.innerText.trim()])")


# ---------------------------------------------------------------------------------------------------
class ResponsiveE2E(E2EBase):
    def test_sin_scroll_horizontal_en_todas_las_paginas_y_tamanos(self):
        for ancho, alto in [(320, 568), (375, 812), (768, 1024), (1280, 800)]:
            pagina = self.pagina(ancho, alto)
            for ruta in PAGINAS:
                with self.subTest(ruta=ruta, ancho=ancho):
                    self.abrir(pagina, ruta)
                    pagina.wait_for_timeout(300)
                    self.assertTrue(self.sin_scroll_horizontal(pagina), f"{ruta} desborda a {ancho}px")

    def test_cabecera_anticlickjacking(self):
        respuesta = self.pagina().goto(self.url("/"))
        self.assertEqual(respuesta.headers.get("x-frame-options"), "SAMEORIGIN")


class MenuMovilE2E(E2EBase):
    def test_menu_se_abre_sin_tapar_el_logo_y_se_cierra(self):
        for ancho, alto in [(320, 568), (375, 812), (768, 1024)]:
            with self.subTest(ancho=ancho):
                pagina = self.abrir(self.pagina(ancho, alto, tactil=True))
                self.assertFalse(pagina.locator(".menu").is_visible(), "el menú debe empezar cerrado")

                self.tocar(pagina, ".menu-icon")
                pagina.wait_for_timeout(300)
                menu, logo = pagina.locator(".menu").bounding_box(), pagina.locator(".logo-img").bounding_box()
                self.assertTrue(pagina.locator(".menu").is_visible())
                self.assertGreaterEqual(menu["y"], logo["y"] + logo["height"] - 1, "el menú tapa el logo")
                self.assertLessEqual(menu["x"] + menu["width"], ancho)
                self.assertEqual(pagina.get_attribute(".menu-icon", "aria-expanded"), "true")
                for i in range(pagina.locator(".menu li a").count()):
                    self.assertGreaterEqual(pagina.locator(".menu li a").nth(i).bounding_box()["height"], 44,
                                            "zona táctil demasiado pequeña")

                pagina.touchscreen.tap(ancho // 2, alto - 60)  # tocar fuera
                pagina.wait_for_timeout(300)
                self.assertFalse(pagina.locator(".menu").is_visible(), "tocar fuera debe cerrar el menú")

                self.tocar(pagina, ".menu-icon")
                pagina.wait_for_timeout(250)
                pagina.keyboard.press("Escape")
                pagina.wait_for_timeout(250)
                self.assertFalse(pagina.locator(".menu").is_visible(), "Escape debe cerrar el menú")

                self.tocar(pagina, ".menu-icon")
                with pagina.expect_navigation():
                    self.tocar(pagina, ".menu li a >> nth=1")
                self.assertTrue(pagina.url.endswith("/equipo"))

    def test_menu_con_teclado(self):
        pagina = self.abrir(self.pagina(375, 812))
        pagina.focus(".menu-icon")
        pagina.keyboard.press("Enter")
        pagina.wait_for_timeout(250)
        self.assertTrue(pagina.locator(".menu").is_visible())


class CookiesE2E(E2EBase):
    def test_terceros_no_se_cargan_hasta_aceptar(self):
        pagina = self.pagina()
        pagina.goto(self.url("/"), wait_until="load")
        pagina.wait_for_timeout(500)
        self.assertTrue(pagina.locator("#cookie-banner").is_visible())
        self.assertEqual(pagina.terceros, [], "hay peticiones a terceros antes de aceptar")
        self.assertEqual(pagina.locator("script[src*=elfsight]").count(), 0)
        self.assertEqual(pagina.evaluate("document.querySelectorAll('iframe[data-consent-src]:not([src])').length"),
                         pagina.locator("iframe[data-consent-src]").count(), "iframes cargados sin consentimiento")
        self.assertTrue(pagina.locator(".google-reviews .embed-placeholder").count() >= 1,
                        "debe verse el aviso en lugar de las reseñas")

        pagina.click("#accept-cookies")
        pagina.wait_for_timeout(800)
        consentimiento = [c for c in pagina.context.cookies() if c["name"] == "cookie_consent"]
        self.assertEqual(len(consentimiento), 1, "debe guardarse la cookie de consentimiento")
        self.assertIn("%22third%22%3Atrue", consentimiento[0]["value"])
        self.assertEqual(pagina.locator("script[src*=elfsight]").count(), 1, "Elfsight debe cargarse al aceptar")
        self.assertGreater(len(pagina.terceros), 0, "al aceptar deben intentarse cargar los terceros")
        self.assertFalse(pagina.locator("#cookie-banner").is_visible())

        pagina.terceros.clear()
        pagina.reload(wait_until="load")
        pagina.wait_for_timeout(500)
        self.assertFalse(pagina.locator("#cookie-banner").is_visible(), "no debe volver a preguntar")
        self.assertEqual(pagina.locator("script[src*=elfsight]").count(), 1, "la decisión se recuerda")

        pagina.click("#cookie-settings")  # cambiar de opinión
        pagina.click("#reject-cookies")
        pagina.wait_for_load_state("load")
        pagina.wait_for_timeout(500)
        self.assertEqual(pagina.locator("script[src*=elfsight]").count(), 0, "al rechazar se descargan los terceros")

    def test_rechazar_no_carga_nada_de_terceros_en_contacto(self):
        pagina = self.pagina()
        pagina.goto(self.url("/contacto/"), wait_until="load")
        pagina.click("#reject-cookies")
        pagina.reload(wait_until="load")
        pagina.wait_for_timeout(500)
        self.assertEqual(pagina.terceros, [])
        self.assertEqual(pagina.locator(".embed-placeholder").count(), 5, "5 mapas sustituidos por su aviso")

    def test_banner_compacto_en_pantallas_pequenas(self):
        for ancho, alto in [(320, 568), (360, 640), (375, 812), (667, 375), (812, 375)]:
            with self.subTest(pantalla=f"{ancho}x{alto}"):
                pagina = self.pagina(ancho, alto, tactil=True)
                pagina.goto(self.url("/"), wait_until="load")
                caja = pagina.locator("#cookie-banner").bounding_box()
                self.assertLessEqual(caja["height"] / alto, 0.45, "el banner ocupa demasiada pantalla")
                self.assertTrue(caja["y"] >= 0 and caja["y"] + caja["height"] <= alto + 1)
                for boton in ("#accept-cookies", "#reject-cookies"):
                    self.assertTrue(pagina.locator(boton).is_visible())


class ContactoE2E(E2EBase):
    def rellenar(self, pagina, mensaje="Hola, quiero información sobre los cursos de FP."):
        pagina.fill("#id_nombre", "Ana")
        pagina.fill("#id_apellido", "García")
        pagina.fill("#id_email", "ana@example.com")
        pagina.fill("#id_numero_tlf", "600123456")
        pagina.fill("#id_asunto", mensaje)

    def test_envio_correcto_guarda_y_envia_correo(self):
        pagina = self.abrir(self.pagina(), "/contacto/")
        self.rellenar(pagina)
        pagina.check("#id_privacidad")
        pagina.click("input[type=submit]")
        pagina.wait_for_load_state("load")
        self.assertTrue(pagina.url.endswith("/contacto/?valido"))
        self.assertIn("enviada correctamente", pagina.locator(".contenedorformulario").inner_text())
        self.assertEqual(Contacto.objects.count(), 1)
        self.assertEqual(len(mail.outbox), 1)

    def test_errores_visibles_y_privacidad_obligatoria_en_servidor(self):
        pagina = self.abrir(self.pagina(), "/contacto/")
        self.rellenar(pagina, mensaje="corto")
        pagina.evaluate("document.getElementById('id_privacidad').required = false")  # se salta el HTML
        pagina.click("input[type=submit]")
        pagina.wait_for_load_state("load")
        texto = pagina.locator(".contenedorformulario").inner_text()
        self.assertIn("al menos 10 caracteres", texto)
        self.assertIn("política de privacidad", texto.lower())
        self.assertEqual(Contacto.objects.count(), 0)

    def test_un_bot_que_rellena_el_campo_trampa_no_guarda_nada(self):
        pagina = self.abrir(self.pagina(), "/contacto/")
        self.assertFalse(pagina.locator("#id_sitio_web").is_visible(), "el campo trampa debe ser invisible")
        self.rellenar(pagina)
        pagina.check("#id_privacidad")
        pagina.evaluate("document.getElementById('id_sitio_web').value = 'http://spam.example'")
        pagina.click("input[type=submit]")
        pagina.wait_for_load_state("load")
        self.assertTrue(pagina.url.endswith("?valido"))  # al bot se le finge éxito
        self.assertEqual((Contacto.objects.count(), len(mail.outbox)), (0, 0))

    def test_acordeon_de_sedes_no_estira_a_las_demas(self):
        pagina = self.abrir(self.pagina(1280, 900), "/contacto/")
        altura = lambda: pagina.evaluate(  # noqa: E731
            "[...document.querySelectorAll('.accordion')].map(e => Math.round(e.getBoundingClientRect().height))")
        pagina.locator(".accordion-button >> nth=0").click()   # cierra Madrid (abierta por defecto)
        pagina.wait_for_timeout(700)
        pagina.locator(".accordion-button >> nth=1").click()   # abre Valencia
        pagina.wait_for_timeout(700)
        h = altura()
        self.assertTrue(h[0] == h[2] == h[3] and h[1] > h[0], f"las sedes se estiran entre sí: {h}")


class ChatE2E(E2EBase):
    def test_botones_enter_y_enlaces(self):
        pagina = self.abrir(self.pagina())
        pagina.locator("#chat-widget").scroll_into_view_if_needed()
        self.assertEqual(pagina.locator("#chat-sugerencias .chat-chip").count(), 6)
        self.assertIn("asistente virtual", self.burbujas(pagina)[0][1])

        pagina.click("#chat-sugerencias .chat-chip >> nth=0")  # ¿Qué cursos ofrecéis?
        self.esperar_respuestas(pagina, 2)
        respuesta = self.burbujas(pagina)[-1][1]
        self.assertTrue(all(c in respuesta for c in ("DAM", "DAW", "ASIR")))
        self.assertEqual(pagina.locator(".chat-escribiendo").count(), 0)
        self.assertTrue(pagina.evaluate(
            "(() => { const a = document.querySelector('#chat-box a[href^=\"https\"]');"
            " return !!a && a.target === '_blank' && a.rel.includes('noopener'); })()"), "enlace externo inseguro")

        pagina.fill("#user-input", "hola, ¿cómo me inscribo?")
        pagina.press("#user-input", "Enter")
        self.esperar_respuestas(pagina, 3)
        self.assertIn("formulario", self.burbujas(pagina)[-1][1])
        self.assertTrue(pagina.evaluate(
            "(() => { const a = [...document.querySelectorAll('#chat-box a')].find(x => x.getAttribute('href') === '/contacto/');"
            " return !!a && !a.target; })()"))

        pagina.fill("#user-input", "¿cuál es la capital de Francia?")
        pagina.press("#user-input", "Enter")
        self.esperar_respuestas(pagina, 4)
        self.assertIn("info@grupoeuroformac.com", self.burbujas(pagina)[-1][1])
        self.assertEqual(pagina.locator("#chat-sugerencias .chat-chip").count(), 6, "vuelven los botones iniciales")

    def test_equipo_docente_viene_de_la_base_de_datos(self):
        pagina = self.abrir(self.pagina())
        pagina.fill("#user-input", "¿Quiénes son los profesores?")
        pagina.press("#user-input", "Enter")
        self.esperar_respuestas(pagina, 2)
        self.assertIn("Ana Ruiz", self.burbujas(pagina)[-1][1])

    def test_el_html_escrito_por_el_usuario_no_se_ejecuta(self):
        pagina = self.abrir(self.pagina())
        pagina.fill("#user-input", '<img src=x onerror="window.__xss=1"><script>window.__xss=2</script>')
        pagina.press("#user-input", "Enter")
        self.esperar_respuestas(pagina, 2)
        self.assertIsNone(pagina.evaluate("window.__xss"))
        self.assertEqual(pagina.locator("#chat-box img").count(), 0)
        self.assertIn("<img", self.burbujas(pagina)[1][1], "el HTML debe verse como texto")

    def test_no_permite_doble_envio_mientras_espera(self):
        pagina = self.abrir(self.pagina())
        retenidas = []
        pagina.route("**/api/chat/", lambda ruta: retenidas.append(ruta))  # se retiene la respuesta
        pagina.fill("#user-input", "hola")
        pagina.press("#user-input", "Enter")
        pagina.press("#user-input", "Enter")
        pagina.wait_for_timeout(300)
        self.assertTrue(pagina.is_disabled("#user-input") and pagina.is_disabled("#chat-form button[type=submit]"))
        self.assertEqual(pagina.locator(".chat-escribiendo").count(), 1)
        self.assertEqual(len(retenidas), 1, "se envió más de una petición")
        retenidas[0].fulfill(status=200, content_type="application/json",
                             body='{"reply": "ok", "source": "faq", "suggestions": []}')
        pagina.wait_for_function("!document.getElementById('user-input').disabled")

    def test_errores_del_servidor_se_muestran_con_amabilidad(self):
        casos = [(429, '{"reply": "Has enviado muchos mensajes seguidos.", "source": "error", "suggestions": []}',
                  "muchos mensajes"), (403, "<h1>CSRF</h1>", "Recarga la página"),
                 (500, "<h1>Error</h1>", "Ha ocurrido un error")]
        for estado, cuerpo, esperado in casos:
            with self.subTest(estado=estado):
                pagina = self.abrir(self.pagina())
                pagina.route("**/api/chat/", self.respuesta_fija(estado, cuerpo))
                pagina.fill("#user-input", "prueba")
                pagina.press("#user-input", "Enter")
                self.esperar_respuestas(pagina, 2)
                self.assertIn(esperado, self.burbujas(pagina)[-1][1])
                self.assertFalse(pagina.is_disabled("#user-input"), "el chat debe seguir usable")

    def test_chat_en_movil(self):
        pagina = self.abrir(self.pagina(375, 812, tactil=True))
        pagina.locator("#chat-widget").scroll_into_view_if_needed()
        self.assertTrue(self.sin_scroll_horizontal(pagina))
        caja = pagina.locator("#chat-widget").bounding_box()
        self.assertTrue(caja["x"] >= 0 and caja["x"] + caja["width"] <= 375)
        self.assertGreaterEqual(pagina.evaluate(
            "parseFloat(getComputedStyle(document.getElementById('user-input')).fontSize)"), 16,
            "menos de 16px provoca zoom automático en iOS")
        pagina.tap("#chat-sugerencias .chat-chip >> nth=2")  # ¿Dónde están las sedes?
        self.esperar_respuestas(pagina, 2)
        self.assertIn("Madrid", self.burbujas(pagina)[-1][1])
