import sys
from PySide6.QtWidgets import QApplication, QDialog, QMainWindow
from foodpass_desktop.ui.ventanilla_view import VentanillaView
from foodpass_desktop.ui.login_view import LoginView  # <--- Importamos la vista de login


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

  # Función que se ejecuta solo si el login es exitoso
  def abrir_ventana_principal():
    global window
    window = MainWindow()
    window.show()

  # Instanciamos y mostramos el Login primero
  login = LoginView(on_login_success_callback=abrir_ventana_principal)
  
  # Si el usuario cierra el login sin autenticarse, la app se cierra correctamente
  if login.exec() != QDialog.Accepted:
    sys.exit(0)

  sys.exit(app.exec())


if __name__ == "__main__":
  main()