"""Capa de servicios para el módulo de Priorización (Canje por QR y Manual).

Desde C2.2-04 el canje se registra directo en MySQL (storage/canjes_bd.py)
cuando el .env trae DB_HOST. Sin DB_HOST se usa la API o el servidor simulado,
como antes (así siguen funcionando las pruebas y el mock).
"""

import re
from dataclasses import dataclass
from typing import Any

from foodpass_desktop.api.cliente import cliente as cliente_por_defecto
from foodpass_desktop.api.errores import ApiError, SinConexionError
from foodpass_desktop.storage import bd

# Códigos que generan hoy la web y el móvil (C2.2-02). No se lee su contenido:
# solo se reconoce el tipo y se busca completo en la base de datos.
PATRON_CODIGO_MOVIL = re.compile(r"^FP-[0-9A-Fa-f]{6}$")  # qr_tokens.code
PATRON_QR_WEB = re.compile(r"^FP-[A-Za-z0-9-]{10,180}$")  # canjes.codigo_qr
PATRON_TOKEN_MOVIL = re.compile(r"^[0-9A-Fa-f]{64}$")  # qr_tokens.token


def interpretar_codigo(texto: str):
    """Devuelve (tipo, código) o None si no es un código de FoodPass."""
    limpio = (texto or "").strip()
    if PATRON_CODIGO_MOVIL.match(limpio):
        return "movil", limpio.upper()
    if PATRON_QR_WEB.match(limpio):
        return "web", limpio
    if PATRON_TOKEN_MOVIL.match(limpio):
        return "token", limpio.lower()
    return None


SERVICIOS_VALIDOS = ("Desayuno", "Almuerzo", "Refrigerio")

MOTIVOS_CANJE_MANUAL = (
    "Carné o celular olvidado",
    "Sin batería en el celular",
    "QR ilegible o pantalla dañada",
    "Falla en el lector QR",
    "Aprendiz nuevo sin acceso a la app",
)


@dataclass
class ResultadoCanje:
    """Estructura normalizada que consume la interfaz gráfica."""

    tipo: str  # 'entregado' | 'ya_recibio' | 'no_beneficiario' | 'no_reconocido' | 'error_conexion'
    datos: dict[str, Any]


class CanjeService:
    """Servicio aislado para validar y registrar entregas de alimentación."""

    def __init__(self, api_client=None, repositorio=None):
        self._api = api_client or cliente_por_defecto
        if repositorio is None and api_client is None and bd.configurada():
            from foodpass_desktop.storage.canjes_bd import CanjesBD

            repositorio = CanjesBD()
        self._repo = repositorio

    @staticmethod
    def validar_contenido_qr(contenido: str) -> tuple[bool, str]:
        """Valida que el QR tenga únicamente entre 1 y 10 dígitos numéricos."""
        limpio = (contenido or "").strip()
        if not limpio.isdigit() or not (1 <= len(limpio) <= 10):
            return False, ""
        return True, limpio

    @staticmethod
    def validar_documento(documento: str) -> tuple[bool, str]:
        """Valida que el documento ingresado manualmente sean dígitos válidos (5 a 15)."""
        limpio = (documento or "").strip()
        if not limpio.isdigit() or not (5 <= len(limpio) <= 15):
            return False, ""
        return True, limpio

    def registrar_canje_qr(self, servicio: str, contenido_qr: str) -> ResultadoCanje:
        """Valida localmente el QR y solicita el registro de canje a la API."""
        if servicio not in SERVICIOS_VALIDOS:
            raise ValueError("Debe seleccionar un servicio antes de escanear.")

        if self._repo is not None:
            codigo = interpretar_codigo(contenido_qr)
            if codigo is None:
                return ResultadoCanje(tipo="no_reconocido", datos={})
            tipo, datos = self._repo.canjear_codigo(servicio, *codigo)
            return ResultadoCanje(tipo=tipo, datos=datos)

        es_valido, usuario_id = self.validar_contenido_qr(contenido_qr)
        if not es_valido:
            return ResultadoCanje(tipo="no_reconocido", datos={})

        payload = {
            "usuario_id": int(usuario_id),
            "servicio": servicio,
            "modalidad": "qr",
        }
        return self._enviar_canje(payload)

    def registrar_canje_manual(
        self, servicio: str, documento: str, motivo: str
    ) -> ResultadoCanje:
        """Valida el documento y motivo, y solicita el canje manual a la API."""
        if servicio not in SERVICIOS_VALIDOS:
            raise ValueError("Debe seleccionar un servicio antes de registrar.")

        es_valido, doc_limpio = self.validar_documento(documento)
        if not es_valido:
            return ResultadoCanje(tipo="no_reconocido", datos={})

        motivo_limpio = (motivo or "").strip()
        if not motivo_limpio:
            raise ValueError("Debe seleccionar un motivo para el canje manual.")

        if self._repo is not None:
            tipo, datos = self._repo.canjear_documento(
                servicio, doc_limpio, motivo_limpio
            )
            return ResultadoCanje(tipo=tipo, datos=datos)

        payload = {
            "documento": doc_limpio,
            "servicio": servicio,
            "modalidad": "manual",
            "motivo": motivo_limpio,
        }
        return self._enviar_canje(payload)

    def _enviar_canje(self, payload: dict[str, Any]) -> ResultadoCanje:
        """Ejecuta la llamada HTTP contra la API (mock o real) y traduce la respuesta."""
        try:
            respuesta = self._api.post("/canjes", json=payload)
            canje = respuesta.get("canje", respuesta)
            return ResultadoCanje(
                tipo="entregado",
                datos={
                    "nombre": canje.get("nombre", "Beneficiario"),
                    "documento": canje.get("documento", ""),
                    "programa": canje.get("programa", ""),
                    "foto_url": canje.get("foto_url"),
                    "servicio": canje.get("servicio", payload["servicio"]),
                    "hora": canje.get("hora", ""),
                    "modalidad": canje.get("modalidad", payload["modalidad"]),
                },
            )
        except ApiError as err:
            if err.status == 409 or err.codigo == "YA_RECIBIO_HOY":
                info = err.datos or {}
                return ResultadoCanje(
                    tipo="ya_recibio",
                    datos={
                        "nombre": info.get("nombre", "Beneficiario"),
                        "documento": info.get("documento", ""),
                        "servicio": info.get("servicio", payload["servicio"]),
                        "hora": info.get("hora", "más temprano"),
                    },
                )
            if err.status == 404 or err.codigo == "NO_BENEFICIARIO":
                return ResultadoCanje(tipo="no_beneficiario", datos={})
            if err.status == 422 or err.codigo == "CODIGO_NO_RECONOCIDO":
                return ResultadoCanje(tipo="no_reconocido", datos={})
            raise
        except SinConexionError:
            return ResultadoCanje(
                tipo="error_conexion",
                datos={"mensaje": "Sin conexión con el servidor de FoodPass."},
            )
