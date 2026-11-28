"""Parámetros locales del equipo (RF-ES07 · D-33).

Se leen del archivo .env que acompaña al ejecutable. Si falta un valor o no
es válido, se usa el valor por defecto.
"""

import os
import sys
from pathlib import Path

MINUTOS_BLOQUEO_POR_DEFECTO = 5
RACIONES_POR_DEFECTO = {"desayuno": 100, "almuerzo": 125, "refrigerio": 100}
PORCENTAJE_ALERTA_POR_DEFECTO = 80


def carpeta_aplicacion() -> Path:
    """Carpeta donde está el ejecutable (o la raíz del proyecto en desarrollo)."""
    if getattr(sys, "frozen", False):
        return Path(sys.executable).resolve().parent
    return Path(__file__).resolve().parents[2]


def cargar_env():
    """Carga el .env de la carpeta de la aplicación."""
    if os.getenv("FOODPASS_SIN_ENV"):
        return
    try:
        from dotenv import load_dotenv
    except ImportError:
        return
    ruta = carpeta_aplicacion() / ".env"
    if ruta.exists():
        load_dotenv(ruta, override=True)


def _numero(nombre, por_defecto, minimo=0.0):
    valor = os.getenv(nombre, "").strip().replace(",", ".")
    try:
        numero = float(valor)
    except ValueError:
        return por_defecto
    return numero if numero > minimo else por_defecto


def minutos_bloqueo():
    """Minutos sin actividad antes de bloquear la pantalla y pedir el PIN."""
    return _numero("BLOQUEO_MINUTOS", MINUTOS_BLOQUEO_POR_DEFECTO)


def raciones_previstas():
    """RN03: referencia para alertar; nunca limita la entrega."""
    return {
        s: int(_numero(f"RACIONES_{s.upper()}", v))
        for s, v in RACIONES_POR_DEFECTO.items()
    }


def porcentaje_alerta():
    return int(_numero("ALERTA_PORCENTAJE", PORCENTAJE_ALERTA_POR_DEFECTO))
