"""Abre la app con la sesión iniciada y el cierre de caja a la vista.

Uso (con el servidor simulado corriendo en otra terminal):
    python -m tools.demo_cierre

Mientras no esté el inicio de sesión (T05), este demo hace el login con el
usuario de prueba del servidor simulado y luego abre la ventana principal.
"""

import sys
from pathlib import Path

from PySide6.QtWidgets import QApplication

from foodpass_desktop.api.cliente import cliente
from foodpass_desktop.api.errores import ApiError, SinConexionError
from foodpass_desktop.ui.ventana_principal import VentanaPrincipal

TEMA = Path(__file__).resolve().parents[1] / "foodpass_desktop" / "resources" / "tema.qss"


def main():
    try:
        datos = cliente.post("/auth/login", json={
            "email": "operador@foodpass.co", "password": "123456", "dispositivo": "PC-DEMO",
        })
    except SinConexionError:
        sys.exit("No se pudo conectar con el servidor. ¿Arrancaste: python -m tools.mock_api?")
    except ApiError as error:
        sys.exit(f"El inicio de sesión falló: {error.codigo}")
    cliente.establecer_token(datos["token"])

    app = QApplication(sys.argv)
    app.setStyleSheet(TEMA.read_text(encoding="utf-8"))
    ventana = VentanaPrincipal()
    ventana.mostrar_pantalla("reportes")
    ventana.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
