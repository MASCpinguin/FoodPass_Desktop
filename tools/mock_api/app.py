"""Servidor simulado de la API de FoodPass para el escritorio.

Responde como lo indica el 05 Contrato de endpoints, con datos de prueba en memoria.
"""

import secrets
from datetime import datetime, timedelta, timezone
from functools import wraps

from flask import Flask, jsonify, request

from .datos import OPERADORES

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
        return error(423, "CUENTA_BLOQUEADA", "Cuenta bloqueada temporalmente.",
                     {"segundos_restantes": restantes})

    operador = next(
        (o for o in OPERADORES if o["email"] == email and o["password"] == password), None
    )
    if operador is None:
        registro["fallidos"] += 1
        if registro["fallidos"] >= MAX_INTENTOS:
            registro["fallidos"] = 0
            registro["bloqueado_hasta"] = ahora() + DURACION_BLOQUEO
            return error(423, "CUENTA_BLOQUEADA", "Cuenta bloqueada temporalmente.",
                         {"segundos_restantes": int(DURACION_BLOQUEO.total_seconds())})
        return error(401, "CREDENCIALES_INVALIDAS", "Correo o contraseña incorrectos.")

    if operador["rol"] != "operador_restaurante":
        return error(403, "SIN_ROL_CAFETERIA", "Esta cuenta no tiene acceso a la cafetería.")

    intentos.pop(email, None)
    token, expira = crear_token(operador)
    return jsonify({
        "token": token,
        "expira": fecha_iso(expira),
        "operador": {"id": operador["id"], "nombre": operador["nombre"], "email": operador["email"]},
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


# ---------- Errores generales con el formato del contrato ----------
@app.errorhandler(404)
def no_encontrado(_):
    return error(404, "NO_ENCONTRADO", "La ruta no existe en el servidor simulado.")


@app.errorhandler(405)
def metodo_no_permitido(_):
    return error(405, "METODO_NO_PERMITIDO", "Método no permitido para esta ruta.")