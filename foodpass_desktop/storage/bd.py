"""Conexión directa a MySQL (C2.2-04).

La API FoodPass solo ofrece al escritorio el inicio de sesión y la consulta
del QR. Canjes, beneficiarios y reportes se leen y escriben directamente en
la base foodpass_v2 con PyMySQL. Los datos de conexión van en el archivo .env
que acompaña al ejecutable (nunca dentro del código ni del .exe).
"""

import contextlib
import os

import pymysql
import pymysql.cursors


def configurada() -> bool:
    """True si el .env trae los datos de la base de datos."""
    return bool(os.getenv("DB_HOST", "").strip())


def _parametros() -> dict:
    return {
        "host": os.getenv("DB_HOST", "127.0.0.1").strip(),
        "port": int(os.getenv("DB_PORT", "3306") or 3306),
        "user": os.getenv("DB_USER", "root"),
        "password": os.getenv("DB_PASSWORD", ""),
        "database": os.getenv("DB_NAME", "foodpass_v2"),
        "charset": "utf8mb4",
        "autocommit": False,
        "cursorclass": pymysql.cursors.DictCursor,
        # Tiempos cortos: si la BD no responde, la ventanilla avisa rápido.
        "connect_timeout": 3,
        "read_timeout": 5,
        "write_timeout": 5,
    }


@contextlib.contextmanager
def conexion():
    """Abre una conexión, la entrega y la cierra siempre.

    Uso:
        with conexion() as conn:
            with conn.cursor() as cur:
                cur.execute("SELECT 1")
            conn.commit()
    """
    conn = pymysql.connect(**_parametros())
    try:
        yield conn
    finally:
        conn.close()


def probar() -> bool:
    """Comprueba que la base responde (para el indicador de conexión)."""
    try:
        with conexion() as conn, conn.cursor() as cur:
            cur.execute("SELECT 1")
        return True
    except pymysql.MySQLError:
        return False
