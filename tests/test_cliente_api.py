import pytest
import requests

from foodpass_desktop.api.cliente import ClienteApi
from foodpass_desktop.api.errores import ApiError, SinConexionError


class RespuestaFalsa:
    def __init__(self, status=200, cuerpo=None, json_invalido=False):
        self.status_code = status
        self._cuerpo = cuerpo if cuerpo is not None else {}
        self._json_invalido = json_invalido

    def json(self):
        if self._json_invalido:
            raise ValueError("no es json")
        return self._cuerpo


@pytest.fixture
def cliente():
    c = ClienteApi("http://prueba/api/v1/escritorio")
    c.establecer_token("TOKEN123")
    return c


def simular(cliente, monkeypatch, respuesta=None, excepcion=None):
    llamadas = []

    def falsa(metodo, url, **kwargs):
        llamadas.append({"metodo": metodo, "url": url, **kwargs})
        if excepcion:
            raise excepcion
        return respuesta

    monkeypatch.setattr(cliente._sesion, "request", falsa)
    return llamadas


def test_exito_devuelve_json_y_arma_la_url(cliente, monkeypatch):
    llamadas = simular(cliente, monkeypatch, RespuestaFalsa(200, {"ok": True}))
    assert cliente.get("/beneficiarios/cache") == {"ok": True}
    assert llamadas[0]["url"] == "http://prueba/api/v1/escritorio/beneficiarios/cache"
    assert llamadas[0]["timeout"] == 3


def test_envia_bearer_en_ruta_protegida(cliente, monkeypatch):
    llamadas = simular(cliente, monkeypatch, RespuestaFalsa(200))
    cliente.post("/canjes", json={"x": 1})
    assert llamadas[0]["headers"]["Authorization"] == "Bearer TOKEN123"


@pytest.mark.parametrize("ruta", ["/auth/login", "/estado"])
def test_no_envia_bearer_en_login_ni_estado(cliente, monkeypatch, ruta):
    llamadas = simular(cliente, monkeypatch, RespuestaFalsa(200))
    cliente.post(ruta)
    assert "Authorization" not in llamadas[0]["headers"]


def test_401_lanza_apierror_y_avisa_a_la_app(cliente, monkeypatch):
    avisos = []
    cliente.al_expirar_sesion(lambda: avisos.append(1))
    cuerpo = {"codigo": "TOKEN_INVALIDO", "mensaje": "x", "datos": {}}
    simular(cliente, monkeypatch, RespuestaFalsa(401, cuerpo))
    with pytest.raises(ApiError) as e:
        cliente.get("/productos")
    assert e.value.codigo == "TOKEN_INVALIDO"
    assert avisos == [1]


def test_401_en_login_no_avisa_sesion_expirada(cliente, monkeypatch):
    avisos = []
    cliente.al_expirar_sesion(lambda: avisos.append(1))
    cuerpo = {"codigo": "CREDENCIALES_INVALIDAS", "mensaje": "x", "datos": {}}
    simular(cliente, monkeypatch, RespuestaFalsa(401, cuerpo))
    with pytest.raises(ApiError) as e:
        cliente.post("/auth/login", json={})
    assert e.value.codigo == "CREDENCIALES_INVALIDAS"
    assert avisos == []


def test_409_trae_codigo_y_datos(cliente, monkeypatch):
    cuerpo = {
        "codigo": "YA_RECIBIO",
        "mensaje": "Ya recibió",
        "datos": {"servicio": "almuerzo"},
    }
    simular(cliente, monkeypatch, RespuestaFalsa(409, cuerpo))
    with pytest.raises(ApiError) as e:
        cliente.post("/canjes", json={})
    assert e.value.codigo == "YA_RECIBIO"
    assert e.value.datos == {"servicio": "almuerzo"}
    assert e.value.status == 409


def test_422_lanza_apierror(cliente, monkeypatch):
    cuerpo = {"codigo": "DATOS_INVALIDOS", "mensaje": "x", "datos": {}}
    simular(cliente, monkeypatch, RespuestaFalsa(422, cuerpo))
    with pytest.raises(ApiError) as e:
        cliente.post("/ventas", json={})
    assert e.value.codigo == "DATOS_INVALIDOS"


def test_timeout_lanza_sin_conexion(cliente, monkeypatch):
    simular(cliente, monkeypatch, excepcion=requests.Timeout())
    with pytest.raises(SinConexionError):
        cliente.get("/estado")


def test_error_sin_json_usa_codigo_generico(cliente, monkeypatch):
    simular(cliente, monkeypatch, RespuestaFalsa(500, json_invalido=True))
    with pytest.raises(ApiError) as e:
        cliente.get("/productos")
    assert e.value.codigo == "HTTP_500"