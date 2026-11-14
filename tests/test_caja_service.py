"""Pruebas unitarias del servicio de cierre de caja (T30 · RF-ES05)."""

from datetime import date

import pytest

from foodpass_desktop.services.caja_service import (
    CajaService,
    CajaYaCerrada,
    ColaPendiente,
    ErrorCaja,
    formato_pesos,
)

RESUMEN = {
    "fecha": "2026-11-14",
    "ventas_por_metodo": {
        "nequi": {"n": 3, "total": 25000},
        "transferencia": {"n": 2, "total": 24500},
        "efectivo": {"n": 0, "total": 0},
    },
    "total": 49500,
    "n_ventas": 5,
    "canjes_por_servicio": {"desayuno": 12, "almuerzo": 18, "refrigerio": 7},
    "pedidos_web_atendidos": 2,
    "anuladas": {"n": 1, "total": 6000},
    "cerrada": False,
}


class ErrorApiFalso(Exception):
    def __init__(self, codigo, mensaje="error"):
        super().__init__(mensaje)
        self.codigo = codigo
        self.mensaje = mensaje


class ClienteFalso:
    """Registra las llamadas y responde lo que se le indique."""

    def __init__(self, respuesta=None, error=None):
        self.respuesta = respuesta
        self.error = error
        self.llamadas = []

    def get(self, ruta, params=None):
        return self._responder("GET", ruta, params)

    def post(self, ruta, json=None):
        return self._responder("POST", ruta, json)

    def _responder(self, metodo, ruta, datos):
        self.llamadas.append((metodo, ruta, datos))
        if self.error:
            raise self.error
        return self.respuesta


class ColaFalsa:
    def __init__(self, pendientes, se_vacia=True):
        self._pendientes = pendientes
        self.se_vacia = se_vacia
        self.enviada = False

    def pendientes(self):
        return self._pendientes

    def enviar(self):
        self.enviada = True
        if self.se_vacia:
            self._pendientes = 0


def respuesta_cierre():
    return {
        "cierre": {**{k: v for k, v in RESUMEN.items() if k != "cerrada"},
                   "id": 1, "observacion": "Todo en orden",
                   "cerrado_por": "Operador de prueba",
                   "creado": "2026-11-14T18:05:00-05:00"},
        "diferencias": None,
        "rechazados": [],
    }


def test_resumen_se_convierte_en_modelo():
    servicio = CajaService(ClienteFalso(RESUMEN))
    resumen = servicio.obtener_resumen()

    assert resumen.fecha == date(2026, 11, 14)
    assert resumen.total == 49500
    assert resumen.n_ventas == 5
    assert resumen.ventas_por_metodo["nequi"].total == 25000
    assert resumen.total_canjes == 37
    assert resumen.anuladas.n == 1
    assert resumen.cerrada is False


def test_resumen_sin_fecha_no_envia_parametros():
    cliente = ClienteFalso(RESUMEN)
    CajaService(cliente).obtener_resumen()
    assert cliente.llamadas == [("GET", "/caja/resumen", None)]


def test_resumen_con_fecha_la_envia_en_formato_iso():
    cliente = ClienteFalso(RESUMEN)
    CajaService(cliente).obtener_resumen(date(2026, 11, 13))
    assert cliente.llamadas[0][2] == {"fecha": "2026-11-13"}


def test_dia_sin_movimientos():
    vacio = {"fecha": "2026-11-14"}
    resumen = CajaService(ClienteFalso(vacio)).obtener_resumen()
    assert resumen.sin_movimientos
    assert resumen.total == 0
    assert resumen.ventas_por_metodo["efectivo"].n == 0


def test_cerrar_caja_envia_fecha_y_observacion():
    cliente = ClienteFalso(respuesta_cierre())
    cierre = CajaService(cliente).cerrar_caja(date(2026, 11, 14), "  Todo en orden ")

    metodo, ruta, cuerpo = cliente.llamadas[0]
    assert (metodo, ruta) == ("POST", "/caja/cierres")
    assert cuerpo == {"fecha": "2026-11-14", "observacion": "Todo en orden",
                      "provisional_local": None}
    assert cierre.id == 1
    assert cierre.resumen.cerrada is True
    assert cierre.resumen.total == 49500


def test_cerrar_caja_dos_veces_lanza_caja_ya_cerrada():
    servicio = CajaService(ClienteFalso(error=ErrorApiFalso("YA_CERRADA")))
    with pytest.raises(CajaYaCerrada) as error:
        servicio.cerrar_caja(date(2026, 11, 14))
    assert error.value.mensaje == "La caja de este día ya está cerrada."


def test_sin_conexion_da_mensaje_claro():
    servicio = CajaService(ClienteFalso(error=ConnectionError("timeout")))
    with pytest.raises(ErrorCaja) as error:
        servicio.obtener_resumen()
    assert error.value.codigo == "SIN_CONEXION"


def test_envia_la_cola_antes_de_cerrar():
    cola = ColaFalsa(pendientes=3)
    cliente = ClienteFalso(respuesta_cierre())
    CajaService(cliente, cola=cola).cerrar_caja(date(2026, 11, 14))
    assert cola.enviada
    assert cliente.llamadas[0][1] == "/caja/cierres"


def test_si_la_cola_no_se_vacia_no_hace_cierre_definitivo():
    cola = ColaFalsa(pendientes=3, se_vacia=False)
    cliente = ClienteFalso(respuesta_cierre())
    with pytest.raises(ColaPendiente):
        CajaService(cliente, cola=cola).cerrar_caja(date(2026, 11, 14))
    assert cliente.llamadas == []  # no se intentó guardar el cierre


@pytest.mark.parametrize("valor, esperado", [
    (0, "$ 0"), (4500, "$ 4.500"), (49500, "$ 49.500"), (1250000, "$ 1.250.000"),
])
def test_formato_pesos(valor, esperado):
    assert formato_pesos(valor) == esperado
