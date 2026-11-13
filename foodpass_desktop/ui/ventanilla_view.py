from PySide6.QtCore import Qt, QTimer
from PySide6.QtGui import QKeySequence, QShortcut
from PySide6.QtWidgets import (
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QPushButton,
    QVBoxLayout,
    QWidget,
)
from foodpass_desktop.ui.widgets.tarjeta_resultado import TarjetaResultado


class VentanillaView(QWidget):

  def __init__(self, parent=None):
    super().__init__(parent)
    self.servicio_actual = None

    # Timer para limpiar la tarjeta automáticamente a los 4 segundos
    self.timer_limpieza = QTimer(self)
    self.timer_limpieza.setSingleShot(True)
    self.timer_limpieza.timeout.connect(self.limpiar_tarjeta_auto)

    self.setup_ui()
    self.registrar_atajos()

  def setup_ui(self):
    main_layout = QVBoxLayout(self)

    # Selector de servicio
    layout_servicios = QHBoxLayout()
    self.btn_desayuno = QPushButton("Desayuno [F5]")
    self.btn_almuerzo = QPushButton("Almuerzo [F6]")
    self.btn_refrigerio = QPushButton("Refrigerio [F7]")

    for btn in [self.btn_desayuno, self.btn_almuerzo, self.btn_refrigerio]:
      btn.setCheckable(True)
      btn.setMinimumHeight(50)
      layout_servicios.addWidget(btn)

    self.btn_desayuno.clicked.connect(lambda: self.seleccionar_servicio("Desayuno"))
    self.btn_almuerzo.clicked.connect(lambda: self.seleccionar_servicio("Almuerzo"))
    self.btn_refrigerio.clicked.connect(
        lambda: self.seleccionar_servicio("Refrigerio")
    )

    main_layout.addLayout(layout_servicios)

    # Estado de selección / Campo de lectura
    self.lbl_aviso_servicio = QLabel("⚠️ Elige un servicio para comenzar")
    self.lbl_aviso_servicio.setStyleSheet(
        "color: #DC2626; font-weight: bold; font-size: 14px;"
    )
    main_layout.addWidget(self.lbl_aviso_servicio)

    self.input_codigo = QLineEdit()
    self.input_codigo.setPlaceholderText(
        "Esperando código de barras / QR..."
    )
    self.input_codigo.setEnabled(False)  # Inicia bloqueado sin servicio
    self.input_codigo.returnPressed.connect(self.procesar_codigo)
    main_layout.addWidget(self.input_codigo)

    # Tarjeta de resultado
    self.tarjeta = TarjetaResultado()
    main_layout.addWidget(self.tarjeta)

    # Forzar el foco constante en el campo de texto
    self.timer_foco = QTimer(self)
    self.timer_foco.setInterval(500)
    self.timer_foco.timeout.connect(self.verificar_foco)
    self.timer_foco.start()

  def registrar_atajos(self):
    """Configura los atajos de teclado globales (F5, F6, F7) para cambiar de servicio."""
    self.shortcut_f5 = QShortcut(QKeySequence(Qt.Key_F5), self)
    self.shortcut_f5.setContext(Qt.WidgetWithChildrenShortcut)
    self.shortcut_f5.activated.connect(lambda: self.seleccionar_servicio("Desayuno"))

    self.shortcut_f6 = QShortcut(QKeySequence(Qt.Key_F6), self)
    self.shortcut_f6.setContext(Qt.WidgetWithChildrenShortcut)
    self.shortcut_f6.activated.connect(lambda: self.seleccionar_servicio("Almuerzo"))

    self.shortcut_f7 = QShortcut(QKeySequence(Qt.Key_F7), self)
    self.shortcut_f7.setContext(Qt.WidgetWithChildrenShortcut)
    self.shortcut_f7.activated.connect(
        lambda: self.seleccionar_servicio("Refrigerio")
    )

  def seleccionar_servicio(self, servicio):
    self.servicio_actual = servicio
    self.lbl_aviso_servicio.setText(f"Servicio activo: {servicio.upper()}")
    self.lbl_aviso_servicio.setStyleSheet(
        "color: #16A34A; font-weight: bold; font-size: 14px;"
    )
    self.input_codigo.setEnabled(True)
    self.input_codigo.setFocus()

    # Actualizar estados visuales de los botones
    self.btn_desayuno.setChecked(servicio == "Desayuno")
    self.btn_almuerzo.setChecked(servicio == "Almuerzo")
    self.btn_refrigerio.setChecked(servicio == "Refrigerio")

  def procesar_codigo(self):
    if not self.servicio_actual:
      return

    texto = self.input_codigo.text().strip()
    self.input_codigo.clear()

    # Reiniciar temporizador si ya estaba corriendo
    self.timer_limpieza.stop()

    # Validar que sean solo dígitos (1 a 10 caracteres)
    if not texto.isdigit() or not (1 <= len(texto) <= 10):
      self.tarjeta.mostrar_resultado("no_reconocido")
    else:
      # Datos simulados de prueba para los tres estados (se reemplazará en T10 con la API)
      if texto == "1111":
        self.tarjeta.mostrar_resultado(
            "entregado", {
                "nombre": "Ana María Gómez",
                "documento": "1098765432",
                "programa": "ADSO 3173467",
            }
        )
      elif texto == "2222":
        self.tarjeta.mostrar_resultado(
            "ya_recibio", {
                "nombre": "Carlos Pérez",
                "servicio": self.servicio_actual,
                "hora": "12:30 PM",
            }
        )
      else:
        self.tarjeta.mostrar_resultado("no_beneficiario")

    # Activar la limpieza automática a los 4 segundos
    self.timer_limpieza.start(4000)

  def limpiar_tarjeta_auto(self):
    self.tarjeta.limpiar()

  def verificar_foco(self):
    if self.isVisible() and self.servicio_actual and not self.input_codigo.hasFocus():
      self.input_codigo.setFocus()