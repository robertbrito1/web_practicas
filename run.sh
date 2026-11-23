#!/usr/bin/env bash
# Arranca el proyecto con un solo comando (Linux / macOS):
#   ./run.sh          -> http://127.0.0.1:8000
#   ./run.sh 8080     -> http://127.0.0.1:8080
set -e
cd "$(dirname "$0")"
PORT="${1:-8000}"

if [ ! -d .venv ]; then
  echo ">> Creando entorno virtual (.venv)..."
  python3 -m venv .venv
fi
# shellcheck disable=SC1091
. .venv/bin/activate

echo ">> Instalando dependencias..."
pip install -q -r requirements.txt

if [ ! -f .env ]; then
  cp .env.example .env
  echo ">> Creado .env desde .env.example (rellena el correo si quieres que el formulario envíe emails)"
fi

cd web_euroforma/Web
echo ">> Aplicando migraciones..."
python manage.py migrate --noinput

echo ">> Servidor en http://127.0.0.1:${PORT}  (Ctrl+C para parar)"
python manage.py runserver "${PORT}"
