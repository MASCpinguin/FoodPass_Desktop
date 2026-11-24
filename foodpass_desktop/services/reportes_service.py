"""Archivos Excel del escritorio: reporte de entregas (RF-ES24) y plantilla de
beneficiarios (RF-ES27). Sin Qt: las pantallas solo eligen la ruta.
"""

from datetime import datetime
from pathlib import Path

from openpyxl import Workbook
from openpyxl.styles import Alignment, Border, Font, PatternFill, Side

from foodpass_desktop.utils.seguridad_excel import (
    aplicar_formato_texto,
    sanitizar_valor_exportacion,
)

VERDE_SELVA = "283618"
GRIS_FONDO = "F8F9FA"
COLUMNAS_PLANTILLA = ["numero_documento", "nombre_completo", "email", "estado"]
_BORDE = Border(bottom=Side(style="thin", color="E2E8F0"))


def nombre_archivo(reporte: str, ahora=None) -> str:
    """C-17: FoodPass_<Reporte>_AAAA-MM-DD_HHMM.xlsx"""
    ahora = ahora or datetime.now()
    return f"FoodPass_{reporte}_{ahora:%Y-%m-%d_%H%M}.xlsx"


def _encabezado_tabla(ws, fila, columnas):
    for col, texto in enumerate(columnas, start=1):
        celda = ws.cell(row=fila, column=col, value=texto)
        celda.font = Font(bold=True, color="FFFFFF")
        celda.fill = PatternFill("solid", fgColor=VERDE_SELVA)
        celda.alignment = Alignment(vertical="center")


def exportar_entregas(reporte: dict, ruta: str | Path, ahora=None) -> Path:
    """Escribe encabezado, detalle y totales por servicio."""
    ahora = ahora or datetime.now()
    wb = Workbook()
    ws = wb.active
    ws.title = "Entregas"
    ws["A1"] = "FoodPass · Reporte de entregas del apoyo de alimentación"
    ws["A1"].font = Font(bold=True, size=14, color=VERDE_SELVA)
    ws["A2"] = f"Periodo: {reporte['desde']} a {reporte['hasta']}"
    ws["A3"] = f"Generado: {ahora:%Y-%m-%d %H:%M}"
    columnas = ["Fecha y hora", "Documento", "Nombre", "Servicio", "Modalidad"]
    _encabezado_tabla(ws, 5, columnas)
    fila = 6
    for r in reporte["detalle"]:
        valores = [
            r["fecha_hora"],
            r["documento"],
            r["nombre"],
            r["servicio"],
            r["modalidad"],
        ]
        for col, valor in enumerate(valores, start=1):
            celda = ws.cell(
                row=fila, column=col, value=sanitizar_valor_exportacion(valor)
            )
            celda.border = _BORDE
        fila += 1
    fila += 1
    ws.cell(row=fila, column=1, value="Totales por servicio").font = Font(
        bold=True, color=VERDE_SELVA
    )
    fila += 1
    for servicio, total in reporte["totales"].items():
        ws.cell(row=fila, column=1, value=servicio.capitalize())
        ws.cell(row=fila, column=2, value=total)
        fila += 1
    ws.cell(row=fila, column=1, value="Total").font = Font(bold=True)
    ws.cell(row=fila, column=2, value=reporte["total"]).font = Font(bold=True)
    for letra, ancho in zip("ABCDE", (22, 16, 36, 14, 12)):
        ws.column_dimensions[letra].width = ancho
    ws.freeze_panes = "A6"
    ruta = Path(ruta)
    wb.save(ruta)
    return ruta


def crear_plantilla_beneficiarios(ruta: str | Path, beneficiarios=None) -> Path:
    """RF-ES27: plantilla con la lista actual de beneficiarios.

    Trae los beneficiarios que ya están en la base para que el operador agregue
    filas, corrija datos o cambie el estado y vuelva a importar: lo que no cambia
    no genera movimientos en la vista previa. Sin lista, queda solo el encabezado.
    """
    from openpyxl.worksheet.datavalidation import DataValidation

    filas = list(beneficiarios or [])
    wb = Workbook()
    ws = wb.active
    ws.title = "Beneficiarios"
    aplicar_formato_texto(ws, len(COLUMNAS_PLANTILLA), max(500, len(filas) + 200))
    _encabezado_tabla(ws, 1, COLUMNAS_PLANTILLA)
    for i, b in enumerate(filas, start=2):
        valores = (
            b.get("numero_documento", ""),
            b.get("nombre_completo", ""),
            b.get("email", ""),
            b.get("estado", "activo"),
        )
        for col, valor in enumerate(valores, start=1):
            ws.cell(row=i, column=col, value=str(valor or ""))
    for letra, ancho in zip("ABCD", (20, 36, 34, 12)):
        ws.column_dimensions[letra].width = ancho
    ws.freeze_panes = "A2"
    estado = DataValidation(
        type="list",
        formula1='"activo,inactivo"',
        allow_blank=True,
        errorTitle="Estado no válido",
        error="Escribe activo o inactivo.",
    )
    ws.add_data_validation(estado)
    estado.add(f"D2:D{max(500, len(filas) + 200)}")
    ayuda = wb.create_sheet("Instrucciones")
    for fila in (
        ["Cómo usar la hoja «Beneficiarios»"],
        [
            "Qué trae",
            "La lista actual de beneficiarios. Agrega filas al final, corrige datos "
            "o cambia el estado, guarda y usa «Importar archivo».",
        ],
        [
            "numero_documento",
            "Solo números, sin puntos ni espacios. Obligatorio y sin repetir.",
        ],
        ["nombre_completo", "Nombre y apellidos."],
        ["email", "Correo del aprendiz. Obligatorio y sin repetir."],
        ["estado", "activo o inactivo (lista desplegable)."],
        [
            "Bajas",
            "Si borras una fila, esa persona solo queda inactiva si marcas "
            "«Aplicar bajas» en la vista previa.",
        ],
        ["Importante", "No escribas celdas que empiecen por =, +, - o @: se rechazan."],
        [],
        ["Ejemplo de fila"],
        ["1001001100", "Ana Gómez", "aprendiz1@soy.sena.edu.co", "activo"],
    ):
        ayuda.append(fila)
    ayuda["A1"].font = Font(bold=True, color=VERDE_SELVA)
    ayuda["A10"].font = Font(bold=True, color=VERDE_SELVA)
    ayuda.column_dimensions["A"].width = 22
    ayuda.column_dimensions["B"].width = 70
    ayuda.column_dimensions["C"].width = 30
    ruta = Path(ruta)
    wb.save(ruta)
    return ruta
