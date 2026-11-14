"""Abre la pantalla de cierre de caja contra el servidor simulado.

Uso (con el servidor simulado corriendo en otra terminal):
    python -m tools.demo_cierre

Es un cliente mínimo solo para probar T30 mientras se fusiona el cliente de
API de T03. Cuando T03 esté en develop, la pantalla se conecta con ese cliente.
"""

import os
import sys

import requests
from dotenv import load_dotenv
from PySide6.QtWidgets import QApplication, QMainWindow

from foodpass_desktop.services.caja_service import CajaService
from foodpass_desktop.ui.cierre_caja_view import CierreCajaView


class ErrorApiDemo(Exception):
    def __init__(self, status, codigo, mensaje):
        super().__init__(mensaje)
        self.status = status
        self.codigo = codigo
        self.mensaje = mensaje


class ClienteDemo:
    """Cliente HTTP mínimo con la interfaz que espera CajaService."""

    def __init__(self, base_url, timeout=3):
        self.base_url = base_url.rstrip("/")
        self.timeout = timeout
        self.token = None

    def login(self, email, password):
        datos = self.post("/auth/login", json={
            "email": email, "password": password, "dispositivo": "PC-DEMO",
        })
        self.token = datos["token"]

    def get(self, ruta, params=None):
        return self._pedir("GET", ruta, params=params)

    def post(self, ruta, json=None):
        return self._pedir("POST", ruta, json=json)

    def _pedir(self, metodo, ruta, **kwargs):
        cabeceras = {"Authorization": f"Bearer {self.token}"} if self.token else {}
        r = requests.request(metodo, self.base_url + ruta, headers=cabeceras,
                             timeout=self.timeout, **kwargs)
        if r.status_code >= 400:
            cuerpo = r.json() if r.content else {}
            raise ErrorApiDemo(r.status_code, cuerpo.get("codigo"), cuerpo.get("mensaje"))
        return r.json() if r.content else {}


def main():
    load_dotenv(override=True)  # el .env manda sobre la terminal
    url = os.getenv("API_URL", "http://127.0.0.1:8000/api/v1/escritorio")
    cliente = ClienteDemo(url)
    try:
        cliente.login("operador@foodpass.co", "123456")
    except requests.RequestException:
        sys.exit(f"No se pudo conectar con {url}. ¿Arrancaste: python -m tools.mock_api?")

    app = QApplication(sys.argv)
    ventana = QMainWindow()
    ventana.setWindowTitle("FoodPass - Cierre de caja (demo T30)")
    ventana.resize(1100, 720)
    ventana.setCentralWidget(CierreCajaView(CajaService(cliente)))
    ventana.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
