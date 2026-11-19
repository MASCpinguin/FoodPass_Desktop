"""Dispara la sincronización cada 30 s sin congelar la ventana."""

from PySide6.QtCore import QObject, QTimer

from foodpass_desktop.api.trabajador import ejecutar_en_segundo_plano

INTERVALO_MS = 30_000


class TemporizadorSync(QObject):
    def __init__(self, sincronizador, intervalo_ms=INTERVALO_MS, parent=None):
        super().__init__(parent)
        self._sincronizador = sincronizador
        self._timer = QTimer(self)
        self._timer.setInterval(intervalo_ms)
        self._timer.timeout.connect(self._tick)

    def iniciar(self):
        self._timer.start()

    def detener(self):
        self._timer.stop()

    def _tick(self):
        ejecutar_en_segundo_plano(self._sincronizador.ciclo)