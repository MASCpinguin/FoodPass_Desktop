"""Pruebas de integración contra la API por HTTP (T37 · 06 Plan de pruebas).

Verifican que el servidor cumpla el 05 Contrato de endpoints.

- Por defecto arrancan el servidor simulado en un puerto libre y lo prueban
  por HTTP real (no con el cliente de pruebas de Flask).
- Para probar la API real del equipo API:
      set API_URL_PRUEBAS=https://.../api/v1/escritorio
      set API_EMAIL_PRUEBAS=operador@...
      set API_PASSWORD_PRUEBAS=...
      python -m pytest tests/test_integracion_api.py -v
  Las pruebas que modifican datos de forma irreversible (bloquear la cuenta,
  cerrar la caja) solo corren contra el servidor simulado.
- Las pruebas de un endpoint que todavía no existe se marcan como «skipped»
  y se activan solas cuando el endpoint aparece (por ejemplo EP-05 con T10).
"""

import os
import threading
import uuid
from datetime import datetime, timedelta, timezone

import pytest
import requests
from werkzeug.serving import make_server

BOGOTA = timezone(timedelta(hours=-5))
URL_REAL = os.getenv("API_URL_PRUEBAS")
EMAIL = os.getenv("API_EMAIL_PRUEBAS", "operador@foodpass.co")
PASSWORD = os.getenv("API_PASSWORD_PRUEBAS", "123456")
TIMEOUT = 5

solo_simulado = pytest.mark.skipif(
    bool(URL_REAL), reason="Modifica datos de forma irreversible: solo en el simulado."
)


# ---------- Servidor y cliente ----------
@pytest.fixture(scope="module")
def base_url():
    if URL_REAL:
        yield URL_REAL.rstrip("/")
        return
    from tools.mock_api.app import PREFIJO, app

    servidor = make_server("127.0.0.1", 0, app)  # puerto libre
    hilo = threading.Thread(target=servidor.serve_forever, daemon=True)
    hilo.start()
    yield f"http://127.0.0.1:{servidor.server_port}{PREFIJO}"
    servidor.shutdown()


@pytest.fixture(autouse=True)
def estado_limpio():
    """En el simulado, cada prueba empieza con datos nuevos."""
    if not URL_REAL:
        from tools.mock_api import app as mock

        mock.tokens.clear()
        mock.intentos.clear()
        if hasattr(mock, "reiniciar_movimientos"):  # existe desde T30
            mock.reiniciar_movimientos()


class Api:
    def __init__(self, base_url):
        self.base_url = base_url
        self.token = None

    def pedir(self, metodo, ruta, token=None, **kwargs):
        token = token or self.token
        cabeceras = {"Authorization": f"Bearer {token}"} if token else {}
        return requests.request(metodo, self.base_url + ruta, headers=cabeceras,
                                timeout=TIMEOUT, **kwargs)

    def login(self, email=EMAIL, password=PASSWORD):
        return self.pedir("POST", "/auth/login", json={
            "email": email, "password": password, "dispositivo": "PC-PRUEBAS-T37",
        })

    def iniciar_sesion(self):
        r = self.login()
        assert r.status_code == 200, r.text
        self.token = r.json()["token"]
        return self


@pytest.fixture
def api(base_url):
    return Api(base_url)


def es_error(respuesta, status, codigo):
    """El error debe tener el estado y el formato del contrato."""
    assert respuesta.status_code == status, respuesta.text
    cuerpo = respuesta.json()
    assert set(cuerpo) >= {"codigo", "mensaje", "datos"}
    assert cuerpo["codigo"] == codigo
    return cuerpo


def omitir_si_no_existe(respuesta, endpoint):
    if respuesta.status_code in (404, 405) and respuesta.json().get("codigo") in (
        "NO_ENCONTRADO", "METODO_NO_PERMITIDO",
    ):
        pytest.skip(f"{endpoint} todavía no existe en el servidor.")


# ---------- EP-03 · Estado ----------
def test_estado_entrega_hora_de_bogota(api):
    r = api.pedir("GET", "/estado")
    assert r.status_code == 200
    hora = datetime.fromisoformat(r.json()["hora_servidor"])
    assert hora.utcoffset() == timedelta(hours=-5)
    # El reloj del servidor no debe diferir más de 5 min (C-02)
    assert abs(datetime.now(BOGOTA) - hora) < timedelta(minutes=5)


# ---------- EP-01 · Inicio de sesión ----------
def test_login_valido_entrega_token_y_operador(api):
    r = api.login()
    assert r.status_code == 200
    datos = r.json()
    assert datos["token"]
    assert datetime.fromisoformat(datos["expira"]) > datetime.now(BOGOTA)
    assert datos["operador"]["email"] == EMAIL


def test_login_invalido_no_revela_que_dato_fallo(api):
    clave_mala = es_error(api.login(password="incorrecta-T37"), 401, "CREDENCIALES_INVALIDAS")
    correo_malo = es_error(api.login(email="noexiste-t37@foodpass.co"), 401,
                           "CREDENCIALES_INVALIDAS")
    # Mismo mensaje en los dos casos: no se sabe cuál dato falló
    assert clave_mala["mensaje"] == correo_malo["mensaje"]


@solo_simulado
def test_tres_intentos_bloquean_la_cuenta_cinco_minutos(api):
    api.login(password="mala")
    api.login(password="mala")
    cuerpo = es_error(api.login(password="mala"), 423, "CUENTA_BLOQUEADA")
    assert cuerpo["datos"]["segundos_restantes"] == 300
    es_error(api.login(), 423, "CUENTA_BLOQUEADA")  # ni la correcta entra


@solo_simulado
def test_cuenta_sin_rol_de_cafeteria(api):
    es_error(api.login(email="sinrol@foodpass.co"), 403, "SIN_ROL_CAFETERIA")


# ---------- EP-31 y EP-02 · Renovar y revocar ----------
def test_ruta_protegida_sin_token(api):
    es_error(api.pedir("POST", "/auth/renovar"), 401, "TOKEN_INVALIDO")


def test_renovar_entrega_un_token_nuevo(api):
    api.iniciar_sesion()
    r = api.pedir("POST", "/auth/renovar")
    assert r.status_code == 200
    assert r.json()["token"] != api.token


def test_token_revocado_responde_401(api):
    api.iniciar_sesion()
    assert api.pedir("POST", "/auth/logout").status_code == 204
    es_error(api.pedir("POST", "/auth/renovar"), 401, "TOKEN_INVALIDO")


# ---------- EP-24 y EP-25 · Caja ----------
def test_resumen_de_caja_cumple_el_contrato(api):
    api.iniciar_sesion()
    r = api.pedir("GET", "/caja/resumen")
    omitir_si_no_existe(r, "EP-24")
    assert r.status_code == 200
    datos = r.json()
    assert set(datos) >= {"fecha", "ventas_por_metodo", "total", "n_ventas",
                          "canjes_por_servicio", "pedidos_web_atendidos", "cerrada"}
    suma = sum(m["total"] for m in datos["ventas_por_metodo"].values())
    assert datos["total"] == suma  # las anuladas no suman


@solo_simulado
def test_cierre_de_caja_es_unico_por_dia(api):
    api.iniciar_sesion()
    r = api.pedir("POST", "/caja/cierres", json={"observacion": "Prueba T37"})
    omitir_si_no_existe(r, "EP-25")
    assert r.status_code == 201
    es_error(api.pedir("POST", "/caja/cierres", json={}), 409, "YA_CERRADA")


# ---------- EP-05 · Canje (se activa cuando exista el endpoint) ----------
def canje(api, usuario_id, servicio="almuerzo", id_unico=None):
    return api.pedir("POST", "/canjes", json={
        "uuid": id_unico or str(uuid.uuid4()),
        "usuario_id": usuario_id,
        "numero_documento": None,
        "servicio": servicio,
        "modalidad": "qr",
        "motivo_manual": None,
        "fecha_hora": datetime.now(BOGOTA).isoformat(timespec="seconds"),
    })


@solo_simulado
def test_canje_aceptado_y_segundo_rechazado(api):
    api.iniciar_sesion()
    r = canje(api, 1001)
    omitir_si_no_existe(r, "EP-05")
    assert r.status_code == 201
    assert r.json()["beneficiario"]["numero_documento"]
    cuerpo = es_error(canje(api, 1001, servicio="refrigerio"), 409, "YA_RECIBIO")
    assert {"servicio", "hora"} <= set(cuerpo["datos"])


@solo_simulado
def test_canje_con_el_mismo_uuid_no_se_duplica(api):
    api.iniciar_sesion()
    id_unico = str(uuid.uuid4())
    primero = canje(api, 1002, id_unico=id_unico)
    omitir_si_no_existe(primero, "EP-05")
    segundo = canje(api, 1002, id_unico=id_unico)
    assert segundo.status_code == 200
    assert segundo.json()["canje_id"] == primero.json()["canje_id"]


def test_canje_de_quien_no_es_beneficiario(api):
    api.iniciar_sesion()
    r = canje(api, 999999)
    omitir_si_no_existe(r, "EP-05")
    es_error(r, 404, "NO_BENEFICIARIO")


@solo_simulado
def test_canje_de_beneficiario_inactivo(api):
    api.iniciar_sesion()
    r = canje(api, 1005)  # inactivo en los datos de prueba
    omitir_si_no_existe(r, "EP-05")
    es_error(r, 422, "BENEFICIARIO_INACTIVO")
