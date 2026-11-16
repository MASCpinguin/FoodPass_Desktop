"""Servicio de cierre de caja (T30 · RF-ES05).

Consulta el resumen del día (EP-24) y guarda el cierre (EP-25).

El servicio no depende de una clase concreta de cliente HTTP: recibe cualquier
objeto con estos dos métodos (el cliente de API de T03 los cumple):

    get(ruta, params=None) -> dict
    post(ruta, json=None) -> dict

Si la API responde con error, el cliente debe lanzar una excepción con el
atributo `codigo` (por ejemplo "YA_CERRADA"), como indica el 05 Contrato.

La cola local (T06) es opcional: si se entrega, debe tener
`pendientes() -> int` y `enviar() -> None`. Antes de cerrar se envía la cola;
si quedan registros sin enviar, se lanza ColaPendiente (el cierre provisional
sin conexión se resuelve en T46).
"""

from datetime import date

from foodpass_desktop.models.caja import CierreCaja, ResumenCaja

RUTA_RESUMEN = "/caja/resumen"
RUTA_CIERRES = "/caja/cierres"


class ErrorCaja(Exception):
    """Error al consultar o cerrar la caja. `mensaje` es apto para mostrar."""

    def __init__(self, mensaje, codigo=None):
        super().__init__(mensaje)
        self.mensaje = mensaje
        self.codigo = codigo


class CajaYaCerrada(ErrorCaja):
    pass


class ColaPendiente(ErrorCaja):
    pass


MENSAJES = {
    "YA_CERRADA": "La caja de este día ya está cerrada.",
    "COLA_PENDIENTE": "Hay registros sin enviar. Espera a que se sincronicen.",
    "TOKEN_INVALIDO": "La sesión venció. Inicia sesión de nuevo.",
    "DATOS_INVALIDOS": "La fecha del cierre no es válida.",
}


def formato_pesos(valor):
    """32000 -> '$ 32.000' (pesos colombianos, sin decimales)."""
    return "$ " + f"{int(valor):,}".replace(",", ".")


class CajaService:

    def __init__(self, cliente, cola=None):
        self.cliente = cliente
        self.cola = cola

    def obtener_resumen(self, fecha=None):
        """Resumen calculado por la API para la fecha (hoy si no se indica)."""
        params = {"fecha": _texto_fecha(fecha)} if fecha else None
        datos = self._llamar(self.cliente.get, RUTA_RESUMEN, params=params)
        return ResumenCaja.desde_api(datos)

    def cerrar_caja(self, fecha=None, observacion=""):
        """Envía la cola pendiente y guarda el cierre definitivo del día."""
        self._enviar_cola()
        cuerpo = {
            "observacion": (observacion or "").strip(),
            "provisional_local": None,
        }
        # Sin fecha, la API usa el día de Bogotá según su propia hora (RN12).
        if fecha:
            cuerpo["fecha"] = _texto_fecha(fecha)
        datos = self._llamar(self.cliente.post, RUTA_CIERRES, json=cuerpo)
        return CierreCaja.desde_api(datos)

    def _enviar_cola(self):
        if self.cola is None or self.cola.pendientes() == 0:
            return
        self.cola.enviar()
        pendientes = self.cola.pendientes()
        if pendientes:
            raise ColaPendiente(
                f"Quedan {pendientes} registros sin enviar. "
                "No se puede hacer el cierre definitivo.",
                "COLA_PENDIENTE",
            )

    def _llamar(self, metodo, ruta, **kwargs):
        try:
            return metodo(ruta, **kwargs)
        except ErrorCaja:
            raise
        except Exception as exc:  # el cliente de API decide el tipo concreto
            codigo = getattr(exc, "codigo", None)
            if codigo is None:
                raise ErrorCaja("No hay conexión con el servidor.", "SIN_CONEXION") from exc
            clase = {"YA_CERRADA": CajaYaCerrada, "COLA_PENDIENTE": ColaPendiente}.get(
                codigo, ErrorCaja
            )
            mensaje = MENSAJES.get(codigo) or getattr(exc, "mensaje", None) or str(exc)
            raise clase(mensaje, codigo) from exc


def _texto_fecha(fecha):
    return fecha.isoformat() if isinstance(fecha, date) else str(fecha)
