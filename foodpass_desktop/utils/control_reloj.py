from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Union

UMBRAL_MINUTOS_ALERTA = 5.0
UMBRAL_SEGUNDOS_ALERTA = UMBRAL_MINUTOS_ALERTA * 60


@dataclass
class EstadoReloj:
    diferencia_segundos: float
    diferencia_minutos: float
    alerta: bool
    mensaje: str
    hora_servidor: datetime
    hora_equipo: datetime


_ULTIMO_ESTADO_RELOJ: EstadoReloj | None = None


def _a_datetime(valor: Union[datetime, str]) -> datetime:
    if isinstance(valor, datetime):
        dt = valor
    elif isinstance(valor, str):
        dt = datetime.fromisoformat(valor)
    else:
        raise TypeError("La hora debe ser datetime o cadena ISO 8601")

    if dt.tzinfo is not None:
        return dt.astimezone(timezone.utc).replace(tzinfo=None)
    return dt


def evaluar_diferencia_reloj(
    hora_servidor: Union[datetime, str],
    hora_equipo: Union[datetime, str],
    umbral_minutos: float = UMBRAL_MINUTOS_ALERTA,
) -> EstadoReloj:
    """
    Calcula la diferencia entre hora del servidor y hora del equipo.
    Si la diferencia absoluta supera el umbral (5 min por defecto), genera alerta.
    """
    global _ULTIMO_ESTADO_RELOJ

    dt_servidor = _a_datetime(hora_servidor)
    dt_equipo = _a_datetime(hora_equipo)

    diff_segundos = abs((dt_servidor - dt_equipo).total_seconds())
    diff_minutos = diff_segundos / 60.0
    umbral_seg = umbral_minutos * 60.0

    alerta = diff_segundos > umbral_seg
    if alerta:
        mensaje = (
            f"Alerta de reloj: diferencia de {diff_minutos:.2f} min "
            f"(supera el límite de {umbral_minutos:g} min entre servidor y equipo)."
        )
    else:
        mensaje = f"Reloj sincronizado: diferencia de {diff_minutos:.2f} min."

    estado = EstadoReloj(
        diferencia_segundos=diff_segundos,
        diferencia_minutos=diff_minutos,
        alerta=alerta,
        mensaje=mensaje,
        hora_servidor=dt_servidor,
        hora_equipo=dt_equipo,
    )
    _ULTIMO_ESTADO_RELOJ = estado
    return estado


def obtener_ultimo_estado_reloj() -> EstadoReloj | None:
    """Devuelve el último estado de reloj evaluado."""
    return _ULTIMO_ESTADO_RELOJ