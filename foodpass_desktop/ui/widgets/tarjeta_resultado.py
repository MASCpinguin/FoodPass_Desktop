from PySide6.QtGui import QFont
from PySide6.QtWidgets import QFrame, QHBoxLayout, QLabel, QVBoxLayout


class TarjetaResultado(QFrame):

  def __init__(self, parent=None):
    super().__init__(parent)
    self.setFrameShape(QFrame.StyledPanel)
    self.setup_ui()
    self.limpiar()

  def setup_ui(self):
    layout = QVBoxLayout(self)
    layout.setContentsMargins(16, 16, 16, 16)

    # Cabecera con indicador de sonido
    header_layout = QHBoxLayout()
    self.lbl_estado_icono = QLabel()
    self.lbl_estado_titulo = QLabel("Esperando lectura...")
    self.lbl_estado_titulo.setFont(QFont("Segoe UI", 14, QFont.Bold))

    header_layout.addWidget(self.lbl_estado_icono)
    header_layout.addWidget(self.lbl_estado_titulo)
    header_layout.addStretch()

    self.lbl_sonido = QLabel("🔇 Sonido apagado")
    self.lbl_sonido.setStyleSheet("color: #718096; font-size: 12px;")
    header_layout.addWidget(self.lbl_sonido)

    layout.addLayout(header_layout)

    # Información principal (Nombre legible a 2 m >= 32 px)
    self.lbl_nombre = QLabel("")
    font_nombre = QFont("Segoe UI", 32, QFont.Bold)
    self.lbl_nombre.setFont(font_nombre)
    self.lbl_nombre.setWordWrap(True)
    layout.addWidget(self.lbl_nombre)

    # Detalles adicionales (Documento, programa, hora, etc.)
    self.lbl_detalles = QLabel("")
    self.lbl_detalles.setFont(QFont("Segoe UI", 16))
    self.lbl_detalles.setWordWrap(True)
    layout.addWidget(self.lbl_detalles)

    layout.addStretch()

  def mostrar_resultado(self, tipo, datos=None):
    """Muestra el resultado según el estado: 'entregado', 'ya_recibio', 'no_beneficiario', o 'no_reconocido'."""
    if tipo == "entregado":
      self.setStyleSheet(
          "background-color: #F0FDF4; border: 2px solid #22C55E; border-radius:"
          " 8px;"
      )
      self.lbl_estado_icono.setText("✅")
      self.lbl_estado_titulosetText = "BENEFICIARIO ATENDIDO"
      self.lbl_estado_titulo.setStyleSheet("color: #166534;")

      nombre = datos.get("nombre", "Nombre Apellido")
      doc = datos.get("documento", "00000000")
      programa = datos.get("programa", "Programa")

      self.lbl_nombre.setText(nombre)
      self.lbl_nombre.setStyleSheet("color: #14532D;")
      self.lbl_detalles.setText(f"Documento: {doc} | Programa: {programa}")
      self.lbl_detalles.setStyleSheet("color: #166534;")

    elif tipo == "ya_recibio":
      self.setStyleSheet(
          "background-color: #FEF2F2; border: 2px solid #EF4444; border-radius:"
          " 8px;"
      )
      self.lbl_estado_icono.setText("⚠️")
      self.lbl_estado_titulo.setText("YA RECIBIÓ HOY")
      self.lbl_estado_titulo.setStyleSheet("color: #991B1B;")

      servicio = datos.get("servicio", "Servicio")
      hora = datos.get("hora", "00:00")
      nombre = datos.get("nombre", "Aprendiz")

      self.lbl_nombre.setText(nombre)
      self.lbl_nombre.setStyleSheet("color: #7F1D1D;")
      self.lbl_detalles.setText(f"Ya reclamó {servicio} hoy a las {hora}.")
      self.lbl_detalles.setStyleSheet("color: #991B1B;")

    elif tipo == "no_beneficiario":
      self.setStyleSheet(
          "background-color: #FEF2F2; border: 2px solid #EF4444; border-radius:"
          " 8px;"
      )
      self.lbl_estado_icono.setText("❌")
      self.lbl_estado_titulo.setText("NO ES BENEFICIARIO")
      self.lbl_estado_titulo.setStyleSheet("color: #991B1B;")

      self.lbl_nombre.setText("Acceso Denegado")
      self.lbl_nombre.setStyleSheet("color: #7F1D1D;")
      self.lbl_detalles.setText(
          "El documento o código no se encuentra en la base activa."
      )
      self.lbl_detalles.setStyleSheet("color: #991B1B;")

    elif tipo == "no_reconocido":
      self.setStyleSheet(
          "background-color: #FFFBEB; border: 2px solid #F59E0B; border-radius:"
          " 8px;"
      )
      self.lbl_estado_icono.setText("⚡")
      self.lbl_estado_titulo.setText("ERROR DE LECTURA")
      self.lbl_estado_titulo.setStyleSheet("color: #92400E;")

      self.lbl_nombre.setText("CÓDIGO NO RECONOCIDO")
      self.lbl_nombre.setStyleSheet("color: #78350F;")
      self.lbl_detalles.setText(
          "El formato ingresado no es válido (solo dígitos de 1 a 10)."
      )
      self.lbl_detalles.setStyleSheet("color: #92400E;")

  def limpiar(self):
    self.setStyleSheet(
        "background-color: #F8FAFC; border: 1px solid #CBD5E1; border-radius:"
        " 8px;"
    )
    self.lbl_estado_icono.setText("ℹ️")
    self.lbl_estado_titulo.setText("ESTADO DE ATENCIÓN")
    self.lbl_estado_titulo.setStyleSheet("color: #475569;")
    self.lbl_nombre.setText("Listo para escanear")
    self.lbl_nombre.setStyleSheet("color: #94A3B8;")
    self.lbl_detalles.setText("Acerque el carné o digite el código.")
    self.lbl_detalles.setStyleSheet("color: #64748B;")
