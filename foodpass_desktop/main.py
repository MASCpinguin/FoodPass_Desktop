import sys
from pathlib import Path

from PySide6.QtWidgets import QApplication

from foodpass_desktop.api.cliente import cliente
from foodpass_desktop.services.sincronizacion import Sincronizador
from foodpass_desktop.services.temporizador_sync import TemporizadorSync
from foodpass_desktop.storage.cola import ColaSync
from foodpass_desktop.ui.ventana_principal import VentanaPrincipal


def main():
    app = QApplication(sys.argv)
    tema = Path(__file__).resolve().parent / "resources" / "tema.qss"
    app.setStyleSheet(tema.read_text(encoding="utf-8"))
    window = VentanaPrincipal()
    window.show()

    # Registro diferido (T06): cola local + reintento cada 30 s.
    cola = ColaSync(Path.home() / ".foodpass_desktop" / "cola_sync.db")
    sincronizador = Sincronizador(cola, cliente)
    temporizador = TemporizadorSync(sincronizador)
    temporizador.iniciar()
    window.sincronizador = sincronizador  # las pantallas llaman .registrar(...)

    return app.exec()


if __name__ == "__main__":
    
    sys.exit(main())