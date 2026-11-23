"""Cliente único de la API. Nadie más debe usar `requests` directamente."""

import os

import requests

from foodpass_desktop.api.errores import ApiError, SinConexionError

from foodpass_desktop.core.config import cargar_env

cargar_env()

URL_MOCK = "http://127.0.0.1:8000/api/v1/escritorio"
TIMEOUT_SEGUNDOS = 3
RUTAS_SIN_TOKEN = {"/auth/login", "/estado"}


def _leer_url_base():
    """API_URL manda. Si no está definida, se usa el servidor simulado."""
    return os.getenv("API_URL", "").strip() or URL_MOCK


def _leer_json(respuesta):
    try:
        return respuesta.json()
    except ValueError:
        return {}


class ClienteApi:
    def __init__(self, url_base=None):
        url_base = url_base or _leer_url_base()
        self._base = url_base.rstrip("/")
        self._sesion = requests.Session()
        self._token = None
        self._al_expirar = None

    # --- sesión ---------------------------------------------------------
    def establecer_token(self, token):
        self._token = token

    def limpiar_token(self):
        self._token = None

    def renovar(self):
        """Renueva el token y lo guarda solo. Devuelve la respuesta."""
        datos = self.post("/auth/renovar")
        self.establecer_token(datos["token"])
        return datos

    def al_expirar_sesion(self, callback):
        """Registra qué hacer ante un 401 (volver al inicio de sesión).

        Ojo: puede ejecutarse en un hilo secundario. Conéctalo a una
        señal de Qt: `cliente.al_expirar_sesion(ventana.sesion_expirada.emit)`.
        """
        self._al_expirar = callback

    # --- métodos públicos -----------------------------------------------
    def get(self, ruta, params=None):
        return self._pedir("GET", ruta, params=params)

    def post(self, ruta, json=None):
        return self._pedir("POST", ruta, json=json)

    def patch(self, ruta, json=None):
        return self._pedir("PATCH", ruta, json=json)

    def put(self, ruta, json=None):
        return self._pedir("PUT", ruta, json=json)

    # --- interno ----------------------------------------------------------
    def _pedir(self, metodo, ruta, params=None, json=None):
        headers = {}
        if ruta not in RUTAS_SIN_TOKEN and self._token:
            headers["Authorization"] = f"Bearer {self._token}"

        try:
            respuesta = self._sesion.request(
                metodo,
                self._base + ruta,
                params=params,
                json=json,
                headers=headers,
                timeout=TIMEOUT_SEGUNDOS,
            )
        except (requests.Timeout, requests.ConnectionError) as e:
            raise SinConexionError(str(e)) from e

        cuerpo = _leer_json(respuesta)
        if respuesta.status_code < 400:
            return cuerpo

        cuerpo = cuerpo if isinstance(cuerpo, dict) else {}
        error = ApiError(
            codigo=cuerpo.get("codigo") or f"HTTP_{respuesta.status_code}",
            mensaje=cuerpo.get("mensaje", ""),
            datos=cuerpo.get("datos"),
            status=respuesta.status_code,
        )
        # Un 401 en /auth/login son credenciales malas, no sesión vencida.
        if (
            respuesta.status_code == 401
            and ruta not in RUTAS_SIN_TOKEN
            and self._al_expirar
        ):
            self._al_expirar()
        raise error


cliente = ClienteApi()
