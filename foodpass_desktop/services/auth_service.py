"""Inicio de sesión, renovación del token y PIN de desbloqueo (T05 · RF-ES25 · CU-01).

Esta capa no conoce Qt: las pantallas la llaman en segundo plano y muestran lo
que devuelve. Endpoints: EP-01 /auth/login, EP-31 /auth/renovar y
EP-02 /auth/logout (05 Contrato de endpoints).
"""

import hashlib
import hmac
import re
import secrets
import socket
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone

from foodpass_desktop.api.errores import ApiError, SinConexionError

BOGOTA = timezone(timedelta(hours=-5))
MARGEN_RENOVACION = timedelta(minutes=5)  # renovar 5 min antes de que venza
MAX_INTENTOS_PIN = 5
LARGO_PIN = (4, 6)
ITERACIONES_PIN = 200_000

CLAVE_TOKEN = "token"
CLAVE_EXPIRA = "token_expira"
CLAVE_PIN = "pin"

_PATRON_EMAIL = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")

MENSAJES = {
    "CORREO_INVALIDO": "Escribe un correo válido.",
    "PASSWORD_VACIA": "Escribe tu contraseña.",
    "CREDENCIALES_INVALIDAS": "Correo o contraseña incorrectos.",
    "CUENTA_BLOQUEADA": "Cuenta bloqueada. Intenta de nuevo en {tiempo}.",
    "SIN_ROL_CAFETERIA": "Esta cuenta no tiene acceso a la cafetería.",
    "SIN_CONEXION": "No hay conexión con el servidor.",
    "ERROR_DESCONOCIDO": "No se pudo iniciar sesión. Intenta de nuevo.",
    "PIN_FORMATO": "El PIN debe tener de 4 a 6 dígitos.",
    "PIN_NO_COINCIDE": "Los PIN no coinciden.",
    "PIN_INCORRECTO": "PIN incorrecto. Te quedan {restantes} intentos.",
    "PIN_AGOTADO": "Demasiados intentos. Ingresa con tu correo y contraseña.",
}


# --- validaciones y formato (sin red) --------------------------------------
def validar_credenciales(email, password):
    """Devuelve el código del primer error o None si se puede enviar."""
    if not _PATRON_EMAIL.match((email or "").strip()):
        return "CORREO_INVALIDO"
    if not password:
        return "PASSWORD_VACIA"
    return None


def validar_formato_pin(pin):
    minimo, maximo = LARGO_PIN
    pin = pin or ""
    return pin.isdigit() and minimo <= len(pin) <= maximo


def formatear_tiempo(segundos):
    """300 -> '5:00'; 65 -> '1:05'."""
    segundos = max(0, int(segundos))
    return f"{segundos // 60}:{segundos % 60:02d}"


def mensaje_bloqueo(segundos):
    return MENSAJES["CUENTA_BLOQUEADA"].format(tiempo=formatear_tiempo(segundos))


class ErrorInicioSesion(Exception):
    """Error listo para mostrar en la pantalla de inicio de sesión.

    La pantalla decide con `codigo`; `segundos_restantes` solo viene con
    CUENTA_BLOQUEADA, para la cuenta regresiva.
    """

    def __init__(self, codigo, segundos_restantes=0):
        self.codigo = codigo
        self.segundos_restantes = segundos_restantes
        if codigo == "CUENTA_BLOQUEADA":
            mensaje = mensaje_bloqueo(segundos_restantes)
        else:
            mensaje = MENSAJES.get(codigo, MENSAJES["ERROR_DESCONOCIDO"])
        self.mensaje = mensaje
        super().__init__(mensaje)


def interpretar_error(error):
    """Traduce lo que lanzó el cliente de la API a un ErrorInicioSesion."""
    if isinstance(error, ErrorInicioSesion):
        return error
    if isinstance(error, SinConexionError):
        return ErrorInicioSesion("SIN_CONEXION")
    if isinstance(error, ApiError):
        if error.codigo == "CUENTA_BLOQUEADA":
            segundos = error.datos.get("segundos_restantes", 0)
            try:
                segundos = int(segundos)
            except (TypeError, ValueError):
                segundos = 0
            return ErrorInicioSesion("CUENTA_BLOQUEADA", segundos)
        if error.codigo in ("CREDENCIALES_INVALIDAS", "SIN_ROL_CAFETERIA"):
            return ErrorInicioSesion(error.codigo)
    return ErrorInicioSesion("ERROR_DESCONOCIDO")


@dataclass
class ResultadoPin:
    correcto: bool
    intentos_restantes: int
    mensaje: str = ""

    @property
    def agotado(self):
        return not self.correcto and self.intentos_restantes == 0


def _ahora():
    return datetime.now(BOGOTA)


def _leer_fecha(texto):
    try:
        fecha = datetime.fromisoformat(texto)
    except (TypeError, ValueError):
        return None
    return fecha if fecha.tzinfo else fecha.replace(tzinfo=BOGOTA)


def _hash_pin(pin, sal):
    return hashlib.pbkdf2_hmac(
        "sha256", pin.encode(), bytes.fromhex(sal), ITERACIONES_PIN
    ).hex()


# --- servicio ----------------------------------------------------------------
class AuthService:
    """Sesión del operador: login, token, renovación, cierre y PIN."""

    def __init__(self, cliente, almacen, reloj=_ahora, dispositivo=None):
        self._cliente = cliente
        self._almacen = almacen
        self._reloj = reloj
        self._dispositivo = dispositivo or socket.gethostname()
        self.operador = None
        self.expira = None
        self._pin_fallidos = 0

    # --- inicio y cierre de sesión ------------------------------------------
    def iniciar_sesion(self, email, password):
        """Llama a EP-01. Devuelve el operador o lanza ErrorInicioSesion.

        Bloquea mientras espera: llámalo con `ejecutar_en_segundo_plano`.
        """
        email = (email or "").strip().lower()
        codigo = validar_credenciales(email, password)
        if codigo:
            raise ErrorInicioSesion(codigo)
        try:
            datos = self._cliente.post(
                "/auth/login",
                json={
                    "email": email,
                    "password": password,
                    "dispositivo": self._dispositivo,
                },
            )
        except (ApiError, SinConexionError) as e:
            raise interpretar_error(e) from e

        if not datos.get("token"):
            raise ErrorInicioSesion("ERROR_DESCONOCIDO")
        self._guardar_token(datos["token"], datos.get("expira"))
        self.operador = datos.get("operador") or {}
        self._pin_fallidos = 0
        return self.operador

    def cerrar_sesion(self):
        """Llama a EP-02 y borra el token aunque la API no responda."""
        try:
            if self._cliente_tiene_token():
                self._cliente.post("/auth/logout")
        except (ApiError, SinConexionError):
            pass  # el token se borra igual; en el servidor vence solo en 1 h
        finally:
            self.borrar_sesion()

    def borrar_sesion(self):
        """Olvida el token en memoria y en el almacén de credenciales."""
        self._cliente.limpiar_token()
        self._almacen.borrar(CLAVE_TOKEN)
        self._almacen.borrar(CLAVE_EXPIRA)
        self.operador = None
        self.expira = None
        self._pin_fallidos = 0

    @property
    def hay_sesion(self):
        return self.expira is not None and self.expira > self._reloj()

    # --- renovación (EP-31) ---------------------------------------------------
    def segundos_para_renovar(self, margen=MARGEN_RENOVACION):
        """Segundos que faltan para renovar (0 si ya toca)."""
        if self.expira is None:
            return 0
        faltan = (self.expira - margen - self._reloj()).total_seconds()
        return max(0, int(faltan))

    def necesita_renovar(self, margen=MARGEN_RENOVACION):
        return self.expira is not None and self.segundos_para_renovar(margen) == 0

    def renovar(self):
        """Pide un token nuevo sin contraseña. Lanza ApiError o SinConexionError."""
        datos = self._cliente.renovar()
        self._guardar_token(datos["token"], datos.get("expira"))
        return self.expira

    # --- PIN de desbloqueo ------------------------------------------------------
    def hay_pin(self):
        return bool(self._almacen.leer(CLAVE_PIN))

    def crear_pin(self, pin, confirmacion=None):
        """Guarda el PIN (solo su hash) en el almacén. Devuelve un error o None."""
        if not validar_formato_pin(pin):
            return MENSAJES["PIN_FORMATO"]
        if confirmacion is not None and pin != confirmacion:
            return MENSAJES["PIN_NO_COINCIDE"]
        sal = secrets.token_hex(16)
        self._almacen.guardar(CLAVE_PIN, f"{sal}${_hash_pin(pin, sal)}")
        self._pin_fallidos = 0
        return None

    def verificar_pin(self, pin):
        """Compara el PIN. Al quinto error borra el token (pide correo y contraseña)."""
        guardado = self._almacen.leer(CLAVE_PIN) or ""
        sal, _, esperado = guardado.partition("$")
        correcto = (
            bool(esperado)
            and validar_formato_pin(pin)
            and hmac.compare_digest(_hash_pin(pin, sal), esperado)
        )
        if correcto:
            self._pin_fallidos = 0
            return ResultadoPin(True, MAX_INTENTOS_PIN)

        self._pin_fallidos += 1
        restantes = max(0, MAX_INTENTOS_PIN - self._pin_fallidos)
        if restantes == 0:
            self.borrar_sesion()
            return ResultadoPin(False, 0, MENSAJES["PIN_AGOTADO"])
        return ResultadoPin(
            False, restantes, MENSAJES["PIN_INCORRECTO"].format(restantes=restantes)
        )

    # --- interno ------------------------------------------------------------------
    def _guardar_token(self, token, expira_texto):
        expira = _leer_fecha(expira_texto) or self._reloj() + timedelta(hours=1)
        self._cliente.establecer_token(token)
        self._almacen.guardar(CLAVE_TOKEN, token)
        self._almacen.guardar(CLAVE_EXPIRA, expira.isoformat())
        self.expira = expira

    def _cliente_tiene_token(self):
        return bool(self._almacen.leer(CLAVE_TOKEN))
