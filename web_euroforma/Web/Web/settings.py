"""
Django settings for Web project.

Configuración pensada para clonar y ejecutar sin pasos manuales extra:
los valores que cambian entre equipos (claves, correo, debug) se leen de
un archivo .env en la raíz del repositorio (ver .env.example).
"""
import os
from pathlib import Path


# Rutas base: BASE_DIR es la carpeta donde está manage.py
BASE_DIR = Path(__file__).resolve().parent.parent
REPO_ROOT = BASE_DIR.parent.parent


# --- Variables de entorno (.env) -------------------------------------------
# Carga REPO_ROOT/.env si existe, sin necesitar librerías extra.
# Las variables ya definidas en el sistema tienen prioridad.
_env_file = REPO_ROOT / ".env"
if _env_file.exists():
    for _line in _env_file.read_text(encoding="utf-8").splitlines():
        _line = _line.strip()
        if _line and not _line.startswith("#") and "=" in _line:
            _k, _v = _line.split("=", 1)
            os.environ.setdefault(_k.strip(), _v.strip().strip('"').strip("'"))


def _env_bool(name, default):
    return os.environ.get(name, str(default)).strip().lower() in ("1", "true", "yes", "on")


# --- Seguridad ---------------------------------------------------------------
# En producción define DJANGO_SECRET_KEY y DJANGO_DEBUG=False en el .env.
SECRET_KEY = os.environ.get(
    "DJANGO_SECRET_KEY",
    "django-insecure-solo-para-desarrollo-local-cambiar-en-produccion",
)

DEBUG = _env_bool("DJANGO_DEBUG", True)

# Lista separada por comas, p. ej. "midominio.com,www.midominio.com"
ALLOWED_HOSTS = [
    h.strip() for h in os.environ.get("DJANGO_ALLOWED_HOSTS", "*").split(",") if h.strip()
]

CSRF_TRUSTED_ORIGINS = [
    'http://localhost:8000',
    'https://localhost:8000',
    'http://127.0.0.1:8000',
    'https://127.0.0.1:8000',
]

# Solo esta misma web puede incrustar sus páginas en un iframe (evita clickjacking).
X_FRAME_OPTIONS = 'SAMEORIGIN'


# --- Aplicaciones ---------------------------------------------------------------
INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'Web',
    'inicio',
    'contacto',
]

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'whitenoise.middleware.WhiteNoiseMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

ROOT_URLCONF = 'Web.urls'

# Las plantillas se buscan en la carpeta templates/ de cada app (APP_DIRS).
TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
            ],
        },
    },
]

WSGI_APPLICATION = 'Web.wsgi.application'


# --- Base de datos -------------------------------------------------------------
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': BASE_DIR / 'db.sqlite3',
    }
}

AUTH_PASSWORD_VALIDATORS = [
    {'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator'},
    {'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator'},
    {'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator'},
    {'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator'},
]


# --- Internacionalización --------------------------------------------------------
LANGUAGE_CODE = 'en-us'
TIME_ZONE = 'UTC'
USE_I18N = True
USE_TZ = True


# --- Archivos estáticos -----------------------------------------------------------
# Los CSS/JS/imágenes viven en inicio/static y Django los encuentra solo porque
# 'inicio' está en INSTALLED_APPS. STATIC_ROOT es el destino de collectstatic
# (necesario si se despliega con WhiteNoise).
STATIC_URL = '/static/'
STATIC_ROOT = BASE_DIR / 'staticfiles'

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'


# --- Correo (formulario de contacto) --------------------------------------------
# Usuario y contraseña de aplicación de Gmail se definen en el .env.
EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'
EMAIL_HOST = 'smtp.gmail.com'
EMAIL_PORT = 587
EMAIL_USE_TLS = True
EMAIL_HOST_USER = os.environ.get("EMAIL_HOST_USER", "")
EMAIL_HOST_PASSWORD = os.environ.get("EMAIL_HOST_PASSWORD", "")
EMAIL_TIMEOUT = 10  # segundos: evita que un fallo de SMTP deje colgada la petición
DEFAULT_FROM_EMAIL = EMAIL_HOST_USER or "webmaster@localhost"

# Quién recibe los mensajes del formulario de contacto (por defecto, la cuenta que envía).
CONTACT_RECIPIENT = os.environ.get("CONTACT_RECIPIENT") or EMAIL_HOST_USER or "webmaster@localhost"

# Sin credenciales (p. ej. recién clonado) los correos se imprimen en la terminal.
if not EMAIL_HOST_USER:
    EMAIL_BACKEND = 'django.core.mail.backends.console.EmailBackend'

# Las peticiones no necesitan subir archivos: se limita el tamaño del cuerpo (100 KB).
DATA_UPLOAD_MAX_MEMORY_SIZE = 100 * 1024


# --- Crispy forms -----------------------------------------------------------------
CRISPY_ALLOWED_TEMPLATE_PACKS = "bootstrap4"
CRISPY_TEMPLATE_PACK = 'bootstrap4'
