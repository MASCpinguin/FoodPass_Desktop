import json
import urllib.request
import urllib.error
from PySide6.QtCore import QThread, Signal

class LoginWorker(QThread):
    login_success = Signal(dict)
    login_error = Signal(int, str, dict)

    def __init__(self, email, password):
        super().__init__()
        self.email = email
        self.password = password

    def run(self):
        # Ajustado a la ruta base de la API descrita en el contrato
        url = "http://localhost:8000/api/v1/escritorio/auth/login"
        
        # ¡IMPORTANTE! Añadimos "dispositivo" tal como lo pide el contrato
        payload = {
            "email": self.email,
            "password": self.password,
            "dispositivo": "desktop"
        }
        
        data_bytes = json.dumps(payload).encode('utf-8')
        req = urllib.request.Request(
            url, 
            data=data_bytes, 
            headers={'Content-Type': 'application/json'}, 
            method='POST'
        )

        try:
            with urllib.request.urlopen(req, timeout=5) as response:
                response_body = response.read().decode('utf-8')
                data = json.loads(response_body)
                self.login_success.emit(data)
                
        except urllib.error.HTTPError as e:
            try:
                error_body = e.read().decode('utf-8')
                error_data = json.loads(error_body)
            except:
                error_data = {}
            
            mensaje = error_data.get("mensaje", "Error en el servidor")
            self.login_error.emit(e.code, mensaje, error_data)
            
        except Exception as ex:
            self.login_error.emit(0, "No hay conexión con el servidor", {})