"""Pantalla 2 · Panel del día (RF-ES01, RF-ES11 · CU-02, CU-16).

Las cifras llegan de la ventana principal (resumen del día cada 30 s), así la
consulta a la base se hace una sola vez para el panel, la ventanilla y el
resumen.
"""

from PySide6.QtWidgets import QGridLayout, QHBoxLayout, QVBoxLayout, QWidget

from foodpass_desktop.core.config import porcentaje_alerta, raciones_previstas
from foodpass_desktop.ui.widgets import Aviso, TarjetaMetrica, etiqueta

SERVICIOS = ("desayuno", "almuerzo", "refrigerio")


def calcular_alertas(resumen, conectado=True):
    """RF-ES11: servicio al umbral de lo previsto o sin conexión (no bloquean)."""
    alertas = []
    if not conectado:
        alertas.append(
            (
                "advertencia",
                "No hay conexión con la base de datos. Las entregas no se pueden registrar.",
            )
        )
    if resumen:
        previstas = raciones_previstas()
        umbral = porcentaje_alerta()
        for s in SERVICIOS:
            hechas = resumen["por_servicio"].get(s, 0)
            meta = max(previstas[s], 1)
            porcentaje = hechas * 100 / meta
            if porcentaje >= 100:
                alertas.append(
                    (
                        "atencion",
                        f"{s.capitalize()}: se superaron las raciones previstas ({hechas} de {meta}). Sigue entregando normalmente.",
                    )
                )
            elif porcentaje >= umbral:
                alertas.append(
                    (
                        "atencion",
                        f"{s.capitalize()} al {int(porcentaje)} % de lo previsto ({hechas} de {meta}).",
                    )
                )
    return alertas


class PanelView(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("paginaContenido")
        raiz = QVBoxLayout(self)
        raiz.setContentsMargins(36, 30, 36, 28)
        raiz.setSpacing(18)
        raiz.addWidget(etiqueta("Panel del día", "tituloPantalla", False))
        self.lbl_descripcion = etiqueta(
            "Así va la entrega del apoyo de alimentación hoy.", "descripcionPantalla"
        )
        raiz.addWidget(self.lbl_descripcion)

        rejilla = QGridLayout()
        rejilla.setSpacing(16)
        self.tarjetas = {}
        for i, s in enumerate(SERVICIOS):
            t = TarjetaMetrica(s.capitalize(), con_barra=True)
            self.tarjetas[s] = t
            rejilla.addWidget(t, 0, i)
        raiz.addLayout(rejilla)

        fila = QHBoxLayout()
        fila.setSpacing(16)
        self.total = TarjetaMetrica("Total de entregas hoy", destacada=True)
        self.anulados = TarjetaMetrica("Canjes anulados")
        self.manuales = TarjetaMetrica("Por documento (F2)")
        for t in (self.total, self.anulados, self.manuales):
            fila.addWidget(t)
        raiz.addLayout(fila)

        raiz.addWidget(etiqueta("Alertas", "tituloSeccion", False))
        self.caja_alertas = QVBoxLayout()
        self.caja_alertas.setSpacing(8)
        raiz.addLayout(self.caja_alertas)
        self.sin_alertas = Aviso("Sin alertas por ahora.", "info")
        raiz.addWidget(self.sin_alertas)
        raiz.addStretch()
        self.actualizar(None, conectado=True)

    def actualizar(self, resumen, conectado=True):
        if resumen is None:
            resumen = getattr(
                self, "_ultimo", None
            )  # sin conexión: conserva las cifras
        else:
            self._ultimo = resumen
        previstas = raciones_previstas()
        por_servicio = (resumen or {}).get("por_servicio", {})
        for s, t in self.tarjetas.items():
            hechas = por_servicio.get(s, 0)
            t.fijar(
                hechas,
                f"de {previstas[s]} previstas",
                hechas * 100 / max(previstas[s], 1),
            )
        if resumen:
            total = resumen["total"]
            self.total.fijar(
                total,
                "Aún no hay entregas hoy." if total == 0 else "entregas registradas",
            )
            self.anulados.fijar(resumen["anulados"], "liberaron el día del aprendiz")
            self.manuales.fijar(resumen["por_modalidad"]["manual"], "canjes sin código")
        while self.caja_alertas.count():
            w = self.caja_alertas.takeAt(0).widget()
            if w:
                w.deleteLater()
        alertas = calcular_alertas(resumen, conectado)
        for tipo, texto in alertas:
            self.caja_alertas.addWidget(Aviso(texto, tipo))
        self.sin_alertas.setVisible(not alertas)
