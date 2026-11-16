"""Pantalla de ejemplo: llama a /estado sin congelar la ventana.

1) Arranca el servidor simulado:  python -m tools.mock_api
2) Corre este ejemplo:            python -m tools.ejemplo_estado
"""

import sys

from PySide6.QtWidgets import QApplication, QLabel, QPushButton, QVBoxLayout, QWidget

from foodpass_desktop.api.cliente import cliente
from foodpass_desktop.api.errores import ApiError, SinConexionError
from foodpass_desktop.api.trabajador import ejecutar_en_segundo_plano


class EjemploEstado(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Ejemplo: cliente API")
        self.boton = QPushButton("Consultar /estado")
        self.etiqueta = QLabel("Sin consultar")
        layout = QVBoxLayout(self)
        layout.addWidget(self.boton)
        layout.addWidget(self.etiqueta)
        self.boton.clicked.connect(self.consultar)

    def consultar(self):
        self.boton.setEnabled(False)
        self.etiqueta.setText("Consultando...")
        ejecutar_en_segundo_plano(
            cliente.get,
            "/estado",
            al_exito=self.mostrar_estado,
            al_error=self.mostrar_error,
        )

    def mostrar_estado(self, datos):
        self.etiqueta.setText(f"Respuesta: {datos}")
        self.boton.setEnabled(True)

    def mostrar_error(self, error):
        if isinstance(error, SinConexionError):
            self.etiqueta.setText("Sin conexión con el servidor")
        elif isinstance(error, ApiError):
            self.etiqueta.setText(f"Error de la API: {error.codigo}")
        else:
            self.etiqueta.setText(f"Error inesperado: {error}")
        self.boton.setEnabled(True)


if __name__ == "__main__":
    app = QApplication(sys.argv)
    ventana = EjemploEstado()
    ventana.show()
    sys.exit(app.exec())