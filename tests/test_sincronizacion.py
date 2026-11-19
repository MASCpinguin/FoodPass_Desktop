import socket
import sqlite3
import threading

import pytest
from werkzeug.serving import make_server

from foodpass_desktop.api.cliente import ClienteApi
from foodpass_desktop.api.errores import ApiError
from foodpass_desktop.services.sincronizacion import RUTA_LOTE, Sincronizador
from foodpass_desktop.storage.cola import ColaSync, nuevo_uuid
from tools.mock_api.app import PREFIJO, app, recibidos, tokens


def _puerto_cerrado():
    s = socket.socket()
    s.bind(("127.0.0.1", 0))
    puerto = s.getsockname()[1]
    s.close()
    return puerto


@pytest.fixture
def api_viva():
    recibidos.clear()
    tokens.clear()
    servidor = make_server("127.0.0.1", 0, app, threaded=True)
    hilo = threading.Thread(target=servidor.serve_forever, daemon=True)
    hilo.start()
    cliente = ClienteApi(f"http://127.0.0.1:{servidor.server_port}{PREFIJO}")
    datos = cliente.post(
        "/auth/login", json={"email": "operador@foodpass.co", "password": "123456"}
    )
    cliente.establecer_token(datos["token"])
    yield cliente
    servidor.shutdown()


@pytest.fixture
def api_caida():
    return ClienteApi(f"http://127.0.0.1:{_puerto_cerrado()}{PREFIJO}")


@pytest.fixture
def ruta(tmp_path):
    return tmp_path / "cola.db"


def test_registrar_con_conexion_se_envia_directo(ruta, api_viva):
    cola = ColaSync(ruta)
    uid, enviado = Sincronizador(cola, api_viva).registrar("venta", {"total": 1})
    assert enviado is True
    assert uid in recibidos
    assert cola.contar() == 0


def test_registrar_sin_conexion_va_a_la_cola_con_su_uuid(ruta, api_caida):
    cola = ColaSync(ruta)
    uid, enviado = Sincronizador(cola, api_caida).registrar("canje", {"x": 1})
    assert enviado is False
    assert len(uid) == 36
    assert cola.contar("pendiente") == 1


def test_con_cola_pendiente_el_nuevo_va_detras_aunque_haya_red(ruta, api_viva):
    cola = ColaSync(ruta)
    cola.encolar("venta", {"n": 1})
    uid, enviado = Sincronizador(cola, api_viva).registrar("anulacion", {"n": 2})
    assert enviado is False
    assert uid not in recibidos
    assert cola.contar("pendiente") == 2


def test_lote_vacio_lo_rechaza_el_servidor(api_viva):
    with pytest.raises(ApiError) as e:
        api_viva.post(RUTA_LOTE, json={"registros": []})
    assert e.value.codigo == "LOTE_INVALIDO"


def test_corte_de_red_y_reinicio_con_200_llegan_todos_sin_duplicados(
    ruta, api_viva, api_caida
):
    # 1) Sin red: 200 registros quedan en la cola.
    cola = ColaSync(ruta)
    sinc = Sincronizador(cola, api_caida)
    ids = {sinc.registrar("venta", {"n": i})[0] for i in range(200)}
    assert cola.contar("pendiente") == 200
    cola.cerrar()

    # 2) Reinicio de la app y vuelve la red.
    cola = ColaSync(ruta)
    resumen = Sincronizador(cola, api_viva).ciclo()

    assert resumen["enviados"] == 200
    assert set(recibidos) == ids
    assert len(recibidos) == 200
    assert cola.contar("enviado") == 200


def test_registro_enviado_dos_veces_no_se_duplica(ruta, api_viva):
    cola = ColaSync(ruta)
    sinc = Sincronizador(cola, api_viva)
    # Caso típico: el servidor sí lo recibió pero la respuesta llegó tarde.
    ids = [cola.encolar("venta", {"n": i}) for i in range(10)]
    lote = [
        {"uuid": u, "tipo": "venta", "payload": {}, "creado_en": "x"} for u in ids
    ]
    api_viva.post(RUTA_LOTE, json={"registros": lote})
    assert len(recibidos) == 10

    resumen = sinc.ciclo()  # la cola los reenvía

    assert resumen["enviados"] == 10
    assert len(recibidos) == 10
    assert cola.contar("enviado") == 10


def test_sin_conexion_en_el_ciclo_no_pierde_ni_cuenta_intentos(
    ruta, api_caida
):
    cola = ColaSync(ruta)
    for i in range(3):
        cola.encolar("venta", {"n": i})
    resumen = Sincronizador(cola, api_caida).ciclo()
    assert resumen["detenido_por"] == "SIN_CONEXION"
    assert cola.contar("pendiente") == 3
    con = sqlite3.connect(ruta)
    assert con.execute("SELECT MAX(intentos) FROM cola_sync").fetchone()[0] == 0


def test_sesion_vencida_deja_los_registros_pendientes(ruta, api_viva):
    cola = ColaSync(ruta)
    cola.encolar("venta", {})
    api_viva.establecer_token("token-malo")
    resumen = Sincronizador(cola, api_viva).ciclo()
    assert resumen["detenido_por"] == "TOKEN_INVALIDO"
    assert cola.contar("pendiente") == 1


def test_dos_ciclos_a_la_vez_no_se_solapan(ruta, api_viva):
    cola = ColaSync(ruta)
    cola.encolar("venta", {})
    sinc = Sincronizador(cola, api_viva)
    sinc._ciclo_activo.acquire()  # simula un ciclo en curso
    assert sinc.ciclo()["detenido_por"] == "CICLO_EN_CURSO"
    assert cola.contar("pendiente") == 1


def test_uuid_nuevo_es_distinto_cada_vez():
    assert nuevo_uuid() != nuevo_uuid()