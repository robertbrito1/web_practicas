"""
Límites anti-abuso del chat (contadores en la caché de Django).

Dos niveles:
  - Mensajes en general (el FAQ es gratis, así que el límite es generoso).
  - Llamadas a la IA (cuestan dinero): por visitante y un tope global diario.

Los contadores viven en la memoria del servidor: se reinician si éste se reinicia y,
con varios procesos, cada uno cuenta por separado. Para producción habría que usar
una caché compartida (Redis, base de datos...).
"""
from django.core.cache import cache

VENTANA_SEGUNDOS = 600          # 10 minutos
DIA_SEGUNDOS = 86400

LIMITE_MENSAJES_IP = 30         # mensajes por visitante cada 10 minutos
LIMITE_IA_IP = 6                # llamadas a la IA por visitante cada 10 minutos
LIMITE_IA_DIA = 300             # llamadas a la IA en total al día


def ip_cliente(request) -> str:
    # REMOTE_ADDR y no X-Forwarded-For: esta última cabecera la puede falsificar el cliente.
    return request.META.get("REMOTE_ADDR", "desconocida")


def contar(clave: str, ventana: int) -> int:
    """Suma 1 al contador de `clave` (caduca a los `ventana` segundos) y devuelve el total."""
    if cache.add(clave, 1, ventana):
        return 1
    try:
        return cache.incr(clave)
    except ValueError:  # caducó justo ahora
        cache.set(clave, 1, ventana)
        return 1


def mensaje_permitido(request) -> bool:
    return contar(f"chat:msg:{ip_cliente(request)}", VENTANA_SEGUNDOS) <= LIMITE_MENSAJES_IP


def ia_permitida(request) -> bool:
    if contar(f"chat:ia:{ip_cliente(request)}", VENTANA_SEGUNDOS) > LIMITE_IA_IP:
        return False
    return contar("chat:ia:global", DIA_SEGUNDOS) <= LIMITE_IA_DIA
