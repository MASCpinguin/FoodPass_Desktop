"""Configuración común de las pruebas.

- No leen el .env del equipo (datos reales de conexión).
- Al terminar cada prueba se cierran y destruyen las ventanas de Qt que haya
  creado, mientras Qt sigue vivo. Sin esto, Python las destruye al salir en
  un orden cualquiera, a veces después de Qt, y el proceso se cae aunque
  todas las pruebas hayan pasado (en el CI: «Bus error», código 134/135).
"""

import os

import pytest

os.environ["FOODPASS_SIN_ENV"] = "1"


def _limpiar_ventanas_qt():
    try:
        from PySide6.QtCore import QCoreApplication, QEvent
        from PySide6.QtWidgets import QApplication
    except Exception:  # Qt no disponible en este equipo
        return
    app = QApplication.instance()
    if app is None:
        return
    for ventana in app.topLevelWidgets():
        ventana.close()
        ventana.deleteLater()
    QCoreApplication.sendPostedEvents(None, QEvent.Type.DeferredDelete)
    app.processEvents()


@pytest.fixture(autouse=True)
def _ventanas_qt_limpias():
    yield
    _limpiar_ventanas_qt()


def pytest_sessionfinish(session, exitstatus):
    """Última limpieza antes de que Python empiece a cerrar."""
    _limpiar_ventanas_qt()
