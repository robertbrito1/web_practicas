@echo off
REM Arranca el proyecto con un solo comando (Windows):
REM   run.bat          -> http://127.0.0.1:8000
REM   run.bat 8080     -> http://127.0.0.1:8080
cd /d "%~dp0"
if "%~1"=="" (set PORT=8000) else (set PORT=%~1)

if not exist .venv (
  echo ^>^> Creando entorno virtual .venv ...
  py -m venv .venv
)
call .venv\Scripts\activate

echo ^>^> Instalando dependencias...
pip install -q -r requirements.txt

if not exist .env (
  copy .env.example .env >nul
  echo ^>^> Creado .env desde .env.example
)

cd web_euroforma\Web
echo ^>^> Aplicando migraciones...
python manage.py migrate --noinput

echo ^>^> Servidor en http://127.0.0.1:%PORT%  (Ctrl+C para parar)
python manage.py runserver %PORT%
