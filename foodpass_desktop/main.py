import sys
from PySide6.QtCore import Qt
from PySide6.QtWidgets import QApplication, QLabel, QMainWindow


def main():
    app = QApplication(sys.argv)
    ventana = QMainWindow()
    ventana.setWindowTitle("FoodPass — Escritorio")
    ventana.resize(1024, 700)

    etiqueta = QLabel("FoodPass funcionando")
    etiqueta.setAlignment(Qt.AlignCenter)
    ventana.setCentralWidget(etiqueta)

    ventana.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()