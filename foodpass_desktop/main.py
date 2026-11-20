import ctypes
import sys
from pathlib import Path

from PySide6.QtGui import QIcon
from PySide6.QtWidgets import QApplication

from foodpass_desktop.ui.ventana_principal import VentanaPrincipal


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
    window = VentanaPrincipal()
    window.show()
    return app.exec()


if __name__ == "__main__":
    sys.exit(main())
