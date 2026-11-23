"""Pruebas de la pantalla de inicio de sesión y del coordinador de sesión (T05).

Corren sin monitor (QT_QPA_PLATFORM=offscreen). Si el equipo no puede cargar
Qt, se saltan.
"""

import os
import time
from datetime import datetime, timedelta

import pytest

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
try:
    from PySide6 import QtWidgets
except ImportError as e:
    # En el servidor de GitHub falta libEGL: PySide6 está instalado pero no
    # carga. `importorskip` de pytest 9 solo salta si el módulo no existe.
    pytest.skip(f"Qt no disponible en este equipo: {e}", allow_module_level=True)

from PySide6.QtCore import QTimer  # noqa: E402

from foodpass_desktop.api.errores import ApiError  # noqa: E402
from foodpass_desktop.core import sesion as sesion_mod  # noqa: E402
from foodpass_desktop.services import auth_service as auth_mod  # noqa: E402
from foodpass_desktop.services.auth_service import AuthService  # noqa: E402
from foodpass_desktop.storage.credenciales import AlmacenMemoria  # noqa: E402
from foodpass_desktop.ui import login_window as login_mod  # noqa: E402
from tests.test_auth_service import RESPUESTA_LOGIN, ClienteFalso  # noqa: E402


@pytest.fixture(scope="module")
def app():
    try:
        return QtWidgets.QApplication.instance() or QtWidgets.QApplication([])
    except Exception as e:  # pragma: no cover - depende del equipo
        pytest.skip(f"Qt no disponible: {e}")


def respuesta_vigente():
    expira = datetime.now(auth_mod.BOGOTA) + timedelta(hours=1)
    return {**RESPUESTA_LOGIN, "expira": expira.isoformat()}


def en_el_mismo_hilo(funcion, *args, al_exito=None, al_error=None, **kwargs):
    try:
        resultado = funcion(*args, **kwargs)
    except Exception as e:
        if al_error:
            al_error(e)
    else:
        if al_exito:
            al_exito(resultado)


@pytest.fixture
def entorno(app, monkeypatch):
    monkeypatch.setattr(auth_mod, "ITERACIONES_PIN", 1_000)
    monkeypatch.setattr(login_mod, "ejecutar_en_segundo_plano", en_el_mismo_hilo)
    monkeypatch.setattr(sesion_mod, "ejecutar_en_segundo_plano", en_el_mismo_hilo)
    cliente = ClienteFalso(respuesta=respuesta_vigente())
    auth = AuthService(cliente, AlmacenMemoria(), dispositivo="PC-PRUEBA")
    return app, auth, cliente


def escribir(ventana, email, password):
    ventana.campo_email.setText(email)
    ventana.campo_password.setText(password)
    ventana.boton_ingresar.click()


def test_la_contrasena_va_oculta(entorno):
    _, auth, _ = entorno
    ventana = login_mod.LoginWindow(auth)
    assert ventana.campo_password.echoMode() == QtWidgets.QLineEdit.EchoMode.Password
    assert ventana.boton_ingresar.text() == "Ingresar"


def test_correo_invalido_no_llama_a_la_api(entorno):
    _, auth, cliente = entorno
    ventana = login_mod.LoginWindow(auth)
    escribir(ventana, "operador", "123456")
    assert ventana.mensaje_acceso.text() == "Escribe un correo válido."
    assert cliente.llamadas == []


def test_primer_ingreso_pide_crear_pin_y_luego_abre(entorno):
    _, auth, _ = entorno
    ventana = login_mod.LoginWindow(auth)
    abiertas = []
    ventana.sesion_iniciada.connect(abiertas.append)

    escribir(ventana, "operador@foodpass.co", "123456")
    assert ventana.vistas.currentWidget() is ventana.vista_pin
    assert abiertas == []

    ventana.campo_pin.setText("4821")
    ventana.campo_confirmacion.setText("4821")
    ventana.boton_pin.click()
    assert abiertas[0]["nombre"] == "Operador de prueba"


def test_con_pin_creado_abre_directo(entorno):
    _, auth, _ = entorno
    auth.crear_pin("4821")
    ventana = login_mod.LoginWindow(auth)
    abiertas = []
    ventana.sesion_iniciada.connect(abiertas.append)
    escribir(ventana, "operador@foodpass.co", "123456")
    assert len(abiertas) == 1


def test_credenciales_invalidas_limpian_la_contrasena(entorno):
    _, auth, cliente = entorno
    cliente.error = ApiError("CREDENCIALES_INVALIDAS", status=401)
    ventana = login_mod.LoginWindow(auth)
    escribir(ventana, "operador@foodpass.co", "mala")
    assert (
        ventana.mensaje_acceso.text()
        == "Correo o contraseña incorrectos. Inténtalo de nuevo."
    )
    assert ventana.campo_password.text() == ""
    assert ventana.boton_ingresar.isEnabled()


def test_cuenta_bloqueada_muestra_cuenta_regresiva(entorno):
    _, auth, cliente = entorno
    cliente.error = ApiError(
        "CUENTA_BLOQUEADA", status=423, datos={"segundos_restantes": 2}
    )
    ventana = login_mod.LoginWindow(auth)
    escribir(ventana, "operador@foodpass.co", "mala")
    assert (
        ventana.mensaje_acceso.text()
        == "Ingreso bloqueado por 0:02. ¿Olvidaste tu contraseña? Comunícate con soporte técnico."
    )
    assert not ventana.boton_ingresar.isEnabled()

    ventana._avanzar_cuenta_regresiva()
    assert "0:01." in ventana.mensaje_acceso.text()
    ventana._avanzar_cuenta_regresiva()
    assert ventana.boton_ingresar.isEnabled()
    assert not ventana.cuenta_bloqueada


def test_cinco_pin_errados_vuelven_al_correo(entorno):
    _, auth, _ = entorno
    auth.iniciar_sesion("operador@foodpass.co", "123456")
    auth.crear_pin("4821")
    ventana = login_mod.LoginWindow(auth)
    agotado = []
    ventana.pin_agotado.connect(lambda: agotado.append(1))
    ventana.mostrar_desbloqueo(auth.operador)

    for _ in range(5):
        ventana.campo_pin.setText("0000")
        ventana.boton_pin.click()

    assert agotado == [1]
    assert ventana.vistas.currentWidget() is ventana.vista_acceso
    assert "correo y contraseña" in ventana.mensaje_acceso.text()
    assert not auth.hay_sesion


def test_la_ventana_no_se_congela_mientras_espera(app, monkeypatch):
    """Con el trabajador real, la interfaz sigue procesando eventos."""
    monkeypatch.setattr(auth_mod, "ITERACIONES_PIN", 1_000)

    class ClienteLento(ClienteFalso):
        def post(self, ruta, json=None):
            time.sleep(0.6)
            return super().post(ruta, json)

    auth = AuthService(
        ClienteLento(respuesta=respuesta_vigente()), AlmacenMemoria(), dispositivo="PC"
    )
    auth.crear_pin("4821")
    ventana = login_mod.LoginWindow(auth)
    latidos, abiertas = [], []
    latido = QTimer()
    latido.timeout.connect(lambda: latidos.append(1))
    latido.start(50)
    ventana.sesion_iniciada.connect(abiertas.append)

    escribir(ventana, "operador@foodpass.co", "123456")
    assert ventana.boton_ingresar.text() == "Ingresando…"
    limite = time.monotonic() + 3
    while not abiertas and time.monotonic() < limite:
        app.processEvents()
        time.sleep(0.01)
    latido.stop()

    assert abiertas, "el login no respondió en 3 s"
    assert len(latidos) >= 5  # el bucle de eventos siguió vivo durante la espera


# --- coordinador de sesión ----------------------------------------------------
def test_flujo_completo_login_bloqueo_pin_y_cierre(entorno):
    app, auth, cliente = entorno
    auth.crear_pin("4821")
    controlador = sesion_mod.ControladorSesion(app, auth, cliente, minutos_bloqueo=5)
    controlador.iniciar()
    login = controlador.login

    escribir(login, "operador@foodpass.co", "123456")
    assert controlador.ventana is not None and controlador.ventana.isVisible()
    assert not login.isVisible()
    assert controlador.ventana.nombre_operador.text() == "Operador de prueba"
    assert controlador.detector.activo

    controlador.bloquear()  # lo mismo que hace el detector al vencer el tiempo
    assert not controlador.ventana.isVisible()
    assert login.vistas.currentWidget() is login.vista_pin

    login.campo_pin.setText("4821")
    login.boton_pin.click()
    assert controlador.ventana.isVisible()

    controlador.ventana.boton_cerrar_sesion.click()
    assert cliente.llamadas[-1][0] == "/auth/logout"
    assert controlador.ventana is None
    assert login.isVisible() and login.vistas.currentWidget() is login.vista_acceso
    assert not auth.hay_sesion
    login.close()
