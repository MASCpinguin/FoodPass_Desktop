"""Pantalla 5 · Resumen del día (RF-ES05 · CU-12) y diálogo del reporte de
entregas con exportación a Excel (RF-ES24 · CU-06).
"""

from datetime import date
from pathlib import Path

from PySide6.QtCore import QDate, Qt, QTimer, Signal
from PySide6.QtWidgets import (
    QComboBox,
    QDateEdit,
    QDialog,
    QFileDialog,
    QFrame,
    QGridLayout,
    QHBoxLayout,
    QHeaderView,
    QLabel,
    QPushButton,
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
    QWidget,
)

from foodpass_desktop.api.trabajador import ejecutar_en_segundo_plano
from foodpass_desktop.services import reportes_service
from foodpass_desktop.storage import consultas_bd
from foodpass_desktop.ui.widgets import (
    Aviso,
    BotonNeutro,
    BotonPrincipal,
    BotonSecundario,
    TarjetaMetrica,
    etiqueta,
)


DIAS = ("lunes", "martes", "miércoles", "jueves", "viernes", "sábado", "domingo")
MESES = (
    "enero",
    "febrero",
    "marzo",
    "abril",
    "mayo",
    "junio",
    "julio",
    "agosto",
    "septiembre",
    "octubre",
    "noviembre",
    "diciembre",
)


def fecha_legible(fecha):
    """«2026-11-28» -> «Sábado 28 de noviembre de 2026» (sin depender del idioma de Windows)."""
    try:
        d = date.fromisoformat(str(fecha)[:10])
    except ValueError:
        return f"Día {fecha}"
    return (
        f"{DIAS[d.weekday()].capitalize()} {d.day} de {MESES[d.month - 1]} de {d.year}"
    )


class ResumenView(QWidget):
    actualizar_solicitado = Signal()
    abrir_reporte = Signal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("paginaContenido")
        raiz = QVBoxLayout(self)
        raiz.setContentsMargins(36, 30, 36, 28)
        raiz.setSpacing(18)
        encabezado = QHBoxLayout()
        col = QVBoxLayout()
        col.addWidget(etiqueta("Resumen del día", "tituloPantalla", False))
        self.lbl_fecha = etiqueta(
            "Se calcula con los canjes registrados. No se guarda.",
            "descripcionPantalla",
        )
        col.addWidget(self.lbl_fecha)
        encabezado.addLayout(col, 1)
        self.btn_reporte = BotonSecundario("Reporte de canjes")
        self.btn_reporte.clicked.connect(self.abrir_reporte.emit)
        self.btn_actualizar = BotonPrincipal("Actualizar")
        self.btn_actualizar.clicked.connect(self.actualizar_solicitado.emit)
        encabezado.addWidget(self.btn_reporte)
        encabezado.addWidget(self.btn_actualizar)
        raiz.addLayout(encabezado)

        self.aviso = Aviso("", "advertencia")
        raiz.addWidget(self.aviso)

        rejilla = QGridLayout()
        rejilla.setSpacing(16)
        self.total = TarjetaMetrica("Total de canjes", destacada=True)
        rejilla.addWidget(self.total, 0, 0, 2, 1)
        self.servicios = {}
        for i, s in enumerate(("desayuno", "almuerzo", "refrigerio")):
            t = TarjetaMetrica(s.capitalize())
            self.servicios[s] = t
            rejilla.addWidget(t, 0, i + 1)
        self.por_codigo = TarjetaMetrica("Con código FoodPass")
        self.por_documento = TarjetaMetrica("Por documento (F2)")
        self.anulados = TarjetaMetrica("Canjes anulados")
        rejilla.addWidget(self.por_codigo, 1, 1)
        rejilla.addWidget(self.por_documento, 1, 2)
        rejilla.addWidget(self.anulados, 1, 3)
        raiz.addLayout(rejilla)
        raiz.addStretch()

    def actualizar(self, resumen, conectado=True):
        if not conectado or resumen is None:
            self.aviso.fijar(
                "No hay conexión con la base de datos. Las cifras pueden estar desactualizadas.",
                "advertencia",
            )
            return
        self.aviso.fijar("", "advertencia")
        self.lbl_fecha.setText(
            f"{fecha_legible(resumen['fecha'])} · se calcula con los canjes "
            "registrados. No se guarda."
        )
        self.total.fijar(resumen["total"], "canjes del día")
        for s, t in self.servicios.items():
            t.fijar(resumen["por_servicio"][s])
        self.por_codigo.fijar(resumen["por_modalidad"]["qr"])
        self.por_documento.fijar(resumen["por_modalidad"]["manual"])
        self.anulados.fijar(resumen["anulados"], "no suman en el total")


class DialogoReporteEntregas(QDialog):
    """RF-ES24: periodo (máx. 93 días), servicio, detalle, totales y Excel.

    Los filtros se aplican solos (sin botón «Consultar») y el Excel sale con lo
    que está en pantalla. Una sola acción principal: «Exportar a Excel».
    """

    def __init__(self, parent=None, consultar=consultas_bd.reporte_entregas):
        super().__init__(parent)
        self._consultar = consultar
        self._reporte = None
        self.setWindowTitle("Reporte de canjes")
        self.resize(980, 660)
        raiz = QVBoxLayout(self)
        raiz.setContentsMargins(28, 24, 28, 24)
        raiz.setSpacing(14)
        raiz.addWidget(etiqueta("Reporte de canjes", "tituloDialogo", False))
        raiz.addWidget(
            etiqueta(
                "Elige el periodo y el servicio: la tabla se actualiza sola y el "
                "Excel sale con lo que ves aquí.",
                "descripcionPantalla",
            )
        )

        # --- tarjeta de filtros ----------------------------------------------
        tarjeta = QFrame()
        tarjeta.setObjectName("tarjetaFiltros")
        filtros = QHBoxLayout(tarjeta)
        filtros.setContentsMargins(18, 14, 18, 14)
        filtros.setSpacing(14)
        hoy = QDate.currentDate()
        self.desde = QDateEdit(hoy)
        self.hasta = QDateEdit(hoy)
        for campo in (self.desde, self.hasta):
            campo.setCalendarPopup(True)
            campo.setDisplayFormat("yyyy-MM-dd")
            campo.setMinimumWidth(150)
        self.servicio = QComboBox()
        self.servicio.setSizeAdjustPolicy(QComboBox.SizeAdjustPolicy.AdjustToContents)
        self.servicio.setMinimumWidth(200)
        self.servicio.addItems(
            ["Todos los servicios", "Desayuno", "Almuerzo", "Refrigerio"]
        )
        for texto, w in (
            ("Desde", self.desde),
            ("Hasta", self.hasta),
            ("Servicio", self.servicio),
        ):
            caja = QVBoxLayout()
            caja.setSpacing(6)
            caja.addWidget(etiqueta(texto, "etiquetaCampo", False))
            caja.addWidget(w)
            filtros.addLayout(caja)
        filtros.addStretch()
        rapidos = QVBoxLayout()
        rapidos.setSpacing(6)
        rapidos.addWidget(etiqueta("Rápido", "etiquetaCampo", False))
        fila_rapida = QHBoxLayout()
        fila_rapida.setSpacing(6)
        for texto, dias in (("Hoy", 0), ("7 días", 6), ("Este mes", None)):
            boton = QPushButton(texto)
            boton.setObjectName("chipFiltro")
            boton.setCursor(Qt.CursorShape.PointingHandCursor)
            boton.clicked.connect(lambda _c=False, d=dias: self._rango_rapido(d))
            fila_rapida.addWidget(boton)
        rapidos.addLayout(fila_rapida)
        filtros.addLayout(rapidos)
        raiz.addWidget(tarjeta)

        # Consulta automática al cambiar un filtro (con una pausa corta para no
        # consultar en cada clic de la fecha).
        self._espera = QTimer(self)
        self._espera.setSingleShot(True)
        self._espera.setInterval(300)
        self._espera.timeout.connect(self.consultar)
        self.desde.dateChanged.connect(self._programar)
        self.hasta.dateChanged.connect(self._programar)
        self.servicio.currentIndexChanged.connect(self._programar)

        self.aviso = Aviso("", "info")
        raiz.addWidget(self.aviso)
        self.tabla = QTableWidget(0, 5)
        self.tabla.setHorizontalHeaderLabels(
            ["Fecha y hora", "Documento", "Nombre", "Servicio", "Modalidad"]
        )
        self.tabla.horizontalHeader().setSectionResizeMode(
            2, QHeaderView.ResizeMode.Stretch
        )
        self.tabla.verticalHeader().setVisible(False)
        self.tabla.horizontalHeader().setDefaultAlignment(
            Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter
        )
        self.tabla.setAlternatingRowColors(True)
        self.tabla.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        raiz.addWidget(self.tabla, 1)

        # --- pie: totales como badges + acciones -------------------------------
        pie = QHBoxLayout()
        pie.setSpacing(8)
        self.badges_totales = {}
        for clave, texto in (
            ("total", "Total"),
            ("desayuno", "Desayuno"),
            ("almuerzo", "Almuerzo"),
            ("refrigerio", "Refrigerio"),
        ):
            badge = QLabel(f"{texto}  0")
            badge.setObjectName("chipTotal")
            badge.setProperty("principal", "true" if clave == "total" else "false")
            badge.setFixedHeight(34)
            self.badges_totales[clave] = (badge, texto)
            pie.addWidget(badge, 0, Qt.AlignmentFlag.AlignVCenter)
        self.lbl_totales = etiqueta("", "textoSecundario")  # texto para lectores
        self.lbl_totales.hide()
        pie.addStretch()
        cerrar = BotonNeutro("Cerrar")
        cerrar.clicked.connect(self.accept)
        self.btn_exportar = BotonPrincipal("Exportar a Excel")
        self.btn_exportar.setEnabled(False)
        self.btn_exportar.clicked.connect(self.exportar)
        pie.addWidget(cerrar)
        pie.addWidget(self.btn_exportar)
        raiz.addLayout(pie)
        self.tabla.setFocus()  # que no abra con la fecha seleccionada
        self.consultar()

    def _programar(self, *_):
        self._espera.start()

    def _rango_rapido(self, dias):
        hoy = QDate.currentDate()
        inicio = (
            QDate(hoy.year(), hoy.month(), 1) if dias is None else hoy.addDays(-dias)
        )
        for campo in (self.desde, self.hasta):
            campo.blockSignals(True)
        self.desde.setDate(inicio)
        self.hasta.setDate(hoy)
        for campo in (self.desde, self.hasta):
            campo.blockSignals(False)
        self.consultar()

    def consultar(self):
        servicio = self.servicio.currentText()
        servicio = None if servicio.startswith("Todos") else servicio
        self.btn_exportar.setEnabled(False)
        ejecutar_en_segundo_plano(
            self._consultar,
            self.desde.date().toString("yyyy-MM-dd"),
            self.hasta.date().toString("yyyy-MM-dd"),
            servicio,
            al_exito=self._mostrar,
            al_error=self._error,
        )

    def _mostrar(self, reporte):
        self._reporte = reporte
        filas = reporte["detalle"]
        self.tabla.setRowCount(len(filas))
        for i, r in enumerate(filas):
            for j, clave in enumerate(
                ("fecha_hora", "documento", "nombre", "servicio", "modalidad")
            ):
                self.tabla.setItem(i, j, QTableWidgetItem(str(r[clave])))
        self.tabla.resizeColumnsToContents()
        self.tabla.horizontalHeader().setSectionResizeMode(
            2, QHeaderView.ResizeMode.Stretch
        )
        t = reporte["totales"]
        valores = {"total": reporte["total"], **t}
        for clave, (badge, texto) in self.badges_totales.items():
            badge.setText(f"{texto}  {valores.get(clave, 0)}")
        self.lbl_totales.setText(
            f"Total: {reporte['total']}  ·  Desayuno {t['desayuno']}  ·  Almuerzo {t['almuerzo']}  ·  Refrigerio {t['refrigerio']}"
        )
        self.aviso.fijar("" if filas else "No hay canjes en el periodo.", "info")
        self.btn_exportar.setEnabled(bool(filas))

    def _error(self, error):
        texto = (
            str(error)
            if isinstance(error, ValueError)
            else "No se pudo consultar. Revisa la conexión o avisa a soporte técnico."
        )
        self.aviso.fijar(texto, "error")
        self.btn_exportar.setEnabled(False)

    def exportar(self):
        if not self._reporte:
            return
        carpeta = Path.home() / "Documents"
        sugerido = str(
            (carpeta if carpeta.exists() else Path.home())
            / reportes_service.nombre_archivo("Canjes")
        )
        ruta, _ = QFileDialog.getSaveFileName(
            self, "Guardar reporte", sugerido, "Excel (*.xlsx)"
        )
        if not ruta:
            return
        reportes_service.exportar_entregas(self._reporte, ruta)
        self.aviso.fijar(f"Reporte guardado en {ruta}", "info")
