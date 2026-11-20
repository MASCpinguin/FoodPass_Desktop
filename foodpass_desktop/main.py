import ctypes
import sys
from pathlib import Path

from PySide6.QtGui import QIcon
from PySide6.QtWidgets import QApplication

from foodpass_desktop.api.cliente import cliente
from foodpass_desktop.core.config import minutos_bloqueo
from foodpass_desktop.core.sesion import ControladorSesion
from foodpass_desktop.services.auth_service import AuthService
from foodpass_desktop.storage.credenciales import crear_almacen


ICONO = Path(__file__).resolve().parent / "resources" / "icons" / "foodpass.ico"


def main():
    if sys.platform == "win32":
        ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID(
            "SENA.FoodPass.Escritorio"
        )
    app = QApplication(sys.argv)
    app.setWindowIcon(QIcon(str(ICONO)))
    tema = Path(__file__).resolve().parent / "resources" / "tema.qss"
    app.setStyleSheet(tema.read_text(encoding="utf-8"))

    # T05: la app arranca en el inicio de sesión; la ventana principal se
    # abre solo con un token válido.
    auth = AuthService(cliente, crear_almacen())
    sesion = ControladorSesion(app, auth, cliente, minutos_bloqueo())
    sesion.iniciar()
    return app.exec()


if __name__ == "__main__":
    sys.exit(main())
