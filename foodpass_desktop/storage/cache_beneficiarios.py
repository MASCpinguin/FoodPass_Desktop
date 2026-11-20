import json
import os
from pathlib import Path

from cryptography.fernet import Fernet, InvalidToken


def obtener_o_crear_clave(ruta_clave: str | Path = "cache.key") -> bytes:
    """
    Obtiene la clave Fernet desde la variable de entorno FOODPASS_CACHE_KEY
    o la crea/lee localmente desde ruta_clave.
    """
    clave_env = os.environ.get("FOODPASS_CACHE_KEY", "").strip()
    if clave_env:
        return clave_env.encode("utf-8")

    archivo_clave = Path(ruta_clave)
    if archivo_clave.exists():
        return archivo_clave.read_bytes().strip()

    nueva_clave = Fernet.generate_key()
    archivo_clave.write_bytes(nueva_clave)
    return nueva_clave


def guardar_cache_beneficiarios(
    beneficiarios: list[dict],
    ruta_cache: str | Path = "beneficiarios_cache.bin",
    ruta_clave: str | Path = "cache.key",
) -> Path:
    """Cifra y guarda la lista de beneficiarios en disco."""
    clave = obtener_o_crear_clave(ruta_clave)
    fernet = Fernet(clave)

    contenido_json = json.dumps(beneficiarios, ensure_ascii=False).encode("utf-8")
    token_cifrado = fernet.encrypt(contenido_json)

    destino = Path(ruta_cache)
    destino.write_bytes(token_cifrado)
    return destino


def cargar_cache_beneficiarios(
    ruta_cache: str | Path = "beneficiarios_cache.bin",
    ruta_clave: str | Path = "cache.key",
) -> list[dict]:
    """Carga y descifra la lista de beneficiarios desde disco."""
    archivo_cache = Path(ruta_cache)
    if not archivo_cache.exists():
        return []

    clave = obtener_o_crear_clave(ruta_clave)
    fernet = Fernet(clave)

    try:
        datos_cifrados = archivo_cache.read_bytes()
        contenido_json = fernet.decrypt(datos_cifrados).decode("utf-8")
        datos = json.loads(contenido_json)
        return datos if isinstance(datos, list) else []
    except (InvalidToken, OSError, json.JSONDecodeError):
        return []