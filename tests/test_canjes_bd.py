"""Pruebas del canje directo en MySQL (C2.2-04) con una conexión simulada."""

import contextlib
from datetime import datetime, timedelta

import pymysql
import pytest

from foodpass_desktop.services.canje_service import CanjeService, interpretar_codigo
from foodpass_desktop.storage.canjes_bd import CanjesBD

FUTURO = datetime.now() + timedelta(days=1)
PASADO = datetime.now() - timedelta(days=1)
USUARIO = {
    "id": 7,
    "nombre": "Ana Gómez",
    "documento": "1001001001",
    "email": "ana@sena.edu.co",
    "activo": 1,
}
BENEFICIARIO = {"id": 3}
RESTAURANTE = {"id": 1}
CON_SERVICIO = {"Field": "servicio"}


class CursorFalso:
    """Devuelve en orden las filas de `respuestas` en cada fetchone()."""

    def __init__(self, respuestas, error_en=None):
        self.respuestas = list(respuestas)
        self.sql = []
        self.error_en = error_en
        self.lastrowid = 99

    def execute(self, sql, params=None):
        self.sql.append(sql)
        if self.error_en and self.error_en in sql:
            raise pymysql.err.IntegrityError(1062, "Duplicate entry")

    def fetchone(self):
        return self.respuestas.pop(0) if self.respuestas else None

    def __enter__(self):
        return self

    def __exit__(self, *exc):
        return False


class ConexionFalsa:
    def __init__(self, cursor):
        self._cursor = cursor
        self.commits = 0
        self.rollbacks = 0

    def cursor(self):
        return self._cursor

    def commit(self):
        self.commits += 1

    def rollback(self):
        self.rollbacks += 1


def repo_con(respuestas, error_en=None):
    cursor = CursorFalso(respuestas, error_en)
    conn = ConexionFalsa(cursor)

    @contextlib.contextmanager
    def conectar():
        yield conn

    return CanjesBD(conectar=conectar), conn, cursor


# ------------------------------------------------------------ interpretar_codigo
@pytest.mark.parametrize(
    "texto, tipo",
    [
        ("FP-A1B2C3", "movil"),
        ("fp-a1b2c3", None),  # el prefijo va en mayúscula
        ("FP-QR-1532-20261122113000-K7D2QX9MPA", "web"),
        ("FP-QR-" + "ab" * 32, "web"),
        ("FP-" + "cd" * 32, "web"),
        ("ef" * 32, "token"),
        ("1532", None),
        ("hola mundo", None),
        ("", None),
    ],
)
def test_interpretar_codigo(texto, tipo):
    resultado = interpretar_codigo(texto)
    assert (resultado[0] if resultado else None) == tipo


# ------------------------------------------------------------------- canjes
def test_qr_web_valido_se_entrega_y_actualiza_el_canje_pendiente():
    repo, conn, cur = repo_con(
        [
            {"id": 50, "usuario_id": 7, "estado": "pendiente", "expira_en": FUTURO},
            USUARIO,
            BENEFICIARIO,
            CON_SERVICIO,
            None,  # sin canje hoy
        ]
    )
    tipo, datos = repo.canjear_codigo("Almuerzo", "web", "FP-QR-x")
    assert tipo == "entregado"
    assert datos["nombre"] == "Ana Gómez"
    assert any(s.startswith("UPDATE canjes") for s in cur.sql)
    assert conn.commits == 1


def test_codigo_movil_valido_inserta_canje_y_marca_usado():
    repo, conn, cur = repo_con(
        [
            {"id": 9, "usuario_id": 7, "expires_at": FUTURO, "usado": 0},
            USUARIO,
            BENEFICIARIO,
            CON_SERVICIO,
            None,
            RESTAURANTE,
        ]
    )
    tipo, _ = repo.canjear_codigo("Desayuno", "movil", "FP-A1B2C3")
    assert tipo == "entregado"
    assert any(s.startswith("INSERT INTO canjes") for s in cur.sql)
    assert any("UPDATE qr_tokens SET usado = 1" in s for s in cur.sql)


def test_segundo_canje_del_dia_se_rechaza_aunque_el_codigo_sea_nuevo():
    previo = {
        "servicio": "almuerzo",
        "detalle": "",
        "actualizado_en": datetime(2026, 11, 23, 12, 5),
    }
    repo, conn, _ = repo_con(
        [
            {"id": 10, "usuario_id": 7, "expires_at": FUTURO, "usado": 0},
            USUARIO,
            BENEFICIARIO,
            CON_SERVICIO,
            previo,
        ]
    )
    tipo, datos = repo.canjear_codigo("Refrigerio", "movil", "FP-D4E5F6")
    assert tipo == "ya_recibio"
    assert datos["servicio"] == "Almuerzo"
    assert conn.rollbacks == 1 and conn.commits == 0


def test_lecturas_simultaneas_la_clave_unica_gana():
    repo, conn, _ = repo_con(
        [
            {"id": 9, "usuario_id": 7, "expires_at": FUTURO, "usado": 0},
            USUARIO,
            BENEFICIARIO,
            CON_SERVICIO,
            None,
            RESTAURANTE,
        ],
        error_en="INSERT INTO canjes",
    )
    tipo, _ = repo.canjear_codigo("Almuerzo", "movil", "FP-A1B2C3")
    assert tipo == "ya_recibio"
    assert conn.rollbacks == 1


def test_no_beneficiario():
    repo, _, _ = repo_con(
        [{"id": 9, "usuario_id": 7, "expires_at": FUTURO, "usado": 0}, USUARIO, None]
    )
    assert repo.canjear_codigo("Almuerzo", "movil", "FP-A1B2C3")[0] == "no_beneficiario"


def test_codigo_usado_o_vencido():
    usado, _, _ = repo_con(
        [{"id": 9, "usuario_id": 7, "expires_at": FUTURO, "usado": 1}]
    )
    assert usado.canjear_codigo("Almuerzo", "movil", "FP-A1B2C3")[0] == "no_reconocido"
    vencido, _, _ = repo_con(
        [{"id": 50, "usuario_id": 7, "estado": "pendiente", "expira_en": PASADO}]
    )
    tipo, datos = vencido.canjear_codigo("Almuerzo", "web", "FP-QR-x")
    assert tipo == "no_reconocido" and "venció" in datos["mensaje"]


def test_manual_beneficiario_sin_cuenta():
    repo, _, _ = repo_con([None, {"id": 3}])
    tipo, datos = repo.canjear_documento("Almuerzo", "1001001001", "Sin batería")
    assert tipo == "no_beneficiario"
    assert "cuenta" in datos["mensaje"]


def test_sin_conexion_a_la_bd():
    @contextlib.contextmanager
    def conectar():
        raise pymysql.err.OperationalError(2003, "Can't connect")
        yield

    tipo, _ = CanjesBD(conectar=conectar).canjear_codigo(
        "Almuerzo", "movil", "FP-A1B2C3"
    )
    assert tipo == "error_conexion"


# ---------------------------------------------------------------- servicio
class RepoFalso:
    def __init__(self):
        self.llamadas = []

    def canjear_codigo(self, servicio, tipo, codigo):
        self.llamadas.append((servicio, tipo, codigo))
        return "entregado", {"nombre": "X"}

    def canjear_documento(self, servicio, documento, motivo):
        self.llamadas.append((servicio, documento, motivo))
        return "entregado", {"nombre": "X"}


def test_servicio_usa_el_repositorio_y_rechaza_texto_desconocido():
    repo = RepoFalso()
    servicio = CanjeService(api_client=object(), repositorio=repo)
    assert servicio.registrar_canje_qr("Almuerzo", "FP-A1B2C3").tipo == "entregado"
    assert repo.llamadas[-1] == ("Almuerzo", "movil", "FP-A1B2C3")
    assert servicio.registrar_canje_qr("Almuerzo", "1532").tipo == "no_reconocido"
    assert (
        servicio.registrar_canje_manual("Almuerzo", "1001001001", "Sin batería").tipo
        == "entregado"
    )
