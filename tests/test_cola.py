import pytest

from foodpass_desktop.storage.cola import ColaSync, nuevo_uuid


@pytest.fixture
def ruta(tmp_path):
    return tmp_path / "cola.db"


def test_encolar_guarda_con_uuid(ruta):
    cola = ColaSync(ruta)
    uid = cola.encolar("venta", {"total": 5000})
    assert len(uid) == 36
    assert cola.contar("pendiente") == 1


def test_tipo_invalido(ruta):
    with pytest.raises(ValueError):
        ColaSync(ruta).encolar("regalo", {})


def test_mismo_uuid_no_se_duplica(ruta):
    cola = ColaSync(ruta)
    uid = nuevo_uuid()
    cola.encolar("canje", {"a": 1}, uuid_registro=uid)
    cola.encolar("canje", {"a": 1}, uuid_registro=uid)
    assert cola.contar() == 1


def test_lotes_de_50_en_orden(ruta):
    cola = ColaSync(ruta)
    ids = [cola.encolar("venta", {"n": i}) for i in range(120)]
    lote1 = cola.tomar_lote()
    assert len(lote1) == 50
    assert [r["uuid"] for r in lote1] == ids[:50]  # orden de creación
    assert len(cola.tomar_lote()) == 50
    assert len(cola.tomar_lote()) == 20
    assert cola.tomar_lote() == []


def test_lote_tomado_no_se_toma_otra_vez(ruta):
    cola = ColaSync(ruta)
    cola.encolar("venta", {})
    assert len(cola.tomar_lote()) == 1
    assert cola.tomar_lote() == []
    assert cola.contar("enviando") == 1


def test_exito_parcial(ruta):
    cola = ColaSync(ruta)
    for i in range(4):
        cola.encolar("venta", {"n": i})
    lote = cola.tomar_lote()
    ok = [r["uuid"] for r in lote[:3]]
    mal = [lote[3]["uuid"]]
    cola.marcar_enviados(ok)
    cola.devolver_a_pendiente(mal, error="VALIDACION")
    assert cola.contar("enviado") == 3
    assert cola.contar("pendiente") == 1


def test_reinicio_con_200_en_cola_llegan_todos_sin_duplicados(ruta):
    cola = ColaSync(ruta)
    ids = {cola.encolar("venta", {"n": i}) for i in range(200)}
    cola.tomar_lote()  # se corta a mitad de un envío
    cola.cerrar()

    cola = ColaSync(ruta)  # reinicio de la app
    assert cola.contar("pendiente") == 200
    recibidos = []
    while lote := cola.tomar_lote():
        recibidos += [r["uuid"] for r in lote]
        cola.marcar_enviados([r["uuid"] for r in lote])
    assert len(recibidos) == 200
    assert set(recibidos) == ids
    assert cola.contar("enviado") == 200