"""Beneficiarios contra la base (RF-ES18, RF-ES27, RF-ES36, RF-ES28).

Reutiliza la vista previa de T17 (importacion_beneficiarios_service) y le
agrega la regla de la v2.2: el correo es obligatorio, válido y único, porque
beneficiarios_sena lo exige (RN14).
"""

import re
import unicodedata

from foodpass_desktop.services.importacion_beneficiarios_service import (
    ErrorFilaImportacion,
    VistaPreviaImportacion,
    _leer_filas_archivo,
    _normalizar_fila_v21,
    generar_vista_previa_importacion,
)
from foodpass_desktop.storage import consultas_bd

_PATRON_EMAIL = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")
POR_PAGINA = 50


def normalizar(texto: str) -> str:
    """Minúsculas, sin tildes y con espacios simples (búsqueda C-13)."""
    texto = unicodedata.normalize("NFD", (texto or "").lower())
    texto = "".join(c for c in texto if unicodedata.category(c) != "Mn")
    return " ".join(texto.split())


def filtrar(beneficiarios, texto="", estado="activo"):
    """RF-ES36: nombre parcial sin tildes ni mayúsculas, documento por prefijo."""
    buscado = normalizar(texto)
    resultado = []
    for b in beneficiarios:
        if estado != "todos" and b["estado"] != estado:
            continue
        if buscado and not (
            buscado in normalizar(b["nombre_completo"])
            or str(b["numero_documento"]).startswith(buscado)
        ):
            continue
        resultado.append(b)
    return resultado


def validar_correos(vista: VistaPreviaImportacion, actuales) -> VistaPreviaImportacion:
    """Mueve a errores las filas con correo vacío, inválido o repetido."""
    dueno_correo = {
        (b.get("email") or "").strip().lower(): str(b["numero_documento"])
        for b in actuales
        if b.get("email")
    }
    vistos = {}
    for lista in (vista.altas, vista.cambios):
        conservar = []
        for reg in lista:
            correo = (reg.get("email") or "").strip().lower()
            doc = str(reg["numero_documento"])
            fila = reg.get("_fila", 0)
            if not correo:
                motivo = "Correo vacío"
            elif not _PATRON_EMAIL.match(correo):
                motivo = "Correo inválido"
            elif correo in vistos and vistos[correo] != doc:
                motivo = "Correo repetido en el archivo"
            elif dueno_correo.get(correo, doc) != doc:
                motivo = "Correo de otro beneficiario"
            else:
                vistos[correo] = doc
                reg["email"] = correo
                conservar.append(reg)
                continue
            vista.errores.append(ErrorFilaImportacion(fila=fila, motivo=motivo))
        lista[:] = conservar
    vista.errores.sort(key=lambda e: e.fila)
    return vista


def vista_previa(ruta_archivo, actuales=None):
    actuales = actuales if actuales is not None else consultas_bd.listar_beneficiarios()
    vista = generar_vista_previa_importacion(ruta_archivo, actuales)
    filas = {}
    for num, valores in _leer_filas_archivo(ruta_archivo):
        filas.setdefault(_normalizar_fila_v21(valores)["numero_documento"], num)
    for reg in vista.altas + vista.cambios:
        reg["_fila"] = filas.get(str(reg["numero_documento"]), 0)
    return validar_correos(vista, actuales)


def aplicar(vista: VistaPreviaImportacion, aplicar_bajas: bool):
    return consultas_bd.aplicar_importacion(
        vista.altas, vista.cambios, vista.bajas if aplicar_bajas else []
    )
