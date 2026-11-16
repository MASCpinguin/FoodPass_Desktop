"""Pruebas de EP-24 y EP-25 en el servidor simulado (T30)."""

import pytest

from tools.mock_api import app as mock

P = "/api/v1/escritorio"


@pytest.fixture
def cliente():
    mock.tokens.clear()
    mock.intentos.clear()
    mock.reiniciar_movimientos()
    return mock.app.test_client()


@pytest.fixture
def auth(cliente):
    r = cliente.post(f"{P}/auth/login", json={
        "email": "operador@foodpass.co", "password": "123456", "dispositivo": "PC-PRUEBA",
    })
    return {"Authorization": f"Bearer {r.json['token']}"}


def test_resumen_exige_token(cliente):
    assert cliente.get(f"{P}/caja/resumen").status_code == 401


def test_resumen_del_dia_no_suma_anuladas(cliente, auth):
    r = cliente.get(f"{P}/caja/resumen", headers=auth)
    assert r.status_code == 200
    datos = r.json
    assert datos["n_ventas"] == 5
    assert datos["total"] == 49500
    assert datos["ventas_por_metodo"]["nequi"] == {"n": 3, "total": 25000}
    assert datos["anuladas"] == {"n": 1, "total": 6000}
    assert datos["canjes_por_servicio"] == {"desayuno": 12, "almuerzo": 18, "refrigerio": 7}
    assert datos["pedidos_web_atendidos"] == 2
    assert datos["cerrada"] is False


def test_resumen_de_otro_dia_viene_en_ceros(cliente, auth):
    r = cliente.get(f"{P}/caja/resumen?fecha=2020-01-01", headers=auth)
    assert r.json["total"] == 0
    assert r.json["n_ventas"] == 0


def test_fecha_invalida(cliente, auth):
    r = cliente.get(f"{P}/caja/resumen?fecha=14-11-2026", headers=auth)
    assert r.status_code == 422
    assert r.json["codigo"] == "DATOS_INVALIDOS"


def test_cerrar_caja_y_no_dejar_cerrarla_dos_veces(cliente, auth):
    r = cliente.post(f"{P}/caja/cierres", json={"observacion": "ok"}, headers=auth)
    assert r.status_code == 201
    cierre = r.json["cierre"]
    assert cierre["total"] == 49500
    assert cierre["cerrado_por"] == "Operador de prueba"

    assert cliente.get(f"{P}/caja/resumen", headers=auth).json["cerrada"] is True

    r = cliente.post(f"{P}/caja/cierres", json={}, headers=auth)
    assert r.status_code == 409
    assert r.json["codigo"] == "YA_CERRADA"
