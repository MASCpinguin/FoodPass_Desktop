from cryptography.fernet import Fernet
from foodpass_desktop.storage.cache_beneficiarios import (
    cargar_beneficiarios_cache,
    guardar_beneficiarios_cache,
)


def test_guardar_y_cargar_devuelve_mismos_datos(tmp_path):
    ruta_cache = tmp_path / "beneficiarios_cache.bin"
    ruta_llave = tmp_path / "cache.key"
    datos = [{"id": 1, "nombre": "Ana Pérez"}]

    guardar_beneficiarios_cache(datos, ruta_cache=ruta_cache, ruta_llave=ruta_llave)
    assert cargar_beneficiarios_cache(ruta_cache=ruta_cache, ruta_llave=ruta_llave) == datos


def test_llave_incorrecta_devuelve_lista_vacia(tmp_path):
    ruta_cache = tmp_path / "beneficiarios_cache.bin"
    ruta_llave_ok = tmp_path / "cache_ok.key"
    ruta_llave_mal = tmp_path / "cache_mal.key"
    ruta_llave_mal.write_bytes(Fernet.generate_key())

    guardar_beneficiarios_cache([{"id": 1}], ruta_cache=ruta_cache, ruta_llave=ruta_llave_ok)
    assert cargar_beneficiarios_cache(ruta_cache=ruta_cache, ruta_llave=ruta_llave_mal) == []