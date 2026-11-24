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


def _como_fecha(valor):
    """Fecha y hora real de Excel (se puede ordenar y filtrar); si no, texto."""
    if isinstance(valor, datetime):
        return valor
    try:
        return datetime.strptime(str(valor)[:19], "%Y-%m-%d %H:%M:%S")
    except ValueError:
        return sanitizar_valor_exportacion(valor)


def _como_documento(valor):
    """Número de documento como número (sin el aviso verde de Excel) si son
    solo dígitos y caben sin perder precisión; si no, texto."""
    texto = str(valor or "").strip()
    if texto.isdigit() and len(texto) <= 15 and not texto.startswith("0"):
        return int(texto)
    return sanitizar_valor_exportacion(texto)


def exportar_entregas(reporte: dict, ruta: str | Path, ahora=None) -> Path:
    """RF-ES24: encabezado, detalle con filtros y totales por servicio."""
    ahora = ahora or datetime.now()
    wb = Workbook()
    ws = wb.active
    ws.title = "Entregas"
    ws.sheet_view.showGridLines = False
    linea = Side(style="thin", color="E2E8F0")
    borde = Border(left=linea, right=linea, top=linea, bottom=linea)
    zebra = PatternFill("solid", fgColor=GRIS_FONDO)
    gris = Font(color="64748B", size=10)

    ws.merge_cells("A1:E1")
    ws["A1"] = "FoodPass · Reporte de entregas del apoyo de alimentación"
    ws["A1"].font = Font(bold=True, size=15, color=VERDE_SELVA)
    ws.row_dimensions[1].height = 26
    ws.merge_cells("A2:E2")
    servicio = reporte.get("servicio") or "Todos los servicios"
    ws["A2"] = f"Periodo: {reporte['desde']} a {reporte['hasta']}  ·  {servicio}"
    ws["A2"].font = gris
    ws.merge_cells("A3:E3")
    ws["A3"] = f"Generado: {ahora:%Y-%m-%d %H:%M}  ·  SENA · CEAI · Cafetería"
    ws["A3"].font = gris

    columnas = ["Fecha y hora", "Documento", "Nombre", "Servicio", "Modalidad"]
    _encabezado_tabla(ws, 5, columnas)
    for col in range(1, len(columnas) + 1):
        ws.cell(row=5, column=col).border = borde
    ws.row_dimensions[5].height = 22

    fila = 6
    detalle = reporte["detalle"]
    for i, r in enumerate(detalle):
        valores = [
            _como_fecha(r["fecha_hora"]),
            _como_documento(r["documento"]),
            sanitizar_valor_exportacion(r["nombre"]),
            sanitizar_valor_exportacion(r["servicio"]),
            sanitizar_valor_exportacion(r["modalidad"]),
        ]
        for col, valor in enumerate(valores, start=1):
            celda = ws.cell(row=fila, column=col, value=valor)
            celda.border = borde
            celda.alignment = Alignment(horizontal="left", vertical="center")
            if i % 2:
                celda.fill = zebra
        ws.cell(row=fila, column=1).number_format = "yyyy-mm-dd hh:mm:ss"
        ws.cell(row=fila, column=2).number_format = "0"
        fila += 1
    if not detalle:
        ws.merge_cells(start_row=6, start_column=1, end_row=6, end_column=5)
        ws.cell(row=6, column=1, value="No hay entregas en el periodo.").font = gris
        fila = 7
    else:
        ws.auto_filter.ref = f"A5:E{fila - 1}"

    # Totales por servicio: tabla pequeña debajo del detalle.
    fila += 1
    _encabezado_tabla(ws, fila, ["Servicio", "Entregas"])
    for col in (1, 2):
        ws.cell(row=fila, column=col).border = borde
    fila += 1
    for servicio_nombre, total in reporte["totales"].items():
        ws.cell(row=fila, column=1, value=servicio_nombre.capitalize()).border = borde
        celda = ws.cell(row=fila, column=2, value=total)
        celda.border = borde
        celda.alignment = Alignment(horizontal="right")
        fila += 1
    verde_claro = PatternFill("solid", fgColor="E3F4E4")
    for col, valor in ((1, "Total"), (2, reporte["total"])):
        celda = ws.cell(row=fila, column=col, value=valor)
        celda.font = Font(bold=True, color="1F7A24")
        celda.fill = verde_claro
        celda.border = Border(
            left=linea, right=linea, bottom=linea, top=Side(style="medium", color="1F7A24")
        )
        if col == 2:
            celda.alignment = Alignment(horizontal="right")

    for letra, ancho in zip("ABCDE", (21, 16, 38, 14, 14)):
        ws.column_dimensions[letra].width = ancho
    ws.freeze_panes = "A6"
    ws.print_title_rows = "5:5"
    ws.page_setup.orientation = "landscape"
    ws.page_setup.fitToWidth = 1
    ws.page_setup.fitToHeight = 0
    ws.sheet_properties.pageSetUpPr.fitToPage = True
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
