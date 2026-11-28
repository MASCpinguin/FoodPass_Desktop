"""Ejecuta llamadas a la API en segundo plano, sin congelar la ventana."""

from PySide6.QtCore import QObject, QRunnable, QThreadPool, Signal

MAX_PARALELAS = 4

_pool = QThreadPool()
_pool.setMaxThreadCount(MAX_PARALELAS)


class _Senales(QObject):
    exito = Signal(object)
    error = Signal(object)


class _Tarea(QRunnable):
    def __init__(self, funcion, args, kwargs):
        super().__init__()
        self.senales = _Senales()
        self._funcion = funcion
        self._args = args
        self._kwargs = kwargs

    def run(self):
        try:
            resultado = self._funcion(*self._args, **self._kwargs)
        except Exception as e:
            self.senales.error.emit(e)
        else:
            self.senales.exito.emit(resultado)


def ejecutar_en_segundo_plano(funcion, *args, al_exito=None, al_error=None, **kwargs):
    """Corre `funcion(*args, **kwargs)` en un hilo del pool (máx. 4).

    `al_exito(resultado)` y `al_error(excepcion)` se ejecutan en el hilo de
    la interfaz si son métodos de un QWidget (no uses lambdas).
    """
    tarea = _Tarea(funcion, args, kwargs)
    if al_exito:
        tarea.senales.exito.connect(al_exito)
    if al_error:
        tarea.senales.error.connect(al_error)
    _pool.start(tarea)
