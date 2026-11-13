"""Arranca el servidor simulado: python -m tools.mock_api"""

from .app import app

print("Servidor simulado de FoodPass en http://localhost:8000/api/v1/escritorio")
print("Usuario de prueba: operador@foodpass.co / 123456")
app.run(host="127.0.0.1", port=8000, debug=True)