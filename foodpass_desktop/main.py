import ctypes
import sys
from pathlib import Path

from foodpass_desktop.core.config import cargar_env

cargar_env()  # antes de crear el cliente de la API: lee API_URL y DB_* del .env

from PySide6.QtGui import QFontDatabase, QIcon  # noqa: E402
from PySide6.QtWidgets import QApplication  # noqa: E402

from foodpass_desktop.api.cliente import cliente  # noqa: E402
from foodpass_desktop.core.config import minutos_bloqueo  # noqa: E402
from foodpass_desktop.core.sesion import ControladorSesion  # noqa: E402
from foodpass_desktop.services.auth_service import AuthService  # noqa: E402
from foodpass_desktop.storage.credenciales import crear_almacen  # noqa: E402

RECURSOS = Path(__file__).resolve().parent / "resources"
ICONO = RECURSOS / "icons" / "foodpass.ico"


def cargar_fuentes():
    """Poppins (Guía de Estilos); si no carga, el QSS cae a Segoe UI."""
    for archivo in sorted((RECURSOS / "fonts").glob("*.ttf")):
        QFontDatabase.addApplicationFont(str(archivo))


def main():
    if sys.platform == "win32":
        ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID(
            "SENA.FoodPass.Escritorio"
        )
    app = QApplication(sys.argv)
    app.setWindowIcon(QIcon(str(ICONO)))
    cargar_fuentes()
    app.setStyleSheet((RECURSOS / "tema.qss").read_text(encoding="utf-8"))

    auth = AuthService(cliente, crear_almacen())
    sesion = ControladorSesion(app, auth, cliente, minutos_bloqueo())
    sesion.iniciar()
    return app.exec()


if __name__ == "__main__":
    sys.exit(main())
