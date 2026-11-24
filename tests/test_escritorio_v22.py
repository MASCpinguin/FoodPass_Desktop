"""Pruebas de las piezas de la v2.2: beneficiarios, reportes, alertas y la
integración con MySQL (esta última solo corre si el .env trae DB_HOST)."""

import os

import openpyxl
import pytest

from foodpass_desktop.services import beneficiarios_service as ben
from foodpass_desktop.services import reportes_service as rep
from foodpass_desktop.services.importacion_beneficiarios_service import (
    VistaPreviaImportacion,
)

ACTUALES = [
    {
        "numero_documento": "100",
        "nombre_completo": "Ana Gómez",
        "email": "ana@sena.co",
        "estado": "activo",
    },
    {
        "numero_documento": "200",
        "nombre_completo": "José Pérez",
        "email": "jose@sena.co",
        "estado": "inactivo",
    },
]


def test_busqueda_sin_tildes_ni_mayusculas_y_documento_por_prefijo():
    assert [b["numero_documento"] for b in ben.filtrar(ACTUALES, "ANA GOMEZ")] == [
        "100"
    ]
    assert ben.filtrar(ACTUALES, "jose") == []  # inactivo: no sale por defecto
    assert [b["numero_documento"] for b in ben.filtrar(ACTUALES, "jose", "todos")] == [
        "200"
    ]
    assert [b["numero_documento"] for b in ben.filtrar(ACTUALES, "2", "todos")] == [
        "200"
    ]


def test_correo_obligatorio_valido_y_unico():
    vista = VistaPreviaImportacion(archivo="x.xlsx")
    vista.altas = [
        {
            "numero_documento": "300",
            "nombre_completo": "A",
            "email": "",
            "estado": "activo",
            "_fila": 2,
        },
        {
            "numero_documento": "301",
            "nombre_completo": "B",
            "email": "malo",
            "estado": "activo",
            "_fila": 3,
        },
        {
            "numero_documento": "302",
            "nombre_completo": "C",
            "email": "ana@sena.co",
            "estado": "activo",
            "_fila": 4,
        },
        {
            "numero_documento": "303",
            "nombre_completo": "D",
            "email": "Nuevo@Sena.co",
            "estado": "activo",
            "_fila": 5,
        },
        {
            "numero_documento": "304",
            "nombre_completo": "E",
            "email": "nuevo@sena.co",
            "estado": "activo",
            "_fila": 6,
        },
    ]
    ben.validar_correos(vista, ACTUALES)
    assert [a["numero_documento"] for a in vista.altas] == ["303"]
    assert vista.altas[0]["email"] == "nuevo@sena.co"
    motivos = {e.fila: e.motivo for e in vista.errores}
    assert motivos == {
        2: "Correo vacío",
        3: "Correo inválido",
        4: "Correo de otro beneficiario",
        6: "Correo repetido en el archivo",
    }


def test_vista_previa_desde_plantilla(tmp_path):
    ruta = tmp_path / "lista.xlsx"
    rep.crear_plantilla_beneficiarios(ruta)
    libro = openpyxl.load_workbook(ruta)
    hoja = libro["Beneficiarios"]
    filas = [
        ["100", "Ana Gómez Ruiz", "ana@sena.co", "activo"],  # cambio
        ["400", "Nueva Persona", "nueva@sena.co", "activo"],  # alta
        ["500", "Sin Correo", "", "activo"],  # error
        ["=1+1", "Fórmula", "f@sena.co", "activo"],  # error
    ]
    for i, fila in enumerate(filas, start=2):
        for j, valor in enumerate(fila, start=1):
            hoja.cell(row=i, column=j, value=valor)
    libro.save(ruta)
    vista = ben.vista_previa(ruta, ACTUALES)
    assert vista.conteos == {"altas": 1, "cambios": 1, "bajas": 0, "errores": 2}
    assert sorted(e.fila for e in vista.errores) == [4, 5]


def test_exportar_entregas(tmp_path):
    reporte = {
        "desde": "2026-11-23",
        "hasta": "2026-11-23",
        "detalle": [
            {
                "fecha_hora": "2026-11-23 12:00:00",
                "documento": "100",
                "nombre": "=peligro",
                "servicio": "Almuerzo",
                "modalidad": "Código",
            }
        ],
        "totales": {"desayuno": 0, "almuerzo": 1, "refrigerio": 0},
        "total": 1,
    }
    ruta = rep.exportar_entregas(reporte, tmp_path / rep.nombre_archivo("Entregas"))
    hoja = openpyxl.load_workbook(ruta).active
    assert hoja["C6"].value == "'=peligro"  # C-17: no se ejecuta como fórmula
    assert ruta.name.startswith("FoodPass_Entregas_")


def test_alertas_de_raciones(monkeypatch):
    pytest.importorskip("PySide6")
    try:
        from foodpass_desktop.ui.panel_view import calcular_alertas
    except ImportError as e:  # Qt sin librerías gráficas (p. ej. libEGL)
        pytest.skip(f"Qt no disponible en este equipo: {e}")

    monkeypatch.setenv("RACIONES_ALMUERZO", "10")
    resumen = {"por_servicio": {"desayuno": 0, "almuerzo": 8, "refrigerio": 0}}
    assert calcular_alertas(resumen)[0][0] == "atencion"
    assert (
        calcular_alertas(
            {"por_servicio": {"desayuno": 0, "almuerzo": 2, "refrigerio": 0}}
        )
        == []
    )
    assert calcular_alertas(None, conectado=False)[0][0] == "advertencia"


@pytest.mark.skipif(
    not os.getenv("DB_HOST"), reason="Sin base de datos de prueba (DB_HOST)"
)
def test_integracion_resumen_y_reporte_con_mysql():
    from foodpass_desktop.storage import consultas_bd

    resumen = consultas_bd.resumen_dia()
    assert set(resumen["por_servicio"]) == {"desayuno", "almuerzo", "refrigerio"}
    reporte = consultas_bd.reporte_entregas(resumen["fecha"], resumen["fecha"])
    assert reporte["total"] == resumen["total"]
    with pytest.raises(ValueError):
        consultas_bd.reporte_entregas("2026-01-01", "2026-12-31")
