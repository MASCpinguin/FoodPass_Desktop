"""Pruebas unitarias de la capa de servicios de canje (RF-ES17 y RF-ES21)."""

from unittest.mock import MagicMock

from foodpass_desktop.api.errores import ApiError
from foodpass_desktop.services.canje_service import CanjeService


def test_canje_qr_aceptado():
    mock_api = MagicMock()
    mock_api.post.return_value = {
        "estado": "entregado",
        "canje": {
            "usuario_id": 1001,
            "nombre": "Aprendiz de prueba 1",
            "documento": "1000000001",
            "programa": "ADSO",
            "foto_url": None,
            "servicio": "Almuerzo",
            "hora": "12:15 PM",
            "modalidad": "qr",
        },
    }
    servicio = CanjeService(api_client=mock_api)

    resultado = servicio.registrar_canje_qr("Almuerzo", "1001")

    assert resultado.tipo == "entregado"
    assert resultado.datos["nombre"] == "Aprendiz de prueba 1"
    assert resultado.datos["documento"] == "1000000001"
    mock_api.post.assert_called_once_with(
        "/canjes",
        json={"usuario_id": 1001, "servicio": "Almuerzo", "modalidad": "qr"},
    )


def test_canje_qr_ya_recibio():
    mock_api = MagicMock()
    mock_api.post.side_effect = ApiError(
        codigo="YA_RECIBIO_HOY",
        mensaje="Ya recibió Desayuno hoy a las 07:30 AM.",
        datos={
            "nombre": "Aprendiz de prueba 1",
            "servicio": "Desayuno",
            "hora": "07:30 AM",
        },
        status=409,
    )
    servicio = CanjeService(api_client=mock_api)

    resultado = servicio.registrar_canje_qr("Almuerzo", "1001")

    assert resultado.tipo == "ya_recibio"
    assert resultado.datos["servicio"] == "Desayuno"
    assert resultado.datos["hora"] == "07:30 AM"


def test_canje_qr_no_es_beneficiario():
    mock_api = MagicMock()
    mock_api.post.side_effect = ApiError(
        codigo="NO_BENEFICIARIO",
        mensaje="No es beneficiario activo.",
        status=404,
    )
    servicio = CanjeService(api_client=mock_api)

    resultado = servicio.registrar_canje_qr("Almuerzo", "9999")

    assert resultado.tipo == "no_beneficiario"


def test_canje_qr_codigo_no_reconocido_no_llama_api():
    mock_api = MagicMock()
    servicio = CanjeService(api_client=mock_api)

    for entrada_invalida in ("ABC123", "12345678901", "", "10-01"):
        resultado = servicio.registrar_canje_qr("Almuerzo", entrada_invalida)
        assert resultado.tipo == "no_reconocido"

    mock_api.post.assert_not_called()


def test_canje_manual_por_documento_y_motivo():
    mock_api = MagicMock()
    mock_api.post.return_value = {
        "estado": "entregado",
        "canje": {
            "nombre": "Aprendiz de prueba 2",
            "documento": "1000000002",
            "servicio": "Desayuno",
            "hora": "08:00 AM",
            "modalidad": "manual",
            "motivo": "Carné o celular olvidado",
        },
    }
    servicio = CanjeService(api_client=mock_api)

    resultado = servicio.registrar_canje_manual(
        "Desayuno", "1000000002", "Carné o celular olvidado"
    )

    assert resultado.tipo == "entregado"
    assert resultado.datos["modalidad"] == "manual"
    mock_api.post.assert_called_once_with(
        "/canjes",
        json={
            "documento": "1000000002",
            "servicio": "Desayuno",
            "modalidad": "manual",
            "motivo": "Carné o celular olvidado",
        },
    )