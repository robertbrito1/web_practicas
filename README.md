# Web Euroformac

Prácticas de la FP DAM: página web de Euroformac. Backend con **Django**; frontend con HTML y CSS, animaciones con JavaScript y Bootstrap.

## Requisitos

- Python 3.10 o superior
- Git

## Arrancar el proyecto (1 comando)

```bash
git clone https://github.com/robertbrito1/web_practicas.git
cd web_practicas
./run.sh          # Linux / macOS
run.bat           # Windows
```

El script crea el entorno virtual, instala las dependencias, aplica las migraciones y levanta el servidor en **http://127.0.0.1:8000**. Para usar otro puerto: `./run.sh 8080`.

### Paso a paso (manual)

```bash
python3 -m venv .venv
source .venv/bin/activate          # Windows: .venv\Scripts\activate
pip install -r requirements.txt
cp .env.example .env               # Windows: copy .env.example .env
cd web_euroforma/Web
python manage.py migrate
python manage.py runserver
```

## Configuración (.env)

Los valores que cambian de un equipo a otro van en un archivo `.env` en la raíz del repositorio (no se sube a git). Hay una plantilla en `.env.example`.

| Variable | Para qué sirve |
|---|---|
| `EMAIL_HOST_USER` | Cuenta de Gmail que envía los mensajes del formulario de contacto |
| `EMAIL_HOST_PASSWORD` | [Contraseña de aplicación](https://myaccount.google.com/apppasswords) de esa cuenta (no la contraseña normal) |
| `DJANGO_SECRET_KEY` | Opcional. Clave secreta; obligatoria en producción |
| `DJANGO_DEBUG` | Opcional. `False` en producción (por defecto `True`) |
| `DJANGO_ALLOWED_HOSTS` | Opcional. Dominios permitidos, separados por comas |

Sin correo configurado la web funciona igual; solo falla el envío de emails del formulario de contacto.

## Estructura

```
web_euroforma/Web/
├── manage.py
├── Web/          # configuración de Django (settings, urls)
├── inicio/       # páginas: inicio, nosotros, equipo, RSC, avisos legales...
│   ├── templates/
│   └── static/   # CSS, JS, imágenes, vídeos
├── contacto/     # formulario de contacto
└── db.sqlite3    # base de datos de ejemplo (profesores, contactos)
```

## Panel de administración

`http://127.0.0.1:8000/admin/`. Para crear un usuario administrador:

```bash
cd web_euroforma/Web
python manage.py createsuperuser
```
