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

# ---------- Movimientos del día para la caja (EP-24 y EP-25) ----------
# Se generan con la fecha de hoy al arrancar el servidor. Las ventas anuladas
# no deben sumar en los totales del cierre (RF-ES29).


def movimientos_de_hoy(hoy):
    """Ventas, canjes y pedidos web de prueba con la fecha `hoy` (date)."""
    dia = hoy.isoformat()
    ventas = [
        {"id": 1, "metodo_pago": "nequi", "total": 12000, "anulada": False},
        {"id": 2, "metodo_pago": "nequi", "total": 8500, "anulada": False},
        {"id": 3, "metodo_pago": "transferencia", "total": 15000, "anulada": False},
        {"id": 4, "metodo_pago": "nequi", "total": 6000, "anulada": True},
        {"id": 5, "metodo_pago": "transferencia", "total": 9500, "anulada": False},
        {"id": 6, "metodo_pago": "nequi", "total": 4500, "anulada": False},
    ]
    for venta in ventas:
        venta["fecha"] = dia
    canjes = (
        [{"servicio": "desayuno", "anulado": False}] * 12
        + [{"servicio": "almuerzo", "anulado": False}] * 18
        + [{"servicio": "almuerzo", "anulado": True}]
        + [{"servicio": "refrigerio", "anulado": False}] * 7
    )
    canjes = [dict(c, fecha=dia) for c in canjes]
    pedidos_web = [
        {"id": 1, "estado": "entregado", "fecha": dia},
        {"id": 2, "estado": "entregado", "fecha": dia},
        {"id": 3, "estado": "pendiente", "fecha": dia},
        {"id": 4, "estado": "cancelado", "fecha": dia},
    ]
    return ventas, canjes, pedidos_web
