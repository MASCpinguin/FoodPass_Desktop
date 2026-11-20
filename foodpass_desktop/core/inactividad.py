"""Detecta cuándo el operador deja de usar el equipo (RF-ES25).

Escucha el teclado y el mouse de toda la aplicación. Si pasa el tiempo
configurado sin actividad, emite `inactivo` y se detiene hasta que se
vuelva a llamar a `iniciar()`.

Una lectura del lector de QR cuenta como actividad: el lector escribe como un
teclado, así que en hora pico la pantalla nunca se bloquea.
"""

from PySide6.QtCore import QEvent, QObject, QTimer, Signal

EVENTOS_DE_ACTIVIDAD = {
    QEvent.Type.KeyPress,
    QEvent.Type.MouseButtonPress,
    QEvent.Type.MouseMove,
    QEvent.Type.Wheel,
}


class DetectorInactividad(QObject):
    inactivo = Signal()

    def __init__(self, app, minutos, parent=None):
        super().__init__(parent)
        self._app = app
        self._temporizador = QTimer(self)
        self._temporizador.setSingleShot(True)
        self._temporizador.timeout.connect(self.inactivo.emit)
        self.cambiar_minutos(minutos)

    def cambiar_minutos(self, minutos):
        """Para cuando Configuración (T33) permita cambiar el tiempo."""
        self._temporizador.setInterval(max(1, int(minutos * 60_000)))

    def iniciar(self):
        self._app.installEventFilter(self)
        self._temporizador.start()

    def detener(self):
        self._app.removeEventFilter(self)
        self._temporizador.stop()

    @property
    def activo(self):
        return self._temporizador.isActive()

    def eventFilter(self, objeto, evento):
        if evento.type() in EVENTOS_DE_ACTIVIDAD and self._temporizador.isActive():
            self._temporizador.start()  # reinicia la cuenta
        return False  # nunca se come el evento
