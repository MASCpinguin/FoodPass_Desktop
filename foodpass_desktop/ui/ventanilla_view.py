"""Pantalla 3 · Ventanilla (Estación 1 · Verificación Alimentaria Social).

RF-ES33 (servicio con F5/F6/F7), RF-ES17 (canje por código), RF-ES20 (foco
permanente y resultado legible), RF-ES21 (canje manual con F2), RF-ES34
(anular en 2 min) y RF-ES24 (reporte de entregas).
"""

from datetime import datetime

from PySide6.QtCore import QRegularExpression, Qt, QTimer, Signal
from PySide6.QtGui import QKeySequence, QRegularExpressionValidator, QShortcut
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
from foodpass_desktop.core.config import raciones_previstas
from foodpass_desktop.services.canje_service import (
    MOTIVOS_CANJE_MANUAL,
    CanjeService,
    ResultadoCanje,
)
from foodpass_desktop.ui.widgets import (
    Badge,
    BotonDestructivo,
    BotonNeutro,
    BotonPrincipal,
    BotonSecundario,
    TarjetaMetrica,
    etiqueta,
    refrescar_estilo,
)
from foodpass_desktop.ui.widgets.tarjeta_resultado import TarjetaResultado

MOTIVOS_ANULACION = (
    "La persona no corresponde",
    "Suplantación (código de otra persona)",
    "Servicio equivocado",
)
SEGUNDOS_ANULACION = 120
MAX_LECTURAS = 6
_ESCALA_HORA = "%I:%M %p"


class DialogoCanjeManual(QDialog):
    """Barra de contingencia por documento (F2 · RF-ES21)."""

    def __init__(self, servicio: str, parent=None):
        super().__init__(parent)
        self.servicio = servicio
        self.setObjectName("dialogoCanjeManual")
        self.setWindowTitle("Canje manual por documento")
        self.setModal(True)
        self.setFixedWidth(460)
        caja = QVBoxLayout(self)
        caja.setContentsMargins(28, 28, 28, 28)
        caja.setSpacing(12)
        caja.addWidget(etiqueta("Canje manual", "tituloDialogoManual"))
        caja.addWidget(
            etiqueta(
                f"Servicio: {servicio}. Busca al aprendiz por su número de documento.",
                "textoSecundario",
            )
        )
        caja.addWidget(etiqueta("Número de documento", "etiquetaCampoManual"))
        self.input_documento = QLineEdit()
        self.input_documento.setObjectName("inputDocumentoManual")
        self.input_documento.setPlaceholderText("Ej. 1001001100")
        self.input_documento.setMaxLength(15)
        self.input_documento.setValidator(
            QRegularExpressionValidator(QRegularExpression(r"\d{0,15}"), self)
        )
        self.input_documento.returnPressed.connect(self.intentar_confirmar)
        caja.addWidget(self.input_documento)
        caja.addWidget(etiqueta("Motivo", "etiquetaCampoManual"))
        self.combo_motivo = QComboBox()
        self.combo_motivo.setObjectName("comboMotivoManual")
        self.combo_motivo.addItems(MOTIVOS_CANJE_MANUAL)
        caja.addWidget(self.combo_motivo)
        self.lbl_error = etiqueta("", "errorDialogo")
        self.lbl_error.setVisible(False)
        caja.addWidget(self.lbl_error)
        fila = QHBoxLayout()
        fila.addStretch()
        self.btn_cancelar = BotonNeutro("Cancelar (Esc)")
        self.btn_cancelar.setObjectName("btnCancelarManual")
        self.btn_cancelar.clicked.connect(self.reject)
        self.btn_confirmar = BotonPrincipal("Registrar (Enter)")
        self.btn_confirmar.setObjectName("btnConfirmarManual")
        self.btn_confirmar.clicked.connect(self.intentar_confirmar)
        fila.addWidget(self.btn_cancelar)
        fila.addWidget(self.btn_confirmar)
        caja.addLayout(fila)
        self.input_documento.setFocus()

    def intentar_confirmar(self):
        doc = self.input_documento.text().strip()
        if not doc.isdigit() or len(doc) < 5:
            self.lbl_error.setText("Escribe un documento válido (mínimo 5 dígitos).")
            self.lbl_error.setVisible(True)
            self.input_documento.setFocus()
            return
        self.accept()

    def obtener_datos(self) -> tuple[str, str]:
        return self.input_documento.text().strip(), self.combo_motivo.currentText()


class DialogoAnular(QDialog):
    """Confirmación de anulación con motivo (RF-ES34 · acción irreversible)."""

    def __init__(self, nombre, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Anular canje")
        self.setModal(True)
        self.setFixedWidth(460)
        caja = QVBoxLayout(self)
        caja.setContentsMargins(28, 28, 28, 28)
        caja.setSpacing(12)
        caja.addWidget(etiqueta("Anular canje", "tituloDialogo"))
        caja.addWidget(
            etiqueta(
                f"Vas a anular la entrega de {nombre}. El día queda libre para el aprendiz verdadero.",
                "textoSecundario",
            )
        )
        caja.addWidget(etiqueta("Motivo", "etiquetaCampo"))
        self.combo = QComboBox()
        self.combo.addItems(MOTIVOS_ANULACION)
        caja.addWidget(self.combo)
        fila = QHBoxLayout()
        fila.addStretch()
        cancelar = BotonNeutro("Cancelar")
        cancelar.clicked.connect(self.reject)
        anular = BotonDestructivo("Anular canje")
        anular.clicked.connect(self.accept)
        fila.addWidget(cancelar)
        fila.addWidget(anular)
        caja.addLayout(fila)


class VentanillaView(QWidget):
    """Pantalla 3 · Ventanilla."""

    canje_registrado = Signal()
    abrir_reporte = Signal()

    def __init__(self, parent=None, servicio_canje: CanjeService | None = None):
        super().__init__(parent)
        self.setObjectName("vistaVentanilla")
        self.servicio_actual = None
        self._procesando = False
        self._dialogo_abierto = False
        self._ultimo_canje = None  # {"canje_id", "registrado_en", "nombre"}
        self._lecturas = []
        self._contador = {"Desayuno": 0, "Almuerzo": 0, "Refrigerio": 0}
        self.canje_service = servicio_canje or CanjeService()

        self.timer_limpieza = QTimer(self)
        self.timer_limpieza.setSingleShot(True)
        self.timer_limpieza.timeout.connect(self.limpiar_tarjeta_auto)
        self.timer_anular = QTimer(self)
        self.timer_anular.setSingleShot(True)
        self.timer_anular.timeout.connect(self._vencer_anulacion)

        self.setup_ui()
        self.registrar_atajos()

    # --- construcción ------------------------------------------------------
    def setup_ui(self):
        raiz = QVBoxLayout(self)
        raiz.setContentsMargins(36, 30, 36, 24)
        raiz.setSpacing(16)

        encabezado = QHBoxLayout()
        col = QVBoxLayout()
        col.setSpacing(4)
        col.addWidget(etiqueta("Ventanilla", "tituloVentanilla", False))
        col.addWidget(
            etiqueta(
                "Elige el servicio y escanea el código FoodPass. No hace falta confirmar.",
                "subtituloVentanilla",
            )
        )
        encabezado.addLayout(col, 1)
        pildoras = QFrame()
        pildoras.setObjectName("contenedorPildoraServicios")
        fila_p = QHBoxLayout(pildoras)
        fila_p.setContentsMargins(4, 4, 4, 4)
        fila_p.setSpacing(4)
        self.btn_desayuno = QPushButton("Desayuno  F5")
        self.btn_almuerzo = QPushButton("Almuerzo  F6")
        self.btn_refrigerio = QPushButton("Refrigerio  F7")
        for btn, servicio in (
            (self.btn_desayuno, "Desayuno"),
            (self.btn_almuerzo, "Almuerzo"),
            (self.btn_refrigerio, "Refrigerio"),
        ):
            btn.setObjectName("btnServicioPildora")
            btn.setCheckable(True)
            btn.setCursor(Qt.CursorShape.PointingHandCursor)
            btn.clicked.connect(
                lambda _c=False, s=servicio: self.seleccionar_servicio(s)
            )
            fila_p.addWidget(btn)
        encabezado.addWidget(pildoras, 0, Qt.AlignmentFlag.AlignVCenter)
        raiz.addLayout(encabezado)

        self.lbl_aviso_servicio = etiqueta(
            "Elige el servicio (F5 desayuno · F6 almuerzo · F7 refrigerio) para empezar a escanear.",
            "avisoServicio",
        )
        self.lbl_aviso_servicio.setProperty("activo", "false")
        raiz.addWidget(self.lbl_aviso_servicio)

        self.caja_lectura = QFrame()
        self.caja_lectura.setObjectName("cajaLecturaQR")
        self.caja_lectura.setProperty("habilitado", "false")
        fila_l = QHBoxLayout(self.caja_lectura)
        fila_l.setContentsMargins(16, 4, 8, 4)
        fila_l.setSpacing(12)
        fila_l.addWidget(etiqueta("⛶", "iconoLectura", False))
        self.input_codigo = QLineEdit()
        self.input_codigo.setObjectName("inputLecturaQR")
        self.input_codigo.setPlaceholderText("Elige un servicio para escanear")
        self.input_codigo.setEnabled(False)
        self.input_codigo.returnPressed.connect(self.procesar_codigo)
        fila_l.addWidget(self.input_codigo, 1)
        self.btn_manual = QPushButton("Canje manual  F2")
        self.btn_manual.setObjectName("btnAtajoManual")
        self.btn_manual.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_manual.setEnabled(False)
        self.btn_manual.clicked.connect(self.abrir_canje_manual)
        fila_l.addWidget(self.btn_manual)
        raiz.addWidget(self.caja_lectura)

        cuerpo = QHBoxLayout()
        cuerpo.setSpacing(20)
        izquierda = QVBoxLayout()
        izquierda.setSpacing(12)
        self.tarjeta = TarjetaResultado()
        izquierda.addWidget(self.tarjeta, 1)
        acciones = QHBoxLayout()
        self.btn_anular = BotonDestructivo("Anular (no corresponde)")
        self.btn_anular.setVisible(False)
        self.btn_anular.clicked.connect(self.anular_ultimo)
        acciones.addWidget(self.btn_anular)
        acciones.addStretch()
        self.btn_reporte = BotonSecundario("Reporte de entregas")
        self.btn_reporte.clicked.connect(self.abrir_reporte.emit)
        acciones.addWidget(self.btn_reporte)
        izquierda.addLayout(acciones)
        cuerpo.addLayout(izquierda, 3)

        derecha = QVBoxLayout()
        derecha.setSpacing(12)
        self.metrica = TarjetaMetrica("Entregas del servicio", con_barra=True)
        derecha.addWidget(self.metrica)
        panel = QFrame()
        panel.setObjectName("panelLecturas")
        caja_p = QVBoxLayout(panel)
        caja_p.setContentsMargins(18, 16, 18, 16)
        caja_p.setSpacing(8)
        caja_p.addWidget(etiqueta("Últimas lecturas", "tituloSeccion", False))
        self.caja_lecturas = QVBoxLayout()
        self.caja_lecturas.setSpacing(6)
        caja_p.addLayout(self.caja_lecturas)
        self.lbl_sin_lecturas = etiqueta("Aún no hay lecturas.", "textoSecundario")
        caja_p.addWidget(self.lbl_sin_lecturas)
        caja_p.addStretch()
        derecha.addWidget(panel, 1)
        cuerpo.addLayout(derecha, 2)
        raiz.addLayout(cuerpo, 1)

        self.timer_foco = QTimer(self)
        self.timer_foco.setInterval(500)
        self.timer_foco.timeout.connect(self.verificar_foco)
        self.timer_foco.start()
        self._actualizar_metrica()

    def registrar_atajos(self):
        for tecla, accion in (
            (Qt.Key.Key_F5, lambda: self.seleccionar_servicio("Desayuno")),
            (Qt.Key.Key_F6, lambda: self.seleccionar_servicio("Almuerzo")),
            (Qt.Key.Key_F7, lambda: self.seleccionar_servicio("Refrigerio")),
            (Qt.Key.Key_F2, self.abrir_canje_manual),
        ):
            atajo = QShortcut(QKeySequence(tecla), self)
            atajo.setContext(Qt.ShortcutContext.WindowShortcut)
            atajo.activated.connect(accion)

    # --- servicio -----------------------------------------------------------
    def seleccionar_servicio(self, servicio: str):
        self.servicio_actual = servicio
        self.lbl_aviso_servicio.setText(f"Servicio activo: {servicio.upper()}")
        self.lbl_aviso_servicio.setProperty("activo", "true")
        refrescar_estilo(self.lbl_aviso_servicio)
        self.caja_lectura.setProperty("habilitado", "true")
        refrescar_estilo(self.caja_lectura)
        self.input_codigo.setEnabled(True)
        self.input_codigo.setPlaceholderText("Escanea o digita el código FoodPass")
        self.btn_manual.setEnabled(True)
        self.input_codigo.setFocus()
        self.btn_desayuno.setChecked(servicio == "Desayuno")
        self.btn_almuerzo.setChecked(servicio == "Almuerzo")
        self.btn_refrigerio.setChecked(servicio == "Refrigerio")
        self._actualizar_metrica()

    def fijar_conteo_del_dia(self, por_servicio: dict):
        """Lo llama la ventana principal con el resumen del día (desde la base)."""
        for s in self._contador:
            self._contador[s] = int(por_servicio.get(s.lower(), self._contador[s]))
        self._actualizar_metrica()

    def _actualizar_metrica(self):
        if not self.servicio_actual:
            self.metrica.lbl_etiqueta.setText("Entregas del servicio")
            self.metrica.fijar("—", "Elige un servicio para ver su avance.", 0)
            return
        previstas = raciones_previstas()[self.servicio_actual.lower()]
        hechas = self._contador[self.servicio_actual]
        self.metrica.lbl_etiqueta.setText(f"{self.servicio_actual} · entregas de hoy")
        self.metrica.fijar(
            hechas, f"de {previstas} previstas", hechas * 100 / max(previstas, 1)
        )

    # --- canje --------------------------------------------------------------
    def procesar_codigo(self):
        if not self.servicio_actual or self._procesando:
            return
        texto = self.input_codigo.text().strip()
        self.input_codigo.clear()
        if not texto:
            return
        self.timer_limpieza.stop()
        if not self.canje_service.es_codigo_valido(texto):
            self.tarjeta.mostrar_resultado(
                "no_reconocido", {"mensaje": "No es un código de FoodPass."}
            )
            self._agregar_lectura("Código no reconocido", "error", "No válido")
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
        if not self.servicio_actual or self._procesando or self._dialogo_abierto:
            return
        self._dialogo_abierto = True
        dialogo = DialogoCanjeManual(self.servicio_actual, self)
        aceptado = dialogo.exec()
        self._dialogo_abierto = False
        self.input_codigo.setFocus()
        if aceptado == QDialog.DialogCode.Accepted:
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
        datos = resultado.datos or {}
        self.tarjeta.mostrar_resultado(resultado.tipo, datos)
        nombre = datos.get("nombre") or "—"
        if resultado.tipo == "entregado":
            self._contador[self.servicio_actual] = (
                self._contador.get(self.servicio_actual, 0) + 1
            )
            self._actualizar_metrica()
            self._agregar_lectura(nombre, "canjeado", datos.get("servicio", "Canjeado"))
            if datos.get("canje_id"):
                self._ultimo_canje = {
                    "canje_id": datos["canje_id"],
                    "registrado_en": datos.get("registrado_en") or datetime.now(),
                    "nombre": nombre,
                    "servicio": self.servicio_actual,
                }
                self.btn_anular.setVisible(True)
                self.timer_anular.start(SEGUNDOS_ANULACION * 1000)
            self.canje_registrado.emit()
        elif resultado.tipo == "ya_recibio":
            self._agregar_lectura(nombre, "ya_recibio", "Ya recibió")
        elif resultado.tipo == "error_conexion":
            self._agregar_lectura("Sin conexión", "error", "Sin conexión")
        else:
            self._agregar_lectura(
                nombre if nombre != "—" else "Rechazado", "error", "Rechazado"
            )
        self.timer_limpieza.start(4000)
        self.input_codigo.setFocus()

    def _al_fallar_canje(self, excepcion: Exception):
        self._procesando = False
        self.tarjeta.mostrar_resultado(
            "error_conexion",
            {
                "mensaje": "No se pudo registrar la entrega. Inténtalo de nuevo o avisa a soporte técnico."
            },
        )
        self.timer_limpieza.start(4000)
        self.input_codigo.setFocus()

    # --- anulación (RF-ES34) --------------------------------------------------
    def anular_ultimo(self):
        canje = self._ultimo_canje
        if not canje:
            return
        self._dialogo_abierto = True
        dialogo = DialogoAnular(canje["nombre"], self)
        aceptado = dialogo.exec() == QDialog.DialogCode.Accepted
        self._dialogo_abierto = False
        self.input_codigo.setFocus()
        if not aceptado:
            return
        ejecutar_en_segundo_plano(
            self.canje_service.anular,
            canje["canje_id"],
            canje["registrado_en"],
            al_exito=self._anulacion_terminada,
            al_error=self._al_fallar_canje,
        )

    def _anulacion_terminada(self, resultado):
        ok, mensaje = resultado
        canje = self._ultimo_canje or {}
        if ok:
            servicio = canje.get("servicio")
            if servicio:
                self._contador[servicio] = max(0, self._contador[servicio] - 1)
                self._actualizar_metrica()
            self.tarjeta.mostrar_resultado(
                "anulado", {"nombre": canje.get("nombre"), "mensaje": mensaje}
            )
            self._agregar_lectura(canje.get("nombre", "—"), "neutro", "Anulado")
            self.canje_registrado.emit()
        else:
            self.tarjeta.mostrar_resultado("no_reconocido", {"mensaje": mensaje})
        self._vencer_anulacion()
        self.timer_limpieza.start(4000)

    def _vencer_anulacion(self):
        self._ultimo_canje = None
        self.btn_anular.setVisible(False)
        self.timer_anular.stop()

    # --- últimas lecturas -----------------------------------------------------
    def _agregar_lectura(self, nombre, tipo, texto_badge):
        hora = datetime.now().strftime(_ESCALA_HORA)
        self._lecturas.insert(0, (hora, nombre, tipo, texto_badge))
        del self._lecturas[MAX_LECTURAS:]
        while self.caja_lecturas.count():
            item = self.caja_lecturas.takeAt(0)
            fila = item.layout()
            if fila is not None:
                while fila.count():
                    w = fila.takeAt(0).widget()
                    if w:
                        w.deleteLater()
        for hora, nombre, tipo, badge in self._lecturas:
            fila = QHBoxLayout()
            fila.setSpacing(8)
            lbl = QLabel(f"{hora}  ·  {nombre}")
            lbl.setObjectName("filaLectura")
            fila.addWidget(lbl, 1)
            fila.addWidget(Badge(badge, tipo))
            self.caja_lecturas.addLayout(fila)
        self.lbl_sin_lecturas.setVisible(not self._lecturas)

    # --- foco ---------------------------------------------------------------------
    def limpiar_tarjeta_auto(self):
        self.tarjeta.limpiar()

    def verificar_foco(self):
        if (
            self.isVisible()
            and self.servicio_actual
            and not self._dialogo_abierto
            and not self.input_codigo.hasFocus()
            and self.window().isActiveWindow()
        ):
            self.input_codigo.setFocus()
