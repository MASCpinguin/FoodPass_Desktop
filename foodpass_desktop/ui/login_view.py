import requests
from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QDialog,
    QVBoxLayout,
    QLabel,
    QLineEdit,
    QPushButton,
)


class LoginView(QDialog):

  def __init__(self, on_login_success_callback):
    super().__init__()
    self.on_login_success_callback = on_login_success_callback

    self.setWindowTitle("FoodPass - Iniciar Sesión")
    self.resize(400, 300)
    self.init_ui()

  def init_ui(self):
    layout = QVBoxLayout()

    title_label = QLabel("Bienvenido a FoodPass")
    title_label.setAlignment(Qt.AlignCenter)
    title_label.setStyleSheet("font-size: 18px; font-weight: bold; margin-bottom: 15px;")
    layout.addWidget(title_label)

    layout.addWidget(QLabel("Correo electrónico:"))
    self.input_email = QLineEdit()
    self.input_email.setPlaceholderText("ejemplo@foodpass.co")
    layout.addWidget(self.input_email)

    layout.addWidget(QLabel("Contraseña:"))
    self.input_password = QLineEdit()
    self.input_password.setEchoMode(QLineEdit.Password)
    self.input_password.setPlaceholderText("******")
    layout.addWidget(self.input_password)

    self.btn_login = QPushButton("Ingresar")
    self.btn_login.setStyleSheet("background-color: #2b579a; color: white; font-weight: bold; padding: 8px;")
    self.btn_login.clicked.connect(self.handle_login)
    layout.addWidget(self.btn_login)

    self.lbl_status = QLabel("")
    self.lbl_status.setAlignment(Qt.AlignCenter)
    self.lbl_status.setStyleSheet("color: red;")
    layout.addWidget(self.lbl_status)

    self.setLayout(layout)

  def handle_login(self):
    email = self.input_email.text().strip()
    password = self.input_password.text().strip()

    if not email or not password:
        self.lbl_status.setText("Por favor complete todos los campos.")
        return

    url = "http://localhost:8000/api/v1/escritorio/auth/login"
    payload = {"email": email, "password": password, "dispositivo": "desktop"}

    try:
        response = requests.post(url, json=payload, timeout=5)
        
        print(f"DEBUG - Status Code: {response.status_code}")
        print(f"DEBUG - Response JSON: {response.text}")

        data = response.json() if response.text else {}

        # Extraemos el código de respuesta del JSON de tu backend
        codigo_respuesta = data.get("codigo", "")

        # El acceso solo es exitoso si el status es 200 y el código interno NO es de error
        if response.status_code == 200 and codigo_respuesta != "CRED_INVALIDAS" and codigo_respuesta != "CREDENCIALES_INVALIDAS":
            self.accept()
            self.on_login_success_callback()
        else:
            # Si el servidor devolvió un mensaje de error en el JSON, lo mostramos en la etiqueta
            mensaje_error = data.get("mensaje", "Credenciales incorrectas.")
            self.lbl_status.setText(mensaje_error)

    except requests.exceptions.ConnectionError:
        self.lbl_status.setText("Error: No se pudo conectar con el servidor.")
    except Exception as e:
        print(f"DEBUG - Error inesperado: {e}")
        self.lbl_status.setText("Ocurrió un error inesperado.")