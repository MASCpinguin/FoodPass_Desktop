import pytest

from tools.mock_api import app as mock

P = "/api/v1/escritorio"


@pytest.fixture
def cliente():
    mock.tokens.clear()
    mock.intentos.clear()
    return mock.app.test_client()


def login(cliente, email="operador@foodpass.co", password="123456"):
    return cliente.post(f"{P}/auth/login",
                        json={"email": email, "password": password, "dispositivo": "PC-PRUEBA"})


def test_estado_responde_con_hora(cliente):
    r = cliente.get(f"{P}/estado")
    assert r.status_code == 200
    assert r.json["ok"] is True
    assert r.json["hora_servidor"].endswith("-05:00")


def test_login_correcto_entrega_token(cliente):
    r = login(cliente)
    assert r.status_code == 200
    assert r.json["token"]
    assert r.json["operador"]["email"] == "operador@foodpass.co"


def test_login_invalido_no_dice_que_fallo(cliente):
    r = login(cliente, password="mala")
    assert r.status_code == 401
    assert r.json["codigo"] == "CREDENCIALES_INVALIDAS"


def test_tres_intentos_bloquean_cinco_minutos(cliente):
    login(cliente, password="mala")
    login(cliente, password="mala")
    r = login(cliente, password="mala")
    assert r.status_code == 423
    assert r.json["datos"]["segundos_restantes"] == 300
    # Bloqueada, ni siquiera la contraseña correcta entra
    assert login(cliente).status_code == 423


def test_cuenta_sin_rol_de_cafeteria(cliente):
    r = login(cliente, email="sinrol@foodpass.co")
    assert r.status_code == 403
    assert r.json["codigo"] == "SIN_ROL_CAFETERIA"


def test_sin_token_responde_401(cliente):
    r = cliente.post(f"{P}/auth/renovar")
    assert r.status_code == 401
    assert r.json["codigo"] == "TOKEN_INVALIDO"


def test_renovar_y_cerrar_sesion(cliente):
    token = login(cliente).json["token"]
    r = cliente.post(f"{P}/auth/renovar", headers={"Authorization": f"Bearer {token}"})
    assert r.status_code == 200
    nuevo = r.json["token"]
    assert nuevo != token

    r = cliente.post(f"{P}/auth/logout", headers={"Authorization": f"Bearer {nuevo}"})
    assert r.status_code == 204
    # El token ya no sirve
    r = cliente.post(f"{P}/auth/logout", headers={"Authorization": f"Bearer {nuevo}"})
    assert r.status_code == 401