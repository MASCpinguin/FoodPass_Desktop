from __future__ import annotations

import csv
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

try:
    from foodpass_desktop.utils.seguridad_excel import (
        cargar_valores_excel,
        tiene_prefijo_peligroso,
    )
except ModuleNotFoundError:
    import openpyxl

    _PREFIJOS_PELIGROSOS = ("=", "+", "-", "@", "\t", "\r")

    def cargar_valores_excel(
        ruta_archivo: str | Path,
        *,
        data_only: bool = True,
    ) -> Any:
        """Abre un libro de Excel como respaldo cuando seguridad_excel no está en la rama."""
        return openpyxl.load_workbook(ruta_archivo, data_only=data_only)

    def tiene_prefijo_peligroso(valor: Any) -> bool:
        """Detecta prefijos potencialmente peligrosos en celdas de hoja de cálculo."""
        if valor is None:
            return False
        texto = str(valor).lstrip()
        return texto.startswith(_PREFIJOS_PELIGROSOS)


ESTADOS_VALIDOS = {"activo", "inactivo"}


@dataclass
class ErrorFilaImportacion:
    fila: int
    motivo: str


@dataclass
class VistaPreviaImportacion:
    archivo: str
    altas: list[dict[str, Any]] = field(default_factory=list)
    cambios: list[dict[str, Any]] = field(default_factory=list)
    bajas: list[dict[str, Any]] = field(default_factory=list)
    errores: list[ErrorFilaImportacion] = field(default_factory=list)

    @property
    def conteos(self) -> dict[str, int]:
        return {
            "altas": len(self.altas),
            "cambios": len(self.cambios),
            "bajas": len(self.bajas),
            "errores": len(self.errores),
        }


def _leer_filas_archivo(ruta_archivo: str | Path) -> list[tuple[int, list[Any]]]:
    """Lee filas de un archivo .xlsx (como valores) o .csv devolviendo (num_fila, valores)."""
    path = Path(ruta_archivo)
    extension = path.suffix.lower()

    if extension == ".xlsx":
        wb = cargar_valores_excel(str(path), data_only=True)
        try:
            ws = wb.active
            if ws is None:
                return []
            filas: list[tuple[int, list[Any]]] = []
            for idx, row in enumerate(
                ws.iter_rows(min_row=2, values_only=True), start=2
            ):
                if row is None or not any(
                    cell is not None and str(cell).strip() != "" for cell in row
                ):
                    continue
                filas.append((idx, list(row)))
            return filas
        finally:
            wb.close()

    if extension == ".csv":
        filas_csv: list[tuple[int, list[Any]]] = []
        with path.open("r", encoding="utf-8-sig", newline="") as f:
            reader = csv.reader(f)
            encabezado = next(reader, None)
            if encabezado is None:
                return []
            for idx, row in enumerate(reader, start=2):
                if not row or not any(str(cell).strip() != "" for cell in row):
                    continue
                filas_csv.append((idx, row))
        return filas_csv

    raise ValueError(f"Formato de archivo no soportado: {extension}. Use .xlsx o .csv")


def _normalizar_fila_v21(valores: list[Any]) -> dict[str, str]:
    """
    Normaliza columnas v2.1:
    numero_documento, nombre_completo, email (opcional), estado
    """
    celdas = [str(v).strip() if v is not None else "" for v in valores]
    while len(celdas) < 4:
        celdas.append("")
    return {
        "numero_documento": celdas[0],
        "nombre_completo": celdas[1],
        "email": celdas[2],
        "estado": celdas[3].lower(),
    }


def generar_vista_previa_importacion(
    ruta_archivo: str | Path,
    beneficiarios_actuales: list[dict[str, Any]],
) -> VistaPreviaImportacion:
    """
        Valida un archivo de beneficiarios (.xlsx o .csv) y calcula:
    - altas: documentos nuevos válidos
    - cambios: documentos existentes con nombre, email o estado distintos
    - bajas: beneficiarios activos actuales cuyo documento no viene en el archivo
    - errores: filas con fórmula peligrosa, documento vacío/repetido o estado inválido
    """
    vista = VistaPreviaImportacion(archivo=Path(ruta_archivo).name)
    filas_leidas = _leer_filas_archivo(ruta_archivo)

    actuales_por_doc: dict[str, dict[str, Any]] = {}
    for ben in beneficiarios_actuales:
        doc = str(ben.get("numero_documento", "")).strip()
        if doc:
            actuales_por_doc[doc] = ben

    documentos_archivo: dict[str, int] = {}
    registros_validos: list[dict[str, str]] = []

    for num_fila, valores in filas_leidas:
        # 1. Bloqueo de inyección de fórmulas (=, +, -, @) en cualquier celda
        if any(tiene_prefijo_peligroso(celda) for celda in valores):
            vista.errores.append(
                ErrorFilaImportacion(
                    fila=num_fila, motivo="Contenido no permitido (=, +, -, @)"
                )
            )
            continue

        registro = _normalizar_fila_v21(valores)
        doc = registro["numero_documento"]
        nombre = registro["nombre_completo"]
        estado = registro["estado"]

        # 2. Documento vacío
        if not doc:
            vista.errores.append(
                ErrorFilaImportacion(fila=num_fila, motivo="Documento vacío")
            )
            continue

        # 3. Nombre vacío
        if not nombre:
            vista.errores.append(
                ErrorFilaImportacion(fila=num_fila, motivo="Nombre vacío")
            )
            continue

        # 4. Estado inválido
        if estado not in ESTADOS_VALIDOS:
            vista.errores.append(
                ErrorFilaImportacion(
                    fila=num_fila, motivo="Estado inválido (debe ser activo o inactivo)"
                )
            )
            continue

        # 5. Documento repetido en el mismo archivo
        if doc in documentos_archivo:
            fila_anterior = documentos_archivo[doc]
            vista.errores.append(
                ErrorFilaImportacion(
                    fila=num_fila,
                    motivo=f"Documento repetido (también en la fila {fila_anterior})",
                )
            )
            continue

        documentos_archivo[doc] = num_fila
        registros_validos.append(registro)

    # Clasificar altas y cambios
    for reg in registros_validos:
        doc = reg["numero_documento"]
        actual = actuales_por_doc.get(doc)
        if actual is None:
            vista.altas.append(reg)
        else:
            nombre_actual = str(actual.get("nombre_completo", "")).strip()
            email_actual = str(actual.get("email") or "").strip()
            estado_actual = str(actual.get("estado", "")).strip().lower()

            if (
                reg["nombre_completo"] != nombre_actual
                or reg["email"] != email_actual
                or reg["estado"] != estado_actual
            ):
                vista.cambios.append(
                    {
                        **reg,
                        "estado_anterior": estado_actual,
                    }
                )

    # Clasificar bajas: beneficiarios activos que no aparecen en el archivo
    for doc, actual in actuales_por_doc.items():
        estado_actual = str(actual.get("estado", "")).strip().lower()
        if estado_actual == "activo" and doc not in documentos_archivo:
            vista.bajas.append(
                {
                    "numero_documento": doc,
                    "nombre_completo": str(actual.get("nombre_completo", "")).strip(),
                    "email": str(actual.get("email") or "").strip(),
                    "estado": "inactivo",
                }
            )

    return vista


def aplicar_vista_previa_importacion(
    vista: VistaPreviaImportacion,
    beneficiarios_actuales: list[dict[str, Any]],
    *,
    confirmado: bool,
    aplicar_bajas: bool = False,
    confirmar_omitir_errores: bool = False,
) -> list[dict[str, Any]]:
    """
        Aplica la vista previa sobre la lista de beneficiarios solo si está confirmada.
    - No aplica nada si confirmado es False.
    - Si hay errores y no se confirma omitirlos, lanza ValueError.
    - Aplica bajas solo si aplicar_bajas es True.
    """
    if not confirmado:
        raise PermissionError(
            "Debe confirmar la vista previa antes de aplicar la importación."
        )

    if vista.errores and not confirmar_omitir_errores:
        raise ValueError(
            "Existen filas con error. Confirme explícitamente que desea omitirlas antes de aplicar."
        )

    por_doc: dict[str, dict[str, Any]] = {
        str(b.get("numero_documento", "")).strip(): dict(b)
        for b in beneficiarios_actuales
        if str(b.get("numero_documento", "")).strip()
    }

    for cambio in vista.cambios:
        doc = cambio["numero_documento"]
        if doc in por_doc:
            por_doc[doc]["nombre_completo"] = cambio["nombre_completo"]
            por_doc[doc]["email"] = cambio["email"]
            por_doc[doc]["estado"] = cambio["estado"]

    for alta in vista.altas:
        doc = alta["numero_documento"]
        por_doc[doc] = {
            "numero_documento": alta["numero_documento"],
            "nombre_completo": alta["nombre_completo"],
            "email": alta["email"],
            "estado": alta["estado"],
        }

    if aplicar_bajas:
        for baja in vista.bajas:
            doc = baja["numero_documento"]
            if doc in por_doc:
                por_doc[doc]["estado"] = "inactivo"

    return list(por_doc.values())
