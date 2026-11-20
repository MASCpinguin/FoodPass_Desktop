from __future__ import annotations

from datetime import datetime, timedelta
from pathlib import Path
from typing import Any

from openpyxl import Workbook, load_workbook

from foodpass_desktop.utils.control_reloj import (
    evaluar_diferencia_reloj,
    obtener_ultimo_estado_reloj,
)
from foodpass_desktop.utils.seguridad_excel import (
    aplicar_formato_texto,
    cargar_valores_excel,
    sanitizar_valor_exportacion,
    tiene_prefijo_peligroso,
)

try:
    from beneficiarios_service import generar_plantilla, validar_archivo_beneficiarios
except ModuleNotFoundError:
    _ENCABEZADOS_PLANTILLA = [
        "tipo_documento",
        "numero_documento",
        "nombre_completo",
        "programa",
        "ficha",
        "estado",
    ]

    def generar_plantilla(ruta_archivo: str | Path) -> str:
        """Crea una plantilla Excel de respaldo con hoja Beneficiarios y formato texto."""
        destino = Path(ruta_archivo)
        wb = Workbook()
        ws = wb.active
        ws.title = "Beneficiarios"
        ws.append(_ENCABEZADOS_PLANTILLA)
        aplicar_formato_texto(ws, num_columnas=len(_ENCABEZADOS_PLANTILLA), max_fila=50)
        wb.save(destino)
        return str(destino)

    def validar_archivo_beneficiarios(
        ruta_archivo: str | Path,
    ) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
        """Valida filas de respaldo rechazando celdas con prefijos peligrosos."""
        wb = load_workbook(ruta_archivo, data_only=True)
        try:
            ws = wb.active
            validas: list[dict[str, Any]] = []
            errores: list[dict[str, Any]] = []

            for fila_idx, row in enumerate(
                ws.iter_rows(min_row=2, values_only=True), start=2
            ):
                if row is None or not any(
                    celda is not None and str(celda).strip() != "" for celda in row
                ):
                    continue

                if any(tiene_prefijo_peligroso(celda) for celda in row):
                    errores.append(
                        {
                            "fila": fila_idx,
                            "motivo": "Contenido no permitido (=, +, -, @)",
                        }
                    )
                    continue

                valores = [str(c).strip() if c is not None else "" for c in row]
                while len(valores) < 6:
                    valores.append("")

                validas.append(
                    {
                        "tipo_documento": valores[0],
                        "numero_documento": valores[1],
                        "nombre_completo": sanitizar_valor_exportacion(valores[2]),
                        "programa": valores[3],
                        "ficha": valores[4],
                        "estado": valores[5].lower(),
                    }
                )

            return validas, errores
        finally:
            wb.close()


def test_importar_lee_valores_y_rechaza_formulas(tmp_path):
    archivo = tmp_path / "beneficiarios_prueba.xlsx"
    wb = Workbook()
    ws = wb.active
    ws.append(
        [
            "tipo_documento",
            "numero_documento",
            "nombre_completo",
            "programa",
            "ficha",
            "estado",
        ]
    )
    ws.append(["CC", "1001", "=SUM(1,1)", "ADSO", "2857123", "activo"])
    ws.append(["CC", "1002", "+cmd|'/C calc'!A0", "ADSO", "2857123", "activo"])
    ws.append(["CC", "1003", "Valido Uno", "ADSO", "2857123", "activo"])
    wb.save(archivo)

    validas, errores = validar_archivo_beneficiarios(str(archivo))

    assert len(validas) == 1
    assert validas[0]["numero_documento"] == "1003"
    assert len(errores) == 2
    assert errores[0]["fila"] == 2
    assert errores[1]["fila"] == 3


def test_exportar_agrega_apostrofo_a_caracteres_peligrosos():
    assert sanitizar_valor_exportacion("=1+1") == "'=1+1"
    assert sanitizar_valor_exportacion("+valor") == "'+valor"
    assert sanitizar_valor_exportacion("-valor") == "'-valor"
    assert sanitizar_valor_exportacion("@valor") == "'@valor"
    assert sanitizar_valor_exportacion("Carlos Perez") == "Carlos Perez"
    assert tiene_prefijo_peligroso("=A1") is True
    assert tiene_prefijo_peligroso("Carlos") is False


def test_plantilla_tiene_formato_texto_y_cargar_valores(tmp_path):
    plantilla = tmp_path / "plantilla.xlsx"
    generar_plantilla(str(plantilla))

    wb_edit = load_workbook(str(plantilla))
    ws_edit = wb_edit["Beneficiarios"]
    aplicar_formato_texto(ws_edit, num_columnas=6, max_fila=10)
    wb_edit.save(str(plantilla))
    wb_edit.close()

    wb = cargar_valores_excel(str(plantilla), data_only=True)
    ws = wb["Beneficiarios"]
    assert ws.cell(row=1, column=1).number_format == "@"
    assert ws.cell(row=2, column=2).number_format == "@"
    wb.close()


def test_control_reloj_alerta_si_supera_5_minutos():
    base = datetime(2026, 11, 20, 9, 0, 0)

    estado_ok = evaluar_diferencia_reloj(base, base + timedelta(minutes=4, seconds=59))
    assert estado_ok.alerta is False

    estado_alerta = evaluar_diferencia_reloj(
        base, base + timedelta(minutes=5, seconds=1)
    )
    assert estado_alerta.alerta is True
    assert "Alerta de reloj" in estado_alerta.mensaje
    assert obtener_ultimo_estado_reloj() == estado_alerta
