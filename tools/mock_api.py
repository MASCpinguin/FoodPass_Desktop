from http.server import HTTPServer, BaseHTTPRequestHandler
import json

class MockApiHandler(BaseHTTPRequestHandler):
    def do_POST(self):
        if self.path == "/api/v1/escritorio/auth/login":
            content_length = int(self.headers.get('Content-Length', 0))
            body = self.rfile.read(content_length)
            
            try:
                data = json.loads(body.decode('utf-8'))
            except:
                data = {}

            email = data.get("email", "")
            password = data.get("password", "")

            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.end_headers()

            # Credenciales correctas del mock
            if email == "operador@foodpass.co" and password == "123456":
                response_data = {
                    "token": "mock-token-jwt-abc123xyz",
                    "expira": "2026-12-31T23:59:59",
                    "operador": {"nombre": "Operador Cafetería", "email": email}
                }
            elif email == "bloqueado@foodpass.co":
                self.send_response(423)
                response_data = {
                    "codigo": "CUENTA_BLOQUEADA",
                    "mensaje": "Cuenta bloqueada temporalmente.",
                    "datos": {"segundos_restantes": 30}
                }
            elif email == "sinrol@foodpass.co":
                self.send_response(403)
                response_data = {
                    "codigo": "SIN_ROL_CAFETERIA",
                    "mensaje": "Esta cuenta no tiene acceso a la cafetería.",
                    "datos": {}
                }
            else:
                self.send_response(401)
                response_data = {
                    "codigo": "CREDENCIALES_INVALIDAS",
                    "mensaje": "Correo o contraseña incorrectos",
                    "datos": {}
                }

            # Reescribimos la respuesta con el código HTTP adecuado
            self.wfile.write(json.dumps(response_data).encode('utf-8'))
        else:
            self.send_response(404)
            self.end_headers()

def run(server_class=HTTPServer, handler_class=MockApiHandler, port=8000):
    server_address = ('localhost', port)
    httpd = server_class(server_address, handler_class)
    print(f"Servidor simulado (Mock API) corriendo en http://localhost:{port}...")
    httpd.serve_forever()

if __name__ == "__main__":
    run()