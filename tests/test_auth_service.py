"""Pruebas de services/auth_service.py (T05 · RF-ES25 · CU-01)."""

from datetime import datetime, timedelta

import pytest

from foodpass_desktop.api.cliente import ClienteApi
from foodpass_desktop.api.errores import ApiError, SinConexionError
from foodpass_desktop.services import auth_service as auth_mod
from foodpass_desktop.services.auth_service import (
    BOGOTA,
    CLAVE_EXPIRA,
    CLAVE_PIN,
    CLAVE_TOKEN,
    AuthService,
    ErrorInicioSesion,
    formatear_tiempo,
    interpretar_error,
    validar_credenciales,
    validar_formato_pin,
)
from foodpass_desktop.storage.credenciales import AlmacenMemoria
from tools.mock_api import app as mock

AHORA = datetime(2026, 11, 20, 7, 0, tzinfo=BOGOTA)


class Reloj:
    def __init__(self, momento=AHORA):
        self.momento = momento

    def __call__(self):
        return self.momento

    def avanzar(self, **kwargs):
        self.momento += timedelta(**kwargs)


class ClienteFalso:
    """Imita a ClienteApi: devuelve o lanza lo que se le programe."""

    def __init__(self, respuesta=None, error=None):
        self.respuesta = respuesta or {}
        self.error = error
        self.token = None
        self.llamadas = []

    def post(self, ruta, json=None):
        self.llamadas.append((ruta, json))
        if self.error:
            raise self.error
        return self.respuesta

    def renovar(self):
        datos = self.post("/auth/renovar")
        self.establecer_token(datos["token"])
        return datos

    def establecer_token(self, token):
        self.token = token

    def limpiar_token(self):
        self.token = None

    def al_expirar_sesion(self, callback):
        pass


RESPUESTA_LOGIN = {
    "token": "TOKEN-1",
    "expira": "2026-11-20T08:00:00-05:00",
    "operador": {
        "id": 7,
        "nombre": "Operador de prueba",
        "email": "operador@foodpass.co",
    },
}


@pytest.fixture
def reloj():
    return Reloj()


@pytest.fixture
def almacen():
    return AlmacenMemoria()


@pytest.fixture(autouse=True)
def pin_rapido(monkeypatch):
    # El hash real usa 200.000 iteraciones; en pruebas basta con pocas.
    monkeypatch.setattr(auth_mod, "ITERACIONES_PIN", 1_000)


def crear_servicio(almacen, reloj, **kwargs):
    cliente = ClienteFalso(**kwargs)
    return AuthService(cliente, almacen, reloj=reloj, dispositivo="PC-PRUEBA"), cliente


def error_api(status, codigo, datos=None):
    return ApiError(codigo=codigo, mensaje="x", datos=datos, status=status)


# --- validaciones antes de enviar ------------------------------------------
@pytest.mark.parametrize(
    "email, password, esperado",
    [
        ("operador@foodpass.co", "123456", None),
        ("  operador@foodpass.co ", "123456", None),
        ("", "123456", "CORREO_INVALIDO"),
        ("operador", "123456", "CORREO_INVALIDO"),
        ("operador@foodpass", "123456", "CORREO_INVALIDO"),
        ("ope rador@foodpass.co", "123456", "CORREO_INVALIDO"),
        ("operador@foodpass.co", "", "PASSWORD_VACIA"),
    ],
)
def test_validar_credenciales(email, password, esperado):
    assert validar_credenciales(email, password) == esperado


def test_datos_invalidos_no_llaman_a_la_api(almacen, reloj):
    servicio, cliente = crear_servicio(almacen, reloj, respuesta=RESPUESTA_LOGIN)
    with pytest.raises(ErrorInicioSesion) as e:
        servicio.iniciar_sesion("no-es-correo", "123456")
    assert e.value.codigo == "CORREO_INVALIDO"
    assert cliente.llamadas == []


@pytest.mark.parametrize(
    "segundos, texto", [(300, "5:00"), (65, "1:05"), (9, "0:09"), (-3, "0:00")]
)
def test_formatear_tiempo(segundos, texto):
    assert formatear_tiempo(segundos) == texto


# --- respuesta 200 -----------------------------------------------------------
def test_login_correcto_guarda_token_en_almacen_y_cliente(almacen, reloj):
    servicio, cliente = crear_servicio(almacen, reloj, respuesta=RESPUESTA_LOGIN)

    operador = servicio.iniciar_sesion(" Operador@FoodPass.co ", "123456")

    assert operador["nombre"] == "Operador de prueba"
    ruta, cuerpo = cliente.llamadas[0]
    assert ruta == "/auth/login"
    assert cuerpo == {
        "email": "operador@foodpass.co",
        "password": "123456",
        "dispositivo": "PC-PRUEBA",
    }
    assert cliente.token == "TOKEN-1"
    assert almacen.leer(CLAVE_TOKEN) == "TOKEN-1"
    assert almacen.leer(CLAVE_EXPIRA) == "2026-11-20T08:00:00-05:00"
    assert servicio.hay_sesion


def test_respuesta_sin_token_es_error(almacen, reloj):
    servicio, _ = crear_servicio(almacen, reloj, respuesta={"operador": {}})
    with pytest.raises(ErrorInicioSesion) as e:
        servicio.iniciar_sesion("operador@foodpass.co", "123456")
    assert e.value.codigo == "ERROR_DESCONOCIDO"
    assert almacen.leer(CLAVE_TOKEN) is None


# --- errores de la API -------------------------------------------------------
def test_401_no_dice_que_dato_fallo(almacen, reloj):
    servicio, _ = crear_servicio(
        almacen, reloj, error=error_api(401, "CREDENCIALES_INVALIDAS")
    )
    with pytest.raises(ErrorInicioSesion) as e:
        servicio.iniciar_sesion("operador@foodpass.co", "mala")
    assert e.value.codigo == "CREDENCIALES_INVALIDAS"
    assert e.value.mensaje == "Correo o contraseña incorrectos. Inténtalo de nuevo."
    assert almacen.leer(CLAVE_TOKEN) is None


def test_423_trae_cuenta_regresiva(almacen, reloj):
    servicio, _ = crear_servicio(
        almacen,
        reloj,
        error=error_api(423, "CUENTA_BLOQUEADA", {"segundos_restantes": 287}),
    )
    with pytest.raises(ErrorInicioSesion) as e:
        servicio.iniciar_sesion("operador@foodpass.co", "mala")
    assert e.value.codigo == "CUENTA_BLOQUEADA"
    assert e.value.segundos_restantes == 287
    assert (
        e.value.mensaje
        == "Ingreso bloqueado por 4:47. ¿Olvidaste tu contraseña? Comunícate con soporte técnico."
    )


def test_403_sin_rol_de_cafeteria(almacen, reloj):
    servicio, _ = crear_servicio(
        almacen, reloj, error=error_api(403, "SIN_ROL_CAFETERIA")
    )
    with pytest.raises(ErrorInicioSesion) as e:
        servicio.iniciar_sesion("sinrol@foodpass.co", "123456")
    assert (
        e.value.mensaje
        == "Esta cuenta no tiene acceso al escritorio. Usa tu cuenta de operador."
    )


def test_sin_conexion(almacen, reloj):
    servicio, _ = crear_servicio(almacen, reloj, error=SinConexionError("timeout"))
    with pytest.raises(ErrorInicioSesion) as e:
        servicio.iniciar_sesion("operador@foodpass.co", "123456")
    assert (
        e.value.mensaje == "No hay conexión con el servidor. Avisa a soporte técnico."
    )


@pytest.mark.parametrize(
    "error",
    [
        error_api(500, "HTTP_500"),
        error_api(423, "CUENTA_BLOQUEADA", {"segundos_restantes": "x"}),
        ValueError(),
    ],
)
def test_errores_inesperados_tienen_mensaje_generico_o_seguro(error):
    resultado = interpretar_error(error)
    assert resultado.mensaje  # nunca vacío
    if resultado.codigo == "CUENTA_BLOQUEADA":
        assert resultado.segundos_restantes == 0


# --- renovación ---------------------------------------------------------------
def test_renovar_solo_antes_de_vencer(almacen, reloj):
    servicio, cliente = crear_servicio(almacen, reloj, respuesta=RESPUESTA_LOGIN)
    servicio.iniciar_sesion("operador@foodpass.co", "123456")

    # Vence a las 8:00 y se renueva 5 min antes: faltan 55 min.
    assert servicio.segundos_para_renovar() == 55 * 60
    assert not servicio.necesita_renovar()
    reloj.avanzar(minutes=55)
    assert servicio.necesita_renovar()

    cliente.respuesta = {"token": "TOKEN-2", "expira": "2026-11-20T09:00:00-05:00"}
    servicio.renovar()
    assert cliente.llamadas[-1][0] == "/auth/renovar"
    assert cliente.token == "TOKEN-2"
    assert almacen.leer(CLAVE_TOKEN) == "TOKEN-2"
    assert servicio.segundos_para_renovar() == 60 * 60


def test_jornada_de_8_horas_sin_volver_a_iniciar_sesion(almacen, reloj):
    servicio, cliente = crear_servicio(almacen, reloj, respuesta=RESPUESTA_LOGIN)
    servicio.iniciar_sesion("operador@foodpass.co", "123456")
    for hora in range(8):
        reloj.avanzar(seconds=servicio.segundos_para_renovar())
        nueva = (reloj() + timedelta(hours=1)).isoformat()
        cliente.respuesta = {"token": f"T{hora}", "expira": nueva}
        servicio.renovar()
        assert servicio.hay_sesion
    assert reloj() >= AHORA + timedelta(hours=7)


# --- cierre de sesión ----------------------------------------------------------
def test_cerrar_sesion_llama_logout_y_borra_token(almacen, reloj):
    servicio, cliente = crear_servicio(almacen, reloj, respuesta=RESPUESTA_LOGIN)
    servicio.iniciar_sesion("operador@foodpass.co", "123456")

    servicio.cerrar_sesion()

    assert cliente.llamadas[-1][0] == "/auth/logout"
    assert cliente.token is None
    assert almacen.leer(CLAVE_TOKEN) is None
    assert not servicio.hay_sesion


def test_cerrar_sesion_sin_conexion_igual_borra_token(almacen, reloj):
    servicio, cliente = crear_servicio(almacen, reloj, respuesta=RESPUESTA_LOGIN)
    servicio.iniciar_sesion("operador@foodpass.co", "123456")
    cliente.error = SinConexionError("sin red")

    servicio.cerrar_sesion()

    assert almacen.leer(CLAVE_TOKEN) is None
    assert cliente.token is None


# --- PIN -----------------------------------------------------------------------
@pytest.mark.parametrize(
    "pin, valido",
    [
        ("1234", True),
        ("123456", True),
        ("123", False),
        ("1234567", False),
        ("12a4", False),
        ("", False),
    ],
)
def test_formato_del_pin(pin, valido):
    assert validar_formato_pin(pin) is valido


def test_pin_se_guarda_como_hash(almacen, reloj):
    servicio, _ = crear_servicio(almacen, reloj)
    assert not servicio.hay_pin()
    assert servicio.crear_pin("4821", "4821") is None
    assert servicio.hay_pin()
    assert "4821" not in almacen.leer(CLAVE_PIN)


def test_crear_pin_rechaza_formato_y_confirmacion(almacen, reloj):
    servicio, _ = crear_servicio(almacen, reloj)
    assert servicio.crear_pin("12") == "El PIN debe tener de 4 a 6 dígitos."
    assert servicio.crear_pin("1234", "4321") == "Los PIN no coinciden."
    assert not servicio.hay_pin()


def test_pin_correcto_desbloquea(almacen, reloj):
    servicio, _ = crear_servicio(almacen, reloj)
    servicio.crear_pin("4821")
    assert servicio.verificar_pin("4821").correcto


def test_pin_errado_cuenta_intentos_y_el_correcto_reinicia(almacen, reloj):
    servicio, _ = crear_servicio(almacen, reloj)
    servicio.crear_pin("4821")
    resultado = servicio.verificar_pin("0000")
    assert not resultado.correcto
    assert resultado.intentos_restantes == 4
    assert resultado.mensaje == "PIN incorrecto. Te quedan 4 intentos."
    servicio.verificar_pin("4821")
    assert servicio.verificar_pin("0000").intentos_restantes == 4


def test_cinco_pin_errados_borran_el_token(almacen, reloj):
    servicio, cliente = crear_servicio(almacen, reloj, respuesta=RESPUESTA_LOGIN)
    servicio.iniciar_sesion("operador@foodpass.co", "123456")
    servicio.crear_pin("4821")

    for _ in range(4):
        assert not servicio.verificar_pin("0000").agotado
    resultado = servicio.verificar_pin("0000")

    assert resultado.agotado
    assert (
        resultado.mensaje == "Demasiados intentos. Ingresa con tu correo y contraseña."
    )
    assert almacen.leer(CLAVE_TOKEN) is None
    assert cliente.token is None
    assert not servicio.hay_sesion


def test_sin_pin_guardado_nunca_desbloquea(almacen, reloj):
    servicio, _ = crear_servicio(almacen, reloj)
    assert not servicio.verificar_pin("1234").correcto


# --- integración con el servidor simulado (T04) ------------------------------
@pytest.fixture
def servicio_mock(monkeypatch, almacen):
    """AuthService real + ClienteApi real hablando con tools/mock_api."""
    mock.tokens.clear()
    mock.intentos.clear()
    flask = mock.app.test_client()

    class Respuesta:
        def __init__(self, r):
            self.status_code = r.status_code
            self._r = r

        def json(self):
            datos = self._r.get_json(silent=True)
            if datos is None:
                raise ValueError("sin json")
            return datos

    def enviar(metodo, url, params=None, json=None, headers=None, timeout=None):
        ruta = url.removeprefix("http://prueba")
        return Respuesta(flask.open(ruta, method=metodo, json=json, headers=headers))

    cliente = ClienteApi("http://prueba/api/v1/escritorio")
    monkeypatch.setattr(cliente._sesion, "request", enviar)
    return AuthService(cliente, almacen, dispositivo="PC-PRUEBA")


def test_mock_login_renovar_y_logout(servicio_mock, almacen):
    operador = servicio_mock.iniciar_sesion("operador@foodpass.co", "123456")
    assert operador["email"] == "operador@foodpass.co"
    primero = almacen.leer(CLAVE_TOKEN)

    servicio_mock.renovar()
    assert almacen.leer(CLAVE_TOKEN) != primero

    servicio_mock.cerrar_sesion()
    assert almacen.leer(CLAVE_TOKEN) is None
    assert mock.tokens == {}


def test_mock_tres_intentos_fallidos_bloquean_con_cuenta_regresiva(servicio_mock):
    for _ in range(2):
        with pytest.raises(ErrorInicioSesion) as e:
            servicio_mock.iniciar_sesion("operador@foodpass.co", "mala")
        assert e.value.codigo == "CREDENCIALES_INVALIDAS"
    with pytest.raises(ErrorInicioSesion) as e:
        servicio_mock.iniciar_sesion("operador@foodpass.co", "mala")
    assert e.value.codigo == "CUENTA_BLOQUEADA"
    assert (
        e.value.mensaje
        == "Ingreso bloqueado por 5:00. ¿Olvidaste tu contraseña? Comunícate con soporte técnico."
    )


def test_mock_cuenta_sin_rol(servicio_mock):
    with pytest.raises(ErrorInicioSesion) as e:
        servicio_mock.iniciar_sesion("sinrol@foodpass.co", "123456")
    assert e.value.codigo == "SIN_ROL_CAFETERIA"


# --- v2.2: API FoodPass real, bloqueo local y rol (C2.2-01 · C2.2-04) -------
def _jwt(exp):
    import base64
    import json

    cuerpo = (
        base64.urlsafe_b64encode(json.dumps({"id": 8, "exp": exp}).encode())
        .decode()
        .rstrip("=")
    )
    return f"cabecera.{cuerpo}.firma"


def test_respuesta_real_de_la_api(almacen, reloj):
    exp = int((AHORA + timedelta(days=7)).timestamp())
    respuesta = {
        "success": True,
        "message": "Login exitoso",
        "data": {
            "token": _jwt(exp),
            "user": {"id": 8, "name": "Operador", "email": "op@fp.co"},
        },
    }
    servicio = AuthService(
        ClienteFalso(respuesta), almacen, reloj=reloj, verificar_rol=lambda uid: True
    )
    operador = servicio.iniciar_sesion("op@fp.co", "clave")
    assert operador == {"id": 8, "nombre": "Operador", "email": "op@fp.co"}
    assert servicio.expira == AHORA + timedelta(days=7)


def test_rol_no_permitido_no_guarda_token(almacen, reloj):
    respuesta = {"data": {"token": "t", "user": {"id": 3, "name": "Aprendiz"}}}
    servicio = AuthService(
        ClienteFalso(respuesta), almacen, reloj=reloj, verificar_rol=lambda uid: False
    )
    with pytest.raises(ErrorInicioSesion) as e:
        servicio.iniciar_sesion("aprendiz@sena.co", "clave")
    assert e.value.codigo == "SIN_ROL_CAFETERIA"
    assert almacen.leer(CLAVE_TOKEN) is None


def test_tres_401_de_la_api_real_bloquean_5_min_en_el_equipo(almacen, reloj):
    error = ApiError("HTTP_401", "Usuario o contraseña incorrectos.", status=401)
    cliente = ClienteFalso(error=error)
    servicio = AuthService(
        cliente, almacen, reloj=reloj, verificar_rol=lambda uid: True
    )
    for _ in range(2):
        with pytest.raises(ErrorInicioSesion) as e:
            servicio.iniciar_sesion("op@fp.co", "mala")
        assert e.value.codigo == "CREDENCIALES_INVALIDAS"
    with pytest.raises(ErrorInicioSesion) as e:
        servicio.iniciar_sesion("op@fp.co", "mala")
    assert e.value.codigo == "CUENTA_BLOQUEADA"
    assert "soporte técnico" in e.value.mensaje
    llamadas = len(cliente.llamadas)
    reloj.avanzar(minutes=2)
    with pytest.raises(ErrorInicioSesion) as e:
        servicio.iniciar_sesion("op@fp.co", "buena")
    assert e.value.segundos_restantes == 180
    assert len(cliente.llamadas) == llamadas  # bloqueado: no llama a la API
    reloj.avanzar(minutes=3)
    cliente.error = None
    cliente.respuesta = {"data": {"token": "t", "user": {"id": 8}}}
    assert servicio.iniciar_sesion("op@fp.co", "buena")["id"] == 8
