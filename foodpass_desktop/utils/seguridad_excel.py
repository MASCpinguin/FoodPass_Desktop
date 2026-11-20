from __future__ import annotations

from typing import Any
import openpyxl
from openpyxl.utils import get_column_letter

PREFIJOS_PELIGROSOS = ("=", "+", "-", "@")


def tiene_prefijo_peligroso(valor: Any) -> bool:
    """Devuelve True si el valor (como texto) inicia con =, +, - o @."""
    if valor is None:
        return False
    texto = str(valor).lstrip()
    return texto.startswith(PREFIJOS_PELIGROSOS)


def sanitizar_valor_exportacion(valor: Any) -> Any:
    """Prefija con apóstrofo (') si el texto inicia con =, +, - o @."""
    if valor is None:
        return ""
    if isinstance(valor, str):
        limpio = valor.lstrip()
        if limpio.startswith(PREFIJOS_PELIGROSOS) and not valor.startswith("'"):
            return f"'{valor}"
    return valor


def aplicar_formato_texto(ws, num_columnas: int, max_fila: int = 1000) -> None:
    """Configura las columnas y filas indicadas con formato de texto ('@')."""
    for col_idx in range(1, num_columnas + 1):
        letra_col = get_column_letter(col_idx)
        ws.column_dimensions[letra_col].number_format = "@"
        for fila_idx in range(1, max_fila + 1):
            ws.cell(row=fila_idx, column=col_idx).number_format = "@"


def cargar_valores_excel(ruta_archivo: str, data_only: bool = True):
    """Abre un libro de Excel leyendo valores calculados (data_only=True por defecto)."""
    return openpyxl.load_workbook(ruta_archivo, data_only=data_only)