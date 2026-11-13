"""Datos de prueba del servidor simulado.

Viven en memoria: se reinician cada vez que se apaga el servidor.
"""

OPERADORES = [
    {
        "id": 7,
        "nombre": "Operador de prueba",
        "email": "operador@foodpass.co",
        "password": "123456",
        "rol": "operador_restaurante",
    },
    {
        "id": 8,
        "nombre": "Usuario sin rol de cafetería",
        "email": "sinrol@foodpass.co",
        "password": "123456",
        "rol": "aprendiz",
    },
]

PROGRAMAS = ["ADSO", "Cocina", "Electricidad", "Mecatrónica"]

# 20 beneficiarios: cada quinto está inactivo y cada tercero no tiene foto.
BENEFICIARIOS = [
    {
        "id": i,
        "usuario_id": 1000 + i,
        "tipo_documento": "CC",
        "numero_documento": f"10000000{i:02d}",
        "nombre_completo": f"Aprendiz de prueba {i}",
        "programa": PROGRAMAS[i % len(PROGRAMAS)],
        "ficha": "3173467",
        "activo": i % 5 != 0,
        "foto_url": None if i % 3 == 0 else f"/fotos/{1000 + i}.jpg",
    }
    for i in range(1, 21)
]