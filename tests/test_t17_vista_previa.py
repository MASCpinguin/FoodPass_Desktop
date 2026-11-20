import csv
import time

import pytest

from foodpass_desktop.services.importacion_beneficiarios_service import (
    aplicar_vista_previa_importacion,
    generar_vista_previa_importacion,
)


def _crear_csv(ruta, filas: list[list[str]]) -> None:
    with ruta.open("w", encoding="utf-8", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(["numero_documento", "nombre_completo", "email", "estado"])
        writer.writerows(filas)


def test_vista_previa_clasifica_altas_cambios_bajas_y_errores(tmp_path):
    actuales = [
        {
            "numero_documento": "1001",
            "nombre_completo": "Ana Maria Lopez",
            "email": "ana@sena.edu.co",
            "estado": "activo",
        },
        {
            "numero_documento": "1002",
            "nombre_completo": "Carlos Perez",
            "email": "carlos@sena.edu.co",
            "estado": "activo",
        },
        {
            "numero_documento": "1003",
            "nombre_completo": "Laura Gomez",
            "email": "laura@sena.edu.co",
            "estado": "activo",
        },
    ]

    archivo = tmp_path / "importacion.csv"
    _crear_csv(
        archivo,
        [
            ["1001", "Ana Maria Lopez", "ana@sena.edu.co", "inactivo"],
            ["1002", "Carlos Perez", "carlos@sena.edu.co", "activo"],
            ["1004", "Diego Ruiz", "diego@sena.edu.co", "activo"],
            ["1005", "=cmd|'/C calc'!A0", "bad@sena.edu.co", "activo"],
            ["1006", "Sofia Torres", "sofia@sena.edu.co", "suspendido"],
            ["1004", "Diego Duplicado", "diego2@sena.edu.co", "activo"],
        ],
    )

    vista = generar_vista_previa_importacion(archivo, actuales)

    assert vista.conteos == {
        "altas": 1,
        "cambios": 1,
        "bajas": 1,
        "errores": 3,
    }
    assert vista.altas[0]["numero_documento"] == "1004"
    assert vista.cambios[0]["numero_documento"] == "1001"
    assert vista.bajas[0]["numero_documento"] == "1003"
    assert [e.fila for e in vista.errores] == [5, 6, 7]


def test_no_aplica_sin_confirmacion_y_respeta_interruptor_de_bajas(tmp_path):
    actuales = [
        {
            "numero_documento": "2001",
            "nombre_completo": "Uno",
            "email": "",
            "estado": "activo",
        },
        {
            "numero_documento": "2002",
            "nombre_completo": "Dos",
            "email": "",
            "estado": "activo",
        },
    ]
    archivo = tmp_path / "solo_uno.csv"
    _crear_csv(archivo, [["2001", "Uno", "", "activo"]])

    vista = generar_vista_previa_importacion(archivo, actuales)
    assert vista.conteos["bajas"] == 1

    with pytest.raises(PermissionError):
        aplicar_vista_previa_importacion(vista, actuales, confirmado=False)

    sin_bajas = aplicar_vista_previa_importacion(
        vista, actuales, confirmado=True, aplicar_bajas=False
    )
    por_doc_sin_bajas = {b["numero_documento"]: b for b in sin_bajas}
    assert por_doc_sin_bajas["2002"]["estado"] == "activo"

    con_bajas = aplicar_vista_previa_importacion(
        vista, actuales, confirmado=True, aplicar_bajas=True
    )
    por_doc_con_bajas = {b["numero_documento"]: b for b in con_bajas}
    assert por_doc_con_bajas["2002"]["estado"] == "inactivo"


def test_exige_confirmacion_explicita_si_hay_errores(tmp_path):
    archivo = tmp_path / "con_error.csv"
    _crear_csv(
        archivo,
        [
            ["3001", "Valido", "", "activo"],
            ["", "Sin Documento", "", "activo"],
        ],
    )

    vista = generar_vista_previa_importacion(archivo, [])
    assert vista.conteos["errores"] == 1

    with pytest.raises(ValueError):
        aplicar_vista_previa_importacion(
            vista,
            [],
            confirmado=True,
            confirmar_omitir_errores=False,
        )

    resultado = aplicar_vista_previa_importacion(
        vista,
        [],
        confirmado=True,
        confirmar_omitir_errores=True,
    )
    assert len(resultado) == 1
    assert resultado[0]["numero_documento"] == "3001"


def test_rendimiento_vista_previa_mil_filas(tmp_path):
    filas = [
        [str(10000 + i), f"Beneficiario {i}", f"b{i}@sena.edu.co", "activo"]
        for i in range(1000)
    ]
    archivo = tmp_path / "mil_filas.csv"
    _crear_csv(archivo, filas)

    inicio = time.perf_counter()
    vista = generar_vista_previa_importacion(archivo, [])
    duracion = time.perf_counter() - inicio

    assert vista.conteos["altas"] == 1000
    assert duracion < 60.0
