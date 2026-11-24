"""Pantalla 4 · Beneficiarios (RF-ES18, RF-ES27, RF-ES36, RF-ES28 · CU-13, CU-14)."""

from pathlib import Path

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QCheckBox,
    QComboBox,
    QDialog,
    QFileDialog,
    QHBoxLayout,
    QHeaderView,
    QLineEdit,
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
    QWidget,
)

from foodpass_desktop.api.trabajador import ejecutar_en_segundo_plano
from foodpass_desktop.services import beneficiarios_service, reportes_service
from foodpass_desktop.storage import consultas_bd
from foodpass_desktop.ui.widgets import (
    Aviso,
    BotonNeutro,
    BotonPrincipal,
    BotonSecundario,
    TarjetaMetrica,
    etiqueta,
)

POR_PAGINA = beneficiarios_service.POR_PAGINA


def _tabla(columnas):
    tabla = QTableWidget(0, len(columnas))
    tabla.setHorizontalHeaderLabels(columnas)
    tabla.verticalHeader().setVisible(False)
    tabla.setAlternatingRowColors(True)
    tabla.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
    tabla.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
    tabla.horizontalHeader().setStretchLastSection(True)
    return tabla


class DialogoVistaPrevia(QDialog):
    """Vista previa: nada se aplica sin confirmar (RF-ES18)."""

    def __init__(self, vista, parent=None):
        super().__init__(parent)
        self.vista = vista
        self.setWindowTitle("Vista previa de la importación")
        self.resize(900, 600)
        raiz = QVBoxLayout(self)
        raiz.setContentsMargins(28, 24, 28, 24)
        raiz.setSpacing(12)
        raiz.addWidget(
            etiqueta(f"Vista previa · {vista.archivo}", "tituloDialogo", False)
        )
        c = vista.conteos
        fila = QHBoxLayout()
        for texto, n in (
            ("Altas", c["altas"]),
            ("Cambios", c["cambios"]),
            ("Bajas", c["bajas"]),
            ("Filas con error", c["errores"]),
        ):
            t = TarjetaMetrica(texto)
            t.fijar(n)
            fila.addWidget(t)
        raiz.addLayout(fila)
        if vista.errores:
            raiz.addWidget(
                Aviso(
                    "Las filas con error no se aplican. Corrígelas en el Excel y vuelve a importar, o aplica solo las válidas.",
                    "advertencia",
                )
            )
            tabla = _tabla(["Fila", "Motivo"])
            tabla.setRowCount(len(vista.errores))
            for i, e in enumerate(vista.errores):
                tabla.setItem(i, 0, QTableWidgetItem(str(e.fila)))
                tabla.setItem(i, 1, QTableWidgetItem(e.motivo))
            tabla.setColumnWidth(0, 80)
            raiz.addWidget(tabla, 1)
        else:
            raiz.addWidget(Aviso("No hay filas con error.", "info"))
            raiz.addStretch()
        self.chk_bajas = QCheckBox(
            f"Aplicar bajas: dejar inactivos a los {c['bajas']} beneficiarios que no están en el archivo"
        )
        self.chk_bajas.setEnabled(c["bajas"] > 0)
        raiz.addWidget(self.chk_bajas)
        pie = QHBoxLayout()
        pie.addStretch()
        cancelar = BotonNeutro("Cancelar")
        cancelar.clicked.connect(self.reject)
        validas = c["altas"] + c["cambios"]
        self.btn_confirmar = BotonPrincipal("Confirmar importación")
        self.btn_confirmar.setEnabled(validas > 0 or c["bajas"] > 0)
        self.btn_confirmar.clicked.connect(self.accept)
        pie.addWidget(cancelar)
        pie.addWidget(self.btn_confirmar)
        raiz.addLayout(pie)


class DialogoBeneficiario(QDialog):
    """RF-ES28 (Debería): alta o edición individual."""

    def __init__(self, beneficiario=None, parent=None):
        super().__init__(parent)
        self.beneficiario = beneficiario or {}
        self.setWindowTitle("Beneficiario")
        self.setFixedWidth(480)
        raiz = QVBoxLayout(self)
        raiz.setContentsMargins(28, 24, 28, 24)
        raiz.setSpacing(10)
        raiz.addWidget(
            etiqueta(
                "Editar beneficiario" if beneficiario else "Nuevo beneficiario",
                "tituloDialogo",
                False,
            )
        )
        self.campos = {}
        for clave, texto in (
            ("numero_documento", "Número de documento"),
            ("nombre_completo", "Nombre completo"),
            ("email", "Correo"),
        ):
            raiz.addWidget(etiqueta(texto, "etiquetaCampo", False))
            campo = QLineEdit(str(self.beneficiario.get(clave, "")))
            self.campos[clave] = campo
            raiz.addWidget(campo)
        raiz.addWidget(etiqueta("Estado", "etiquetaCampo", False))
        self.estado = QComboBox()
        self.estado.addItems(["activo", "inactivo"])
        self.estado.setCurrentText(self.beneficiario.get("estado", "activo"))
        raiz.addWidget(self.estado)
        self.error = etiqueta("", "errorDialogo")
        raiz.addWidget(self.error)
        pie = QHBoxLayout()
        pie.addStretch()
        cancelar = BotonNeutro("Cancelar")
        cancelar.clicked.connect(self.reject)
        guardar = BotonPrincipal("Guardar")
        guardar.clicked.connect(self._validar)
        pie.addWidget(cancelar)
        pie.addWidget(guardar)
        raiz.addLayout(pie)

    def _validar(self):
        d = self.datos()
        if not d["numero_documento"].isdigit() or len(d["numero_documento"]) < 5:
            self.error.setText("Escribe un documento válido (solo números, mínimo 5).")
        elif not d["nombre_completo"]:
            self.error.setText("Escribe el nombre completo.")
        elif not beneficiarios_service._PATRON_EMAIL.match(d["email"]):
            self.error.setText("Escribe un correo válido.")
        else:
            self.accept()

    def datos(self):
        d = {k: c.text().strip() for k, c in self.campos.items()}
        d["estado"] = self.estado.currentText()
        if self.beneficiario.get("id"):
            d["id"] = self.beneficiario["id"]
        return d


class BeneficiariosView(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("paginaContenido")
        self._todos = []
        self._filtrados = []
        self._pagina = 0
        raiz = QVBoxLayout(self)
        raiz.setContentsMargins(36, 30, 36, 24)
        raiz.setSpacing(14)
        encabezado = QHBoxLayout()
        col = QVBoxLayout()
        col.addWidget(etiqueta("Beneficiarios", "tituloPantalla", False))
        col.addWidget(
            etiqueta(
                "Importa la lista del SENA con la plantilla y consulta quién tiene el apoyo.",
                "descripcionPantalla",
            )
        )
        encabezado.addLayout(col, 1)
        self.btn_plantilla = BotonSecundario("Descargar plantilla")
        self.btn_plantilla.clicked.connect(self.descargar_plantilla)
        self.btn_importar = BotonPrincipal("Importar archivo")
        self.btn_importar.clicked.connect(self.importar)
        encabezado.addWidget(self.btn_plantilla)
        encabezado.addWidget(self.btn_importar)
        raiz.addLayout(encabezado)

        metricas = QHBoxLayout()
        self.m_activos = TarjetaMetrica("Activos")
        self.m_inactivos = TarjetaMetrica("Inactivos")
        self.m_total = TarjetaMetrica("Total en la base")
        for m in (self.m_activos, self.m_inactivos, self.m_total):
            metricas.addWidget(m)
        raiz.addLayout(metricas)

        self.aviso = Aviso("", "info")
        raiz.addWidget(self.aviso)

        filtros = QHBoxLayout()
        self.buscar = QLineEdit()
        self.buscar.setPlaceholderText("Busca por nombre o documento")
        self.buscar.textChanged.connect(self._filtrar)
        self.estado = QComboBox()
        self.estado.addItems(["Activos", "Inactivos", "Todos"])
        self.estado.currentIndexChanged.connect(self._filtrar)
        self.btn_nuevo = BotonNeutro("Nuevo beneficiario")
        self.btn_nuevo.clicked.connect(lambda: self.editar(None))
        filtros.addWidget(self.buscar, 1)
        filtros.addWidget(self.estado)
        filtros.addWidget(self.btn_nuevo)
        raiz.addLayout(filtros)

        self.tabla = _tabla(["Documento", "Nombre completo", "Correo", "Estado"])
        cabecera = self.tabla.horizontalHeader()
        cabecera.setStretchLastSection(False)
        cabecera.setSectionResizeMode(0, QHeaderView.ResizeMode.ResizeToContents)
        cabecera.setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)
        cabecera.setSectionResizeMode(2, QHeaderView.ResizeMode.Stretch)
        cabecera.setSectionResizeMode(3, QHeaderView.ResizeMode.ResizeToContents)
        self.tabla.doubleClicked.connect(self._editar_fila)
        raiz.addWidget(self.tabla, 1)

        pie = QHBoxLayout()
        self.lbl_pagina = etiqueta("", "textoSecundario", False)
        self.btn_anterior = BotonNeutro("Anterior")
        self.btn_siguiente = BotonNeutro("Siguiente")
        self.btn_anterior.clicked.connect(lambda: self._cambiar_pagina(-1))
        self.btn_siguiente.clicked.connect(lambda: self._cambiar_pagina(1))
        pie.addWidget(self.lbl_pagina, 1)
        pie.addWidget(self.btn_anterior)
        pie.addWidget(self.btn_siguiente)
        raiz.addLayout(pie)

    # --- datos ------------------------------------------------------------------
    def cargar(self):
        ejecutar_en_segundo_plano(
            consultas_bd.listar_beneficiarios,
            al_exito=self._cargado,
            al_error=self._error,
        )

    def _cargado(self, lista):
        self._todos = lista
        activos = sum(1 for b in lista if b["estado"] == "activo")
        self.m_activos.fijar(activos)
        self.m_inactivos.fijar(len(lista) - activos)
        self.m_total.fijar(len(lista))
        self._filtrar()

    def _error(self, _error):
        self.aviso.fijar(
            "No se pudo leer la base de beneficiarios. Revisa la conexión o avisa a soporte técnico.",
            "error",
        )

    def _filtrar(self):
        estado = {"Activos": "activo", "Inactivos": "inactivo"}.get(
            self.estado.currentText(), "todos"
        )
        self._filtrados = beneficiarios_service.filtrar(
            self._todos, self.buscar.text(), estado
        )
        self._pagina = 0
        self._pintar()

    def _cambiar_pagina(self, paso):
        self._pagina += paso
        self._pintar()

    def _pintar(self):
        paginas = max(1, -(-len(self._filtrados) // POR_PAGINA))
        self._pagina = max(0, min(self._pagina, paginas - 1))
        inicio = self._pagina * POR_PAGINA
        filas = self._filtrados[inicio : inicio + POR_PAGINA]
        self.tabla.setRowCount(len(filas))
        for i, b in enumerate(filas):
            for j, clave in enumerate(
                ("numero_documento", "nombre_completo", "email", "estado")
            ):
                item = QTableWidgetItem(
                    str(b[clave]).capitalize() if clave == "estado" else str(b[clave])
                )
                item.setData(Qt.ItemDataRole.UserRole, b)
                self.tabla.setItem(i, j, item)
        self.lbl_pagina.setText(
            f"{len(self._filtrados)} resultados · página {self._pagina + 1} de {paginas}"
        )
        self.btn_anterior.setEnabled(self._pagina > 0)
        self.btn_siguiente.setEnabled(self._pagina < paginas - 1)

    # --- acciones ---------------------------------------------------------------
    def descargar_plantilla(self):
        sugerido = str(Path.home() / "plantilla_beneficiarios.xlsx")
        ruta, _ = QFileDialog.getSaveFileName(
            self, "Guardar plantilla", sugerido, "Excel (*.xlsx)"
        )
        if ruta:
            reportes_service.crear_plantilla_beneficiarios(ruta, self._todos)
            n = len(self._todos)
            self.aviso.fijar(
                f"Plantilla guardada en {ruta} con los {n} beneficiarios actuales. "
                "Agrega o corrige filas y luego usa «Importar archivo».",
                "info",
            )

    def importar(self):
        ruta, _ = QFileDialog.getOpenFileName(
            self, "Importar beneficiarios", str(Path.home()), "Plantilla (*.xlsx *.csv)"
        )
        if not ruta:
            return
        self.importar_desde(ruta)

    def importar_desde(self, ruta):
        try:
            vista = beneficiarios_service.vista_previa(ruta, self._todos)
        except ValueError as e:
            self.aviso.fijar(str(e), "error")
            return
        dialogo = DialogoVistaPrevia(vista, self)
        if dialogo.exec() != QDialog.DialogCode.Accepted:
            self.aviso.fijar("Importación cancelada. No se cambió nada.", "info")
            return
        ejecutar_en_segundo_plano(
            beneficiarios_service.aplicar,
            vista,
            dialogo.chk_bajas.isChecked(),
            al_exito=self._importado,
            al_error=self._error_importar,
        )

    def _importado(self, r):
        self.aviso.fijar(
            f"Importación aplicada: {r['altas']} altas, {r['cambios']} cambios y {r['bajas']} bajas.",
            "info",
        )
        self.cargar()

    def _error_importar(self, _e):
        self.aviso.fijar(
            "No se pudo aplicar la importación. No se cambió nada. Avisa a soporte técnico.",
            "error",
        )

    def _editar_fila(self, indice):
        item = self.tabla.item(indice.row(), 0)
        if item:
            self.editar(item.data(Qt.ItemDataRole.UserRole))

    def editar(self, beneficiario):
        dialogo = DialogoBeneficiario(beneficiario, self)
        if dialogo.exec() != QDialog.DialogCode.Accepted:
            return
        ejecutar_en_segundo_plano(
            consultas_bd.guardar_beneficiario,
            dialogo.datos(),
            al_exito=self._guardado,
            al_error=self._error,
        )

    def _guardado(self, resultado):
        ok, mensaje = resultado
        self.aviso.fijar(mensaje, "info" if ok else "error")
        if ok:
            self.cargar()
