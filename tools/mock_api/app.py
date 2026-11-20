"""Servidor simulado de la API de FoodPass para el escritorio.

Responde como lo indica el 05 Contrato de endpoints, con datos de prueba en memoria.
"""

import secrets
from datetime import datetime, timedelta, timezone
from functools import wraps

from flask import Flask, jsonify, request

from .datos import BENEFICIARIOS, OPERADORES

BOGOTA = timezone(timedelta(hours=-5))
PREFIJO = "/api/v1/escritorio"
MAX_INTENTOS = 3
DURACION_BLOQUEO = timedelta(minutes=5)
DURACION_TOKEN = timedelta(hours=1)

app = Flask(__name__)
app.json.ensure_ascii = False  # tildes legibles en las respuestas

# Estado en memoria
tokens = {}  # token -> {"operador": dict, "expira": datetime}
intentos = {}  # email -> {"fallidos": int, "bloqueado_hasta": datetime | None}
recibidos = {}  # uuid -> registro (sincronización)
canjes_hoy = {}  # usuario_id -> {"servicio": str, "hora": str, "modalidad": str, "motivo": str | None}



def ahora():
    return datetime.now(BOGOTA)


def fecha_iso(fecha):
    return fecha.isoformat(timespec="seconds")


def error(status, codigo, mensaje, datos=None):
    """Respuesta de error con el formato del contrato."""
    return jsonify({"codigo": codigo, "mensaje": mensaje, "datos": datos or {}}), status


def requiere_token(funcion):
    """Exige 'Authorization: Bearer <token>' vigente."""

    @wraps(funcion)
    def envoltura(*args, **kwargs):
        cabecera = request.headers.get("Authorization", "")
        token = cabecera.removeprefix("Bearer ").strip()
        sesion = tokens.get(token)
        if sesion is None or sesion["expira"] < ahora():
            return error(401, "TOKEN_INVALIDO", "La sesión no es válida o venció.")
        request.operador = sesion["operador"]
        request.token = token
        return funcion(*args, **kwargs)

    return envoltura


def crear_token(operador):
    token = secrets.token_hex(16)
    expira = ahora() + DURACION_TOKEN
    tokens[token] = {"operador": operador, "expira": expira}
    return token, expira


# ---------- EP-03 · Estado ----------
@app.get(f"{PREFIJO}/estado")
def estado():
    return jsonify({"ok": True, "hora_servidor": fecha_iso(ahora())})


# ---------- EP-01 · Inicio de sesión ----------
@app.post(f"{PREFIJO}/auth/login")
def login():
    datos = request.get_json(silent=True) or {}
    email = str(datos.get("email", "")).strip().lower()
    password = str(datos.get("password", ""))

    registro = intentos.setdefault(email, {"fallidos": 0, "bloqueado_hasta": None})
    bloqueado_hasta = registro["bloqueado_hasta"]
    if bloqueado_hasta and bloqueado_hasta > ahora():
        restantes = int((bloqueado_hasta - ahora()).total_seconds())
        return error(
            423,
            "CUENTA_BLOQUEADA",
            "Cuenta bloqueada temporalmente.",
            {"segundos_restantes": restantes},
        )

    operador = next(
        (o for o in OPERADORES if o["email"] == email and o["password"] == password),
        None,
    )
    if operador is None:
        registro["fallidos"] += 1
        if registro["fallidos"] >= MAX_INTENTOS:
            registro["fallidos"] = 0
            registro["bloqueado_hasta"] = ahora() + DURACION_BLOQUEO
            return error(
                423,
                "CUENTA_BLOQUEADA",
                "Cuenta bloqueada temporalmente.",
                {"segundos_restantes": int(DURACION_BLOQUEO.total_seconds())},
            )
        return error(401, "CREDENCIALES_INVALIDAS", "Correo o contraseña incorrectos.")

    if operador["rol"] != "operador_restaurante":
        return error(
            403, "SIN_ROL_CAFETERIA", "Esta cuenta no tiene acceso a la cafetería."
        )

    intentos.pop(email, None)
    token, expira = crear_token(operador)
    return jsonify({
        "token": token,
        "expira": fecha_iso(expira),
        "operador": {
            "id": operador["id"],
            "nombre": operador["nombre"],
            "email": operador["email"],
        },
    })


# ---------- EP-31 · Renovar token ----------
@app.post(f"{PREFIJO}/auth/renovar")
@requiere_token
def renovar():
    tokens.pop(request.token, None)
    token, expira = crear_token(request.operador)
    return jsonify({"token": token, "expira": fecha_iso(expira)})


# ---------- EP-02 · Cerrar sesión ----------
@app.post(f"{PREFIJO}/auth/logout")
@requiere_token
def logout():
    tokens.pop(request.token, None)
    return "", 204


# ---------- EP-04 · Registrar canje (QR y Manual) ----------
@app.post(f"{PREFIJO}/canjes")
def registrar_canje():
    """Registra un canje por QR (usuario_id) o Manual (documento + motivo)."""
    datos = request.get_json(silent=True) or {}
    servicio = str(datos.get("servicio", "")).strip()
    modalidad = str(datos.get("modalidad", "qr")).strip().lower()
    motivo = datos.get("motivo")

    if servicio not in {"Desayuno", "Almuerzo", "Refrigerio"}:
        return error(422, "SERVICIO_INVALIDO", "Debe seleccionar un servicio válido.")

    if modalidad == "manual":
        documento = str(datos.get("documento", "")).strip()
        if not documento:
            return error(
                422, "DOCUMENTO_REQUERIDO", "Debe ingresar el número de documento."
            )
        if not motivo:
            return error(
                422,
                "MOTIVO_REQUERIDO",
                "Debe seleccionar un motivo para el canje manual.",
            )
        beneficiario = next(
            (b for b in BENEFICIARIOS if b["numero_documento"] == documento),
            None,
        )
    else:
        raw_id = str(datos.get("usuario_id", "")).strip()
        if not raw_id.isdigit():
            return error(
                422, "CODIGO_NO_RECONOCIDO", "El código leído no es un ID válido."
            )
        usuario_id = int(raw_id)
        beneficiario = next(
            (b for b in BENEFICIARIOS if b["usuario_id"] == usuario_id),
            None,
        )

    if beneficiario is None or not beneficiario.get("activo", False):
        return error(
            404,
            "NO_BENEFICIARIO",
            "El usuario no se encuentra activo en la base de beneficiarios.",
        )

    uid = beneficiario["usuario_id"]
    if uid in canjes_hoy:
        previo = canjes_hoy[uid]
        return error(
            409,
            "YA_RECIBIO_HOY",
            f"Ya recibió {previo['servicio']} hoy a las {previo['hora']}.",
            {
                "nombre": beneficiario["nombre_completo"],
                "documento": beneficiario["numero_documento"],
                "servicio": previo["servicio"],
                "hora": previo["hora"],
            },
        )

    hora_actual = ahora().strftime("%I:%M %p")
    canjes_hoy[uid] = {
        "servicio": servicio,
        "hora": hora_actual,
        "modalidad": modalidad,
        "motivo": motivo,
    }

    return (
        jsonify({
            "estado": "entregado",
            "canje": {
                "usuario_id": uid,
                "nombre": beneficiario["nombre_completo"],
                "documento": beneficiario["numero_documento"],
                "programa": beneficiario["programa"],
                "foto_url": beneficiario["foto_url"],
                "servicio": servicio,
                "hora": hora_actual,
                "modalidad": modalidad,
                "motivo": motivo,
            },
        }),
        201,
    )


# ---------- Errores generales con el formato del contrato ----------
@app.errorhandler(404)
def no_encontrado(_):
    return error(404, "NO_ENCONTRADO", "La ruta no existe en el servidor simulado.")


@app.errorhandler(405)
def metodo_no_permitido(_):
    return error(405, "METODO_NO_PERMITIDO", "Método no permitido para esta ruta.")

# ---------- Sincronización · Lote de registros diferidos ----------
# FORMATO SUPUESTO: confirmar contra el 05 Contrato de endpoints.
@app.post(f"{PREFIJO}/sincronizacion/lote")
@requiere_token
def sincronizacion_lote():
    datos = request.get_json(silent=True) or {}
    registros = datos.get("registros")
    if not isinstance(registros, list) or not registros or len(registros) > 50:
        return error(400, "LOTE_INVALIDO", "El lote debe traer entre 1 y 50 registros.")
    resultados = []
    for r in registros:
        uid = r.get("uuid") if isinstance(r, dict) else None
        if not uid or r.get("tipo") not in ("canje", "venta", "anulacion"):
            resultados.append({"uuid": uid, "estado": "error", "codigo": "REGISTRO_INVALIDO"})
        elif uid in recibidos:
            resultados.append({"uuid": uid, "estado": "duplicado"})
        else:
            recibidos[uid] = r
            resultados.append({"uuid": uid, "estado": "ok"})
    return jsonify({"resultados": resultados})