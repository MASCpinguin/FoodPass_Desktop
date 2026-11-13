import sys
from pathlib import Path

from PySide6.QtWidgets import QApplication

from foodpass_desktop.ui.ventana_principal import VentanaPrincipal


def main():
    app = QApplication(sys.argv)
    tema = Path(__file__).resolve().parent / "resources" / "tema.qss"
    app.setStyleSheet(tema.read_text(encoding="utf-8"))
    window = VentanaPrincipal()
    window.show()
    return app.exec()


if __name__ == "__main__":
    sys.exit(main())
