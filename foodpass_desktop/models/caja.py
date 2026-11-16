"""Modelos del cierre de caja (RF-ES05).

Representan lo que responde la API en EP-24 (resumen) y EP-25 (cierre).
"""

from dataclasses import dataclass, field
from datetime import date

METODOS_PAGO = ("nequi", "transferencia", "efectivo")
SERVICIOS = ("desayuno", "almuerzo", "refrigerio")


@dataclass(frozen=True)
class Conteo:
    """Cantidad de ventas y su valor en pesos."""

    n: int = 0
    total: int = 0

    @classmethod
    def desde_api(cls, datos):
        datos = datos or {}
        return cls(n=int(datos.get("n", 0)), total=int(datos.get("total", 0)))


@dataclass(frozen=True)
class ResumenCaja:
    """Resumen del día calculado por la API para el cierre."""

    fecha: date
    ventas_por_metodo: dict = field(default_factory=dict)
    total: int = 0
    n_ventas: int = 0
    canjes_por_servicio: dict = field(default_factory=dict)
    pedidos_web_atendidos: int = 0
    anuladas: Conteo = Conteo()
    cerrada: bool = False

    @property
    def total_canjes(self):
        return sum(self.canjes_por_servicio.values())

    @property
    def sin_movimientos(self):
        return self.n_ventas == 0 and self.total_canjes == 0

    @classmethod
    def desde_api(cls, datos):
        metodos = datos.get("ventas_por_metodo") or {}
        servicios = datos.get("canjes_por_servicio") or {}
        return cls(
            fecha=date.fromisoformat(datos["fecha"]),
            ventas_por_metodo={m: Conteo.desde_api(metodos.get(m)) for m in METODOS_PAGO},
            total=int(datos.get("total", 0)),
            n_ventas=int(datos.get("n_ventas", 0)),
            canjes_por_servicio={s: int(servicios.get(s, 0)) for s in SERVICIOS},
            pedidos_web_atendidos=int(datos.get("pedidos_web_atendidos", 0)),
            anuladas=Conteo.desde_api(datos.get("anuladas")),
            cerrada=bool(datos.get("cerrada", False)),
        )


@dataclass(frozen=True)
class CierreCaja:
    """Cierre guardado. Es inmutable: no se edita después de creado."""

    id: int
    resumen: ResumenCaja
    observacion: str
    cerrado_por: str
    creado: str
    rechazados: list = field(default_factory=list)

    @classmethod
    def desde_api(cls, datos):
        cierre = datos["cierre"]
        return cls(
            id=int(cierre["id"]),
            resumen=ResumenCaja.desde_api({**cierre, "cerrada": True}),
            observacion=cierre.get("observacion", ""),
            cerrado_por=cierre.get("cerrado_por", ""),
            creado=cierre.get("creado", ""),
            rechazados=list(datos.get("rechazados") or []),
        )
