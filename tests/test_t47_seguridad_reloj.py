from datetime import datetime, timedelta

from openpyxl import Workbook

from beneficiarios_service import generar_plantilla, validar_archivo_beneficiarios
from foodpass_desktop.utils.control_reloj import (
    evaluar_diferencia_reloj,
    obtener_ultimo_estado_reloj,
)
from foodpass_desktop.utils.seguridad_excel import (
    cargar_valores_excel,
    sanitizar_valor_exportacion,
    tiene_prefijo_peligroso,
)


def test_importar_lee_valores_y_rechaza_formulas(tmp_path):
    archivo = tmp_path / "beneficiarios_prueba.xlsx"
    wb = Workbook()
    ws = wb.active
    ws.append(["tipo_documento", "numero_documento", "nombre_completo", "programa", "ficha", "estado"])
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

    wb = cargar_valores_excel(str(plantilla), data_only=True)
    ws = wb["Beneficiarios"]
    assert ws.cell(row=1, column=1).number_format == "@"
    assert ws.cell(row=2, column=2).number_format == "@"


def test_control_reloj_alerta_si_supera_5_minutos():
    base = datetime(2026, 11, 20, 9, 0, 0)

    estado_ok = evaluar_diferencia_reloj(base, base + timedelta(minutes=4, seconds=59))
    assert estado_ok.alerta is False

    estado_alerta = evaluar_diferencia_reloj(base, base + timedelta(minutes=5, seconds=1))
    assert estado_alerta.alerta is True
    assert "Alerta de reloj" in estado_alerta.mensaje
    assert obtener_ultimo_estado_reloj() == estado_alerta