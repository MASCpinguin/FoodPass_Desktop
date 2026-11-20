"""Vista de Ventanilla de Priorización (RF-ES33, RF-ES17, RF-ES20, RF-ES21)."""

from PySide6.QtCore import Qt, QTimer
from PySide6.QtGui import QIntValidator, QKeySequence, QShortcut
from PySide6.QtWidgets import (
    QComboBox,
    QDialog,
    QFrame,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QPushButton,
    QVBoxLayout,
    QWidget,
)

from foodpass_desktop.api.trabajador import ejecutar_en_segundo_plano
from foodpass_desktop.services.canje_service import (
    MOTIVOS_CANJE_MANUAL,
    CanjeService,
    ResultadoCanje,
)
from foodpass_desktop.ui.widgets.tarjeta_resultado import (
    TarjetaResultado,
    _refrescar_estilo,
)


class DialogoCanjeManual(QDialog):
    """Modal rápido para registrar canje manual por documento y motivo (RF-ES21 · F2)."""

    def __init__(self, servicio: str, parent=None):
        super().__init__(parent)
        self.servicio = servicio
        self.setObjectName("dialogoCanjeManual")
        self.setWindowTitle("Canje manual por documento")
        self.setModal(True)
        self.setFixedWidth(440)
        self.setup_ui()

    def setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(28, 28, 28, 28)
        layout.setSpacing(14)

        titulo = QLabel("Canje manual")
        titulo.setObjectName("tituloDialogoManual")
        layout.addWidget(titulo)

        subtitulo = QLabel(
            f"Servicio activo: {self.servicio} · Se busca solo por documento, nunca por ID."
        )
        subtitulo.setObjectName("lblDetallesAprendiz")
        subtitulo.setWordWrap(True)
        layout.addWidget(subtitulo)

        lbl_doc = QLabel("NÚMERO DE DOCUMENTO")
        lbl_doc.setObjectName("etiquetaCampoManual")
        layout.addWidget(lbl_doc)

        self.input_documento = QLineEdit()
        self.input_documento.setObjectName("inputDocumentoManual")
        self.input_documento.setPlaceholderText("Ej. 1000000001")
        self.input_documento.setMaxLength(15)
        self.input_documento.setValidator(QIntValidator(1, 999999999, self))
        self.input_documento.returnPressed.connect(self.intentar_confirmar)
        layout.addWidget(self.input_documento)

        lbl_motivo = QLabel("MOTIVO DEL CANJE MANUAL")
        lbl_motivo.setObjectName("etiquetaCampoManual")
        layout.addWidget(lbl_motivo)

        self.combo_motivo = QComboBox()
        self.combo_motivo.setObjectName("comboMotivoManual")
        self.combo_motivo.addItems(MOTIVOS_CANJE_MANUAL)
        layout.addWidget(self.combo_motivo)

        self.lbl_error = QLabel("")
        self.lbl_error.setStyleSheet(
            "color: #C0392B; font-size: 13px; font-weight: 700;"
        )
        self.lbl_error.setVisible(False)
        layout.addWidget(self.lbl_error)

        fila_botones = QHBoxLayout()
        fila_botones.setSpacing(12)
        fila_botones.addStretch()

        self.btn_cancelar = QPushButton("Cancelar [Esc]")
        self.btn_cancelar.setObjectName("btnCancelarManual")
        self.btn_cancelar.setCursor(Qt.PointingHandCursor)
        self.btn_cancelar.clicked.connect(self.reject)
        fila_botones.addWidget(self.btn_cancelar)

        self.btn_confirmar = QPushButton("Confirmar [Enter]")
        self.btn_confirmar.setObjectName("btnConfirmarManual")
        self.btn_confirmar.setCursor(Qt.PointingHandCursor)
        self.btn_confirmar.clicked.connect(self.intentar_confirmar)
        fila_botones.addWidget(self.btn_confirmar)

        layout.addSpacing(6)
        layout.addLayout(fila_botones)

        self.input_documento.setFocus()

    def intentar_confirmar(self):
        doc = self.input_documento.text().strip()
        if not doc.isdigit() or len(doc) < 5:
            self.lbl_error.setText(
                "Ingrese un número de documento válido (mínimo 5 dígitos)."
            )
            self.lbl_error.setVisible(True)
            self.input_documento.setFocus()
            return
        self.accept()

    def obtener_datos(self) -> tuple[str, str]:
        return self.input_documento.text().strip(), self.combo_motivo.currentText()


class VentanillaView(QWidget):
    """Pantalla 3 · Ventanilla de priorización."""

    def __init__(self, parent=None, servicio_canje: CanjeService | None = None):
        super().__init__(parent)
        self.setObjectName("vistaVentanilla")
        self.servicio_actual = None
        self._procesando = False
        self._dialogo_abierto = False
        self.canje_service = servicio_canje or CanjeService()

        # Timer para limpiar la tarjeta automáticamente a los 4 segundos (RF-ES20)
        self.timer_limpieza = QTimer(self)
        self.timer_limpieza.setSingleShot(True)
        self.timer_limpieza.timeout.connect(self.limpiar_tarjeta_auto)

        self.setup_ui()
        self.registrar_atajos()

    def setup_ui(self):
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(36, 32, 36, 28)
        main_layout.setSpacing(20)

        # 1. Encabezado: Título a la izquierda + Selector en píldora a la derecha
        header_layout = QHBoxLayout()
        header_layout.setSpacing(16)

        col_titulo = QVBoxLayout()
        col_titulo.setSpacing(4)
        lbl_titulo = QLabel("Ventanilla de priorización")
        lbl_titulo.setObjectName("tituloVentanilla")
        lbl_subtitulo = QLabel(
            "Elija el servicio y escanee el QR del aprendiz. No hace falta confirmar."
        )
        lbl_subtitulo.setObjectName("subtituloVentanilla")
        col_titulo.addWidget(lbl_titulo)
        col_titulo.addWidget(lbl_subtitulo)
        header_layout.addLayout(col_titulo, 1)

        # Selector en píldora (Manual v2.1 Sec. 5 y Pantalla 3)
        contenedor_pildora = QFrame()
        contenedor_pildora.setObjectName("contenedorPildoraServicios")
        layout_servicios = QHBoxLayout(contenedor_pildora)
        layout_servicios.setContentsMargins(6, 6, 6, 6)
        layout_servicios.setSpacing(4)

        self.btn_desayuno = QPushButton("Desayuno  F5")
        self.btn_almuerzo = QPushButton("Almuerzo  F6")
        self.btn_refrigerio = QPushButton("Refrigerio  F7")

        for btn in (self.btn_desayuno, self.btn_almuerzo, self.btn_refrigerio):
            btn.setObjectName("btnServicioPildora")
            btn.setCheckable(True)
            btn.setCursor(Qt.PointingHandCursor)
            layout_servicios.addWidget(btn)

        self.btn_desayuno.clicked.connect(lambda: self.seleccionar_servicio("Desayuno"))
        self.btn_almuerzo.clicked.connect(lambda: self.seleccionar_servicio("Almuerzo"))
        self.btn_refrigerio.clicked.connect(
            lambda: self.seleccionar_servicio("Refrigerio")
        )

        header_layout.addWidget(contenedor_pildora, 0, Qt.AlignVCenter)
        main_layout.addLayout(header_layout)

        # 2. Aviso de estado del servicio (RF-ES33)
        self.lbl_aviso_servicio = QLabel(
            "⚠️ Elija un servicio (F5 Desayuno · F6 Almuerzo · F7 Refrigerio) para habilitar la lectura"
        )
        self.lbl_aviso_servicio.setObjectName("avisoServicio")
        self.lbl_aviso_servicio.setProperty("activo", "false")
        _refrescar_estilo(self.lbl_aviso_servicio)
        main_layout.addWidget(self.lbl_aviso_servicio)

        # 3. Campo de lectura QR con borde naranja y botón F2 integrado
        self.caja_lectura = QFrame()
        self.caja_lectura.setObjectName("cajaLecturaQR")
        self.caja_lectura.setProperty("habilitado", "false")
        _refrescar_estilo(self.caja_lectura)

        layout_lectura = QHBoxLayout(self.caja_lectura)
        layout_lectura.setContentsMargins(16, 8, 12, 8)
        layout_lectura.setSpacing(12)

        lbl_icono_qr = QLabel("⛶")
        lbl_icono_qr.setStyleSheet(
            "color: #243314; font-size: 22px; font-weight: 700;"
        )
        layout_lectura.addWidget(lbl_icono_qr)

        self.input_codigo = QLineEdit()
        self.input_codigo.setObjectName("inputLecturaQR")
        self.input_codigo.setPlaceholderText("Seleccione un servicio para escanear...")
        self.input_codigo.setEnabled(False)  # Inicia bloqueado sin servicio (RF-ES33)
        self.input_codigo.returnPressed.connect(self.procesar_codigo)
        layout_lectura.addWidget(self.input_codigo, 1)

        self.btn_manual = QPushButton("Canje manual  F2")
        self.btn_manual.setObjectName("btnAtajoManual")
        self.btn_manual.setCursor(Qt.PointingHandCursor)
        self.btn_manual.setEnabled(False)
        self.btn_manual.clicked.connect(self.abrir_canje_manual)
        layout_lectura.addWidget(self.btn_manual)

        main_layout.addWidget(self.caja_lectura)

        # 4. Tarjeta de resultado principal
        self.tarjeta = TarjetaResultado()
        main_layout.addWidget(self.tarjeta, 1)

        # 5. Pie informativo (indicador de sonido apagado RNF-ES11 / RF-ES20)
        pie_layout = QHBoxLayout()
        self.lbl_sonido = QLabel("🔇 Sonido apagado · Limpieza automática en 4 s")
        self.lbl_sonido.setObjectName("lblSonidoEstado")
        pie_layout.addWidget(self.lbl_sonido)
        pie_layout.addStretch()
        main_layout.addLayout(pie_layout)

        # Forzar el foco constante en el campo de texto (RF-ES20)
        self.timer_foco = QTimer(self)
        self.timer_foco.setInterval(500)
        self.timer_foco.timeout.connect(self.verificar_foco)
        self.timer_foco.start()

    def registrar_atajos(self):
        """Configura los atajos globales (F5, F6, F7 para servicio y F2 para canje manual)."""
        self.shortcut_f5 = QShortcut(QKeySequence(Qt.Key_F5), self)
        self.shortcut_f5.setContext(Qt.WindowShortcut)
        self.shortcut_f5.activated.connect(lambda: self.seleccionar_servicio("Desayuno"))

        self.shortcut_f6 = QShortcut(QKeySequence(Qt.Key_F6), self)
        self.shortcut_f6.setContext(Qt.WindowShortcut)
        self.shortcut_f6.activated.connect(lambda: self.seleccionar_servicio("Almuerzo"))

        self.shortcut_f7 = QShortcut(QKeySequence(Qt.Key_F7), self)
        self.shortcut_f7.setContext(Qt.WindowShortcut)
        self.shortcut_f7.activated.connect(
            lambda: self.seleccionar_servicio("Refrigerio")
        )

        self.shortcut_f2 = QShortcut(QKeySequence(Qt.Key_F2), self)
        self.shortcut_f2.setContext(Qt.WindowShortcut)
        self.shortcut_f2.activated.connect(self.abrir_canje_manual)

    def seleccionar_servicio(self, servicio: str):
        self.servicio_actual = servicio
        self.lbl_aviso_servicio.setText(f"✓ Servicio activo: {servicio.upper()}")
        self.lbl_aviso_servicio.setProperty("activo", "true")
        _refrescar_estilo(self.lbl_aviso_servicio)

        self.caja_lectura.setProperty("habilitado", "true")
        _refrescar_estilo(self.caja_lectura)

        self.input_codigo.setEnabled(True)
        self.input_codigo.setPlaceholderText("Escanee el código QR del aprendiz...")
        self.btn_manual.setEnabled(True)
        self.input_codigo.setFocus()

        self.btn_desayuno.setChecked(servicio == "Desayuno")
        self.btn_almuerzo.setChecked(servicio == "Almuerzo")
        self.btn_refrigerio.setChecked(servicio == "Refrigerio")

    def procesar_codigo(self):
        """Lee el contenido del QR, valida localmente y envía a la API en segundo plano."""
        if not self.servicio_actual or self._procesando:
            return

        texto = self.input_codigo.text().strip()
        self.input_codigo.clear()
        if not texto:
            return

        self.timer_limpieza.stop()

        # Validación rápida antes de lanzar hilo: si no son 1 a 10 dígitos, no va a la API
        es_valido, _ = self.canje_service.validar_contenido_qr(texto)
        if not es_valido:
            self.tarjeta.mostrar_resultado("no_reconocido")
            self.timer_limpieza.start(4000)
            return

        self._procesando = True
        ejecutar_en_segundo_plano(
            self.canje_service.registrar_canje_qr,
            self.servicio_actual,
            texto,
            al_exito=self._al_completar_canje,
            al_error=self._al_fallar_canje,
        )

    def abrir_canje_manual(self):
        """Abre el modal de canje manual con F2 (RF-ES21) y devuelve el foco al cerrar."""
        if not self.servicio_actual or self._procesando or self._dialogo_abierto:
            return

        self._dialogo_abierto = True
        dialogo = DialogoCanjeManual(self.servicio_actual, self)
        aceptado = dialogo.exec()
        self._dialogo_abierto = False

        # Al cerrar, el foco vuelve inmediatamente al campo de lectura
        self.input_codigo.setFocus()

        if aceptado == QDialog.Accepted:
            documento, motivo = dialogo.obtener_datos()
            self.timer_limpieza.stop()
            self._procesando = True
            ejecutar_en_segundo_plano(
                self.canje_service.registrar_canje_manual,
                self.servicio_actual,
                documento,
                motivo,
                al_exito=self._al_completar_canje,
                al_error=self._al_fallar_canje,
            )

    def _al_completar_canje(self, resultado: ResultadoCanje):
        self._procesando = False
        self.tarjeta.mostrar_resultado(resultado.tipo, resultado.datos)
        self.timer_limpieza.start(4000)
        self.input_codigo.setFocus()

    def _al_fallar_canje(self, excepcion: Exception):
        self._procesando = False
        self.tarjeta.mostrar_resultado(
            "error_conexion",
            {"mensaje": f"Error inesperado al registrar canje: {excepcion}"},
        )
        self.timer_limpieza.start(4000)
        self.input_codigo.setFocus()

    def limpiar_tarjeta_auto(self):
        self.tarjeta.limpiar()

    def verificar_foco(self):
        if (
            self.isVisible()
            and self.servicio_actual
            and not self._dialogo_abierto
            and not self.input_codigo.hasFocus()
        ):
            self.input_codigo.setFocus()