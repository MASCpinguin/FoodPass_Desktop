import sys
from PySide6.QtWidgets import QApplication, QMainWindow
from foodpass_desktop.ui.ventanilla_view import VentanillaView


class MainWindow(QMainWindow):

  def __init__(self):
    super().__init__()
    self.setWindowTitle("FoodPass - Ventanilla de Priorización")
    self.resize(1000, 700)

    # Cargar la vista de la ventanilla como componente central
    self.ventanilla_widget = VentanillaView(self)
    self.setCentralWidget(self.ventanilla_widget)


def main():
  app = QApplication(sys.argv)
  window = MainWindow()
  window.show()
  sys.exit(app.exec())


if __name__ == "__main__":
  main()