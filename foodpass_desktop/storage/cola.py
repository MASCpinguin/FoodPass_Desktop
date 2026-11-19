"""Cola local persistente (SQLite) para el registro diferido.

Guarda canjes, ventas y anulaciones, cada uno con su UUID, mientras no haya
conexión. Estados: pendiente -> enviando -> enviado.
"""

import json
import sqlite3
import threading
import uuid
from datetime import datetime, timezone
from pathlib import Path

TIPOS = ("canje", "venta", "anulacion")
TAMANO_LOTE = 50

ESQUEMA = """
CREATE TABLE IF NOT EXISTS cola_sync (
    uuid         TEXT PRIMARY KEY,
    tipo         TEXT NOT NULL CHECK (tipo IN ('canje','venta','anulacion')),
    payload      TEXT NOT NULL,
    estado       TEXT NOT NULL DEFAULT 'pendiente'
                 CHECK (estado IN ('pendiente','enviando','enviado')),
    intentos     INTEGER NOT NULL DEFAULT 0,
    ultimo_error TEXT,
    creado_en    TEXT NOT NULL,
    enviado_en   TEXT
);
CREATE INDEX IF NOT EXISTS idx_cola_estado_creado
    ON cola_sync (estado, creado_en);
"""


def nuevo_uuid():
    """Genera el UUID del registro. Hazlo ANTES de intentar enviarlo."""
    return str(uuid.uuid4())


def ahora_iso():
    return datetime.now(timezone.utc).isoformat(timespec="microseconds")


class ColaSync:
    def __init__(self, ruta="cola_sync.db"):
        if str(ruta) != ":memory:":
            Path(ruta).parent.mkdir(parents=True, exist_ok=True)
        # Una sola conexión compartida entre hilos, protegida con un candado.
        self._con = sqlite3.connect(str(ruta), check_same_thread=False)
        self._con.row_factory = sqlite3.Row
        self._lock = threading.Lock()
        self._con.execute("PRAGMA journal_mode=WAL")
        self._con.execute("PRAGMA synchronous=FULL")
        self._con.executescript(ESQUEMA)
        # Si la app se cerró a mitad de un envío, esos registros no se
        # perdieron: solo hay que volver a intentarlos.
        self.recuperar_en_envio()

    def cerrar(self):
        with self._lock:
            self._con.close()

    def encolar(self, tipo, payload, uuid_registro=None, creado_en=None):
        """Guarda un registro como pendiente. Devuelve su UUID.

        Si el UUID ya existe no se duplica (INSERT OR IGNORE).
        """
        if tipo not in TIPOS:
            raise ValueError(f"Tipo inválido: {tipo!r}")
        uuid_registro = uuid_registro or nuevo_uuid()
        with self._lock, self._con:
            self._con.execute(
                "INSERT OR IGNORE INTO cola_sync (uuid, tipo, payload, creado_en)"
                " VALUES (?, ?, ?, ?)",
                (uuid_registro, tipo, json.dumps(payload), creado_en or ahora_iso()),
            )
        return uuid_registro

    def tomar_lote(self, maximo=TAMANO_LOTE):
        """Toma hasta `maximo` pendientes (los más antiguos) y los marca
        como 'enviando' para que ningún otro ciclo los vuelva a tomar."""
        with self._lock, self._con:
            filas = self._con.execute(
                "SELECT uuid, tipo, payload, creado_en FROM cola_sync"
                " WHERE estado = 'pendiente'"
                " ORDER BY creado_en, rowid LIMIT ?",
                (maximo,),
            ).fetchall()
            self._con.executemany(
                "UPDATE cola_sync SET estado = 'enviando' WHERE uuid = ?",
                [(f["uuid"],) for f in filas],
            )
        return [
            {
                "uuid": f["uuid"],
                "tipo": f["tipo"],
                "payload": json.loads(f["payload"]),
                "creado_en": f["creado_en"],
            }
            for f in filas
        ]

    def marcar_enviados(self, uuids):
        """Solo para los que el servidor confirmó, uno por uno."""
        with self._lock, self._con:
            self._con.executemany(
                "UPDATE cola_sync SET estado = 'enviado', enviado_en = ?,"
                " ultimo_error = NULL WHERE uuid = ?",
                [(ahora_iso(), u) for u in uuids],
            )

    def devolver_a_pendiente(self, uuids, error=None, contar_intento=True):
        """Los que fallaron vuelven a la cola. Si fue por falta de red o
        sesión vencida, usa contar_intento=False."""
        suma = 1 if contar_intento else 0
        with self._lock, self._con:
            self._con.executemany(
                "UPDATE cola_sync SET estado = 'pendiente',"
                " intentos = intentos + ?, ultimo_error = ? WHERE uuid = ?",
                [(suma, error, u) for u in uuids],
            )

    def recuperar_en_envio(self):
        with self._lock, self._con:
            self._con.execute(
                "UPDATE cola_sync SET estado = 'pendiente'"
                " WHERE estado = 'enviando'"
            )

    def contar(self, estado=None):
        sql = "SELECT COUNT(*) FROM cola_sync"
        args = ()
        if estado:
            sql += " WHERE estado = ?"
            args = (estado,)
        with self._lock:
            return self._con.execute(sql, args).fetchone()[0]