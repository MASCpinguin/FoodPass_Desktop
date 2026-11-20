"""Parámetros locales del equipo (RF-ES07).

Mientras la pantalla Configuración (T33) no exista, se leen del archivo .env.
"""

import os

MINUTOS_BLOQUEO_POR_DEFECTO = 5


def minutos_bloqueo():
    """Minutos sin actividad antes de bloquear la pantalla y pedir el PIN."""
    valor = os.getenv("BLOQUEO_MINUTOS", "").strip().replace(",", ".")
    try:
        minutos = float(valor)
    except ValueError:
        return MINUTOS_BLOQUEO_POR_DEFECTO
    return minutos if minutos > 0 else MINUTOS_BLOQUEO_POR_DEFECTO
