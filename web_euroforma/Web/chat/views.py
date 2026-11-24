import json
import logging
import re

from django.http import JsonResponse
from django.views.decorators.http import require_POST

from . import faq, ia, limites

logger = logging.getLogger(__name__)

MAX_MENSAJE = 500          # caracteres por mensaje del usuario
MAX_RESPUESTA_HISTORIAL = 1500
MAX_HISTORIAL = 6          # mensajes anteriores que se tienen en cuenta
MAX_BODY = 20_000          # bytes de la petición

_CONTROL = re.compile(r"[\x00-\x08\x0b\x0c\x0e-\x1f\x7f]")  # caracteres de control (salvo \n y \t)


def _json(datos: dict, estado: int = 200) -> JsonResponse:
    respuesta = JsonResponse(datos, status=estado, json_dumps_params={"ensure_ascii": False})
    respuesta["Cache-Control"] = "no-store"
    return respuesta


def _error(mensaje: str, estado: int) -> JsonResponse:
    # "reply" también va en los errores para que el widget siempre tenga algo que mostrar.
    return _json({"error": mensaje, "reply": mensaje, "source": "error", "suggestions": []}, estado)


def _limpiar(texto, maximo: int):
    if not isinstance(texto, str):
        return None
    texto = _CONTROL.sub("", texto).strip()
    return texto[:maximo] if texto else None


def _sanear_historial(bruto) -> list:
    """Solo roles válidos, textos acotados, a lo sumo MAX_HISTORIAL y empezando por 'user'."""
    if not isinstance(bruto, list):
        return []
    limpio = []
    for item in bruto:  # el tamaño total ya está acotado por MAX_BODY
        if not isinstance(item, dict) or item.get("role") not in ("user", "assistant"):
            continue
        maximo = MAX_MENSAJE if item["role"] == "user" else MAX_RESPUESTA_HISTORIAL
        contenido = _limpiar(item.get("content"), maximo)
        if contenido:
            limpio.append({"role": item["role"], "content": contenido})
    limpio = limpio[-MAX_HISTORIAL:]  # primero se filtra y luego se recorta: la basura no expulsa mensajes válidos
    while limpio and limpio[0]["role"] != "user":
        limpio.pop(0)
    return limpio


@require_POST
def chat(request):
    """POST /api/chat/  {"message": "...", "history": [...]}  ->  {"reply", "source", "suggestions"}"""
    if len(request.body) > MAX_BODY:
        return _error("La petición es demasiado grande.", 413)

    try:
        datos = json.loads(request.body.decode("utf-8"))
    except (ValueError, UnicodeDecodeError):
        return _error("Petición no válida.", 400)
    if not isinstance(datos, dict):
        return _error("Petición no válida.", 400)

    mensaje = _limpiar(datos.get("message"), MAX_MENSAJE)
    if mensaje is None:
        return _error("Escribe tu pregunta (máximo %d caracteres)." % MAX_MENSAJE, 400)

    if not limites.mensaje_permitido(request):
        return _error("Has enviado muchos mensajes seguidos. Espera unos minutos e inténtalo de nuevo.", 429)

    # 1) Preguntas frecuentes: gratis y sin red.
    respuesta = faq.responder(mensaje)
    if respuesta is not None:
        return _json({"reply": respuesta.texto, "source": "faq", "suggestions": list(respuesta.sugerencias)})

    # 2) IA (apagada por defecto): solo si está habilitada y quedan llamadas disponibles.
    if ia.disponible() and limites.ia_permitida(request):
        try:
            texto = ia.responder(_sanear_historial(datos.get("history")), mensaje)
            return _json({"reply": texto, "source": "ia", "suggestions": list(faq.SUGERENCIAS_GENERALES)})
        except ia.IAError:
            pass  # ya está registrado en ia.py; se responde con el mensaje de reserva

    # 3) Reserva: derivar a una persona.
    return _json({
        "reply": faq.MENSAJE_SIN_RESPUESTA,
        "source": "fallback",
        "suggestions": list(faq.SUGERENCIAS_INICIALES),
    })
