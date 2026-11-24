# FP Euroformac · Web con Django

Prácticas de la FP DAM: web de la academia **Euroformac**. Backend con **Django**; frontend con HTML, CSS, JavaScript y Bootstrap.

> Es una web de **portafolio / demostración**: las sedes, el contacto y los ciclos salen de la propia web; el resto de datos del asistente (turnos, proceso de inscripción…) son de ejemplo.

## Resumen para reclutadores

Después de la versión inicial, el proyecto se revisó y mejoró en cuatro frentes: que **se vea bien en cualquier pantalla**, que **sea seguro**, que **cumpla la normativa de cookies** y que **cualquiera pueda clonarlo y ejecutarlo con un comando**. Además se añadió un **asistente de chat** con arquitectura preparada para IA.

| Área | Qué se hizo | Cómo se comprobó |
|---|---|---|
| **Responsive** | Se corrigió el desbordamiento horizontal de las 10 páginas en móvil y tablet (causa: un logo de 350 px sin límite de ancho), el pie de página, el formulario de contacto, las tarjetas del equipo y los acordeones de sedes | Prueba E2E: 4 tamaños (320, 375, 768 y 1280 px) × 10 páginas = **40 combinaciones** sin scroll horizontal |
| **Menús y ventanas emergentes** | El menú móvil ya no tapa el logo, tiene zonas táctiles de 48 px, se cierra al tocar fuera / con Escape y funciona con teclado. El banner de cookies es compacto en pantallas pequeñas y apaisadas | Pruebas E2E con toque real: menú en 3 tamaños y banner en 5 (incluido móvil apaisado) |
| **Cookies (RGPD/LSSI)** | Consentimiento **real**: YouTube, Google Maps y las reseñas de Google (Elfsight) **no se cargan hasta que el usuario acepta**; Aceptar y Rechazar tienen el mismo peso; se puede cambiar la decisión desde «Configurar cookies»; la política de cookies lista las cookies que la web usa de verdad | Prueba E2E: sin aceptar, **0 peticiones** a esos servicios; al aceptar se cargan y al rechazar se descargan |
| **Seguridad del formulario de contacto** | Campo trampa anti-bots, límite de envíos (por visitante y global), validación en servidor (longitud, enlaces, teléfono, saltos de línea), consentimiento de privacidad validado en el servidor, avisos de error al usuario | 16 tests de integración + 3 pruebas E2E del formulario (envío, errores y campo trampa) |
| **Secretos y configuración** | Credenciales fuera del código (`.env`), destinatario del correo configurable, `X-Frame-Options: SAMEORIGIN` (anticlickjacking), tamaño máximo de petición | Revisión del historial y de lo que se sube a git |
| **Portabilidad** | `run.sh` / `run.bat` (entorno virtual, dependencias, migraciones y servidor en un paso), `settings.py` limpio y leído de `.env`, `.env.example`, correo por consola si no hay credenciales | Se clonó el repo en una carpeta limpia y se ejecutó con `./run.sh` |
| **Asistente de chat** | Se implementó con **preguntas frecuentes primero para ahorrar costes**: lo habitual se responde gratis y al instante, y solo lo que el FAQ no sabe llegaría a la IA (opcional, apagada por defecto). Ver la sección siguiente | 41 tests (unitarios e integración) + 6 pruebas E2E |
| **Despliegue** | **Despliegue continuo (CD):** cada `git push` a la rama `main` se despliega automáticamente en el hosting, sin pasos manuales. Archivos estáticos servidos con WhiteNoise y configuración sensible por variables de entorno | Configurado en la plataforma de hosting (no en el repositorio) |
| **Calidad y pruebas** | **16 pruebas unitarias, 41 de integración y 17 E2E** en navegador real (Playwright), JavaScript sin `var`, `.gitignore` y limpieza de archivos compilados del repo | Ver la sección [Tests](#tests) |

*Estas mejoras se hicieron con ayuda de Claude Code (asistente de IA) y se revisaron y verificaron con las pruebas descritas.*

## Arquitectura: monolito modular

El proyecto es un **monolito**: el servidor, las páginas HTML (renderizadas por Django con plantillas), los archivos estáticos y el endpoint del chat viven en **un solo proyecto y se despliegan juntos**. No hay un frontend separado ni varios servicios.

```
        Navegador
            │
   ┌────────▼─────────────────────────────────┐
   │  Django (un solo despliegue)             │
   │  ├── inicio/    páginas y plantillas     │
   │  ├── contacto/  formulario + correo      │
   │  └── chat/      asistente (FAQ + IA)     │
   │  + SQLite · WhiteNoise (estáticos)       │
   └──────────────────────────────────────────┘
```

**Por qué esta decisión**
- **Despliegue sencillo:** un `git push` publica toda la web (ver [Despliegue](#despliegue)); no hay que coordinar varios servicios ni versiones.
- **Una sola tecnología principal (Python/Django)** para backend, plantillas, API del chat y tests, en vez de repartir el trabajo entre un backend y un frontend independientes.
- **Menos piezas que configurar:** sin CORS, sin dos servidores y sin una API versionada entre frontend y backend; el CSRF y las cookies funcionan en el mismo origen.
- **Sigue siendo ordenado:** cada app (`inicio`, `contacto`, `chat`) tiene una responsabilidad clara y sus propios tests, así que se podría separar más adelante si el proyecto creciera.

Para el tamaño de esta web es la opción más práctica; si tuviera mucho tráfico o varios equipos trabajando a la vez, convendría separar frontend y backend.

## Asistente de chat (FAQ + IA opcional)

En la página de inicio hay un asistente que responde a las dudas típicas (cursos, becas, sedes, inscripción, contacto…).

```
Navegador (jv/ia.js) ──POST /api/chat/──▶ Django (chat/views.py)
                                             1. valida la petición, CSRF y límites
                                             2. FAQ (chat/faq.py)  ──▶ responde          coste: 0
                                             3. ¿sin respuesta? ──▶ IA (chat/ia.py)      apagada por defecto
                                             4. si nada responde ──▶ deriva a una persona
```

**Por qué primero preguntas frecuentes y después IA (ahorro de costes).** Las preguntas habituales se contestan al instante, sin red y sin coste, y con información controlada (no inventa precios ni fechas). Cada pregunta que resuelve el FAQ es una llamada a la API de IA que no se paga: la IA solo se consultaría para lo que el FAQ no sabe, así que se hacen muchas menos llamadas y el gasto se mantiene muy bajo.

**Una sola fuente de verdad.** El prompt de la IA se construye a partir de las mismas entradas del FAQ (`chat/faq.py`); editar ese archivo cambia lo que sabe el asistente en ambos modos.

**Seguridad del chat**
- La clave de la API vive solo en el servidor (`.env`); nunca llega al navegador.
- Protección CSRF activa (el token viaja en una cabecera) y todo el texto se inserta con `createTextNode`: no se puede inyectar HTML ni scripts.
- Límites: 30 mensajes por visitante cada 10 minutos; para la IA, 6 llamadas por visitante cada 10 minutos y 300 al día en total.
- El modelo no tiene herramientas ni acceso a la base de datos: lo peor que puede hacer es escribir texto.
- Si la IA falla, se agota el saldo o rechaza la petición, el chat responde con un mensaje de reserva (nunca un error 500).

**Activar la IA (opcional).** Está totalmente implementada pero **apagada**: sin clave el chat funciona igual con el FAQ. Para activarla, en el `.env`:

```
CHAT_IA_ENABLED=True
ANTHROPIC_API_KEY=tu_clave
# CHAT_IA_MODEL=claude-haiku-5-5      (por defecto; modelo económico)
```

La API de Claude se factura aparte de cualquier suscripción ([console.anthropic.com](https://console.anthropic.com)). Con el modelo por defecto el coste estimado es de céntimos por cada mil mensajes, y conviene fijar un límite de gasto en la consola.

## Arrancar el proyecto (1 comando)

Requisitos: **Python 3.10+** y Git.

```bash
git clone https://github.com/robertbrito1/web_practicas.git
cd web_practicas
./run.sh          # Linux / macOS
run.bat           # Windows
```

El script crea el entorno virtual, instala las dependencias, aplica las migraciones y levanta el servidor en **http://127.0.0.1:8000**. Para otro puerto: `./run.sh 8080`.

<details>
<summary>Paso a paso (manual)</summary>

```bash
python3 -m venv .venv
source .venv/bin/activate          # Windows: .venv\Scripts\activate
pip install -r requirements.txt
cp .env.example .env               # Windows: copy .env.example .env
cd web_euroforma/Web
python manage.py migrate
python manage.py runserver
```
</details>

## Configuración (.env)

Los valores que cambian de un equipo a otro van en un archivo `.env` en la raíz del repositorio (no se sube a git). Hay una plantilla en `.env.example`.

| Variable | Para qué sirve |
|---|---|
| `EMAIL_HOST_USER` | Cuenta de Gmail que envía los mensajes del formulario de contacto |
| `EMAIL_HOST_PASSWORD` | [Contraseña de aplicación](https://myaccount.google.com/apppasswords) de esa cuenta (no la contraseña normal) |
| `CONTACT_RECIPIENT` | Opcional. Quién recibe los mensajes (por defecto, la misma cuenta) |
| `CHAT_IA_ENABLED` | Opcional. `True` activa la IA del chat (por defecto apagada) |
| `ANTHROPIC_API_KEY` | Opcional. Clave de la API de Claude, solo si se activa la IA |
| `CHAT_IA_MODEL` | Opcional. Modelo de la IA (por defecto `claude-haiku-5-5`) |
| `DJANGO_SECRET_KEY` | Opcional. Clave secreta; obligatoria en producción |
| `DJANGO_DEBUG` | Opcional. `False` en producción (por defecto `True`) |
| `DJANGO_ALLOWED_HOSTS` | Opcional. Dominios permitidos, separados por comas |

Sin credenciales de correo la web funciona igual: los mensajes del formulario se guardan en la base de datos y el correo se imprime en la terminal.

## Despliegue

El proyecto usa **despliegue continuo (CD)**: la plataforma de hosting está conectada a este repositorio y **vuelve a desplegar automáticamente cada vez que se hace `git push` a la rama `main`**. Los archivos estáticos se sirven con [WhiteNoise](https://whitenoise.readthedocs.io/).

Esa configuración vive en la plataforma de hosting, no en el repositorio. En producción hay que definir allí, como variables de entorno, `DJANGO_SECRET_KEY`, `DJANGO_DEBUG=False`, `DJANGO_ALLOWED_HOSTS` y, para el formulario de contacto, `EMAIL_HOST_USER` / `EMAIL_HOST_PASSWORD` (ver la tabla de configuración).

## Tests

Hay tres niveles de pruebas:

| Nivel | Qué comprueba | Nº |
|---|---|---|
| **Unitarias** | Piezas aisladas, sin servidor: el motor de preguntas frecuentes (normalización, puntuación, prioridad del saludo) y el saneamiento del historial del chat | 16 |
| **Integración** | Varias capas a la vez: cliente de Django → middleware y CSRF → vista → caché y base de datos → JSON; el formulario de contacto con su base de datos y su correo; y el SDK de Anthropic contra un servidor falso (**sin gastar nada**) | 41 |
| **E2E (extremo a extremo)** | Un navegador real (Chromium, con Playwright) usa la web completa como lo haría una persona | 17 |

```bash
cd web_euroforma/Web
python manage.py test                                  # unitarias + integración (57)

# E2E: instalación única y ejecución
pip install -r requirements-dev.txt && playwright install chromium
python manage.py test e2e --pattern "e2e_*.py"         # 17 pruebas en navegador real
```

**Qué cubren las E2E:** que ninguna página tenga scroll horizontal en móvil, tablet y escritorio; el menú móvil (abre sin tapar el logo, zonas táctiles, se cierra al tocar fuera o con Escape); que YouTube, Google Maps y Elfsight **no se carguen hasta aceptar las cookies**; el formulario de contacto (envío, errores y campo trampa anti-bots); el chat (botones, Enter, enlaces seguros, que el HTML escrito por el usuario no se ejecute, doble envío y errores del servidor) y la cabecera anticlickjacking.

**Cómo se usaron.** Durante el desarrollo, cada cambio de frontend o de backend se validó con pruebas E2E en un navegador real (primero como scripts sueltos, ahora consolidadas en esta suite), además de las unitarias y de integración. Para comprobar que detectan fallos de verdad, se rompió el código a propósito (cargar Elfsight sin consentimiento, volver a tapar el logo con el menú, usar `innerHTML` en el chat) y las pruebas fallaron como debían.

Las E2E requieren conexión a internet (Bootstrap se carga desde un CDN); las peticiones a YouTube, Google y Elfsight se bloquean y se registran para que las pruebas no dependan de esos servicios. Si Playwright no está instalado, se saltan con un mensaje que explica cómo instalarlo.

## Estructura

```
web_euroforma/Web/
├── manage.py
├── Web/          # configuración de Django (settings, urls)
├── inicio/       # páginas: inicio, nosotros, equipo, RSC, avisos legales…
│   ├── templates/
│   └── static/   # CSS, JS (menú, cookies, chat), imágenes, vídeos
├── contacto/     # formulario de contacto (forms, views, tests)
├── chat/         # asistente: faq.py · ia.py · limites.py · views.py · tests.py
├── e2e/          # pruebas E2E con Playwright (e2e_web.py)
└── db.sqlite3    # base de datos de ejemplo (profesores, contactos)

requirements.txt        # dependencias de la web
requirements-dev.txt    # + Playwright, solo para las pruebas E2E
```

## Panel de administración

`http://127.0.0.1:8000/admin/`. Para crear un usuario administrador:

```bash
cd web_euroforma/Web
python manage.py createsuperuser
```

## Limitaciones conocidas

- El repositorio no incluye un pipeline de integración continua (CI): los tests se ejecutan en local y el despliegue automático publica cada push sin ejecutarlos antes.
- Los mensajes del formulario de contacto se guardan en SQLite (`db.sqlite3`). En plataformas de hosting con disco efímero esa base de datos se restablece en cada despliegue; los mensajes también llegan por correo. Para producción real convendría una base de datos externa (p. ej. PostgreSQL).
- La integración con la API de Claude está verificada con un servidor simulado, no contra la API real (la IA está apagada por defecto).
- Los límites anti-abuso viven en la memoria del servidor: valen para un solo proceso; en producción habría que usar una caché compartida (p. ej. Redis).
- `run.bat` (Windows) está escrito con la misma lógica que `run.sh`, pero solo se ha probado `run.sh`.
- Las pruebas E2E se ejecutan a mano (`python manage.py test e2e …`); no hay CI que las lance automáticamente en cada push.
