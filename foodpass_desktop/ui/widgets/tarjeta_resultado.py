"""Widget de Tarjeta de Resultado para la Ventanilla de Priorización (Manual v2.1)."""

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QFrame,
    QHBoxLayout,
    QLabel,
    QVBoxLayout,
)


def _refrescar_estilo(widget):
    """Fuerza a Qt a reaplicar selectores QSS basados en propiedades dinámicas."""
    widget.style().unpolish(widget)
    widget.style().polish(widget)
    widget.update()


class TarjetaResultado(QFrame):
    """Muestra el resultado de verificación con color, icono, texto y recuadro de foto."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("tarjetaResultado")
        self.setup_ui()
        self.limpiar()

    def setup_ui(self):
        layout_raiz = QHBoxLayout(self)
        layout_raiz.setContentsMargins(28, 28, 28, 28)
        layout_raiz.setSpacing(28)

        # Recuadro de foto / "Sin foto" (Manual v2.1 Pantalla 3)
        self.recuadro_foto = QFrame()
        self.recuadro_foto.setObjectName("recuadroFoto")
        self.recuadro_foto.setFixedSize(160, 180)
        layout_foto = QVBoxLayout(self.recuadro_foto)
        layout_foto.setAlignment(Qt.AlignCenter)

        self.lbl_foto = QLabel("Sin foto")
        self.lbl_foto.setObjectName("lblSinFoto")
        self.lbl_foto.setAlignment(Qt.AlignCenter)
        layout_foto.addWidget(self.lbl_foto)

        layout_raiz.addWidget(self.recuadro_foto, 0, Qt.AlignVCenter)

        # Columna derecha con estado, nombre (40 px), documento y detalles
        col_info = QVBoxLayout()
        col_info.setSpacing(10)
        col_info.addStretch()

        header_layout = QHBoxLayout()
        header_layout.setSpacing(8)
        self.lbl_estado_icono = QLabel("ℹ️")
        self.lbl_estado_titulo = QLabel("ESTADO DE ATENCIÓN")
        self.lbl_estado_titulo.setObjectName("lblEstadoTitulo")

        header_layout.addWidget(self.lbl_estado_icono)
        header_layout.addWidget(self.lbl_estado_titulo)
        header_layout.addStretch()
        col_info.addLayout(header_layout)

        # Nombre del aprendiz (40 px, peso 800, legible a 2 metros)
        self.lbl_nombre = QLabel("Listo para escanear")
        self.lbl_nombre.setObjectName("lblNombreAprendiz")
        self.lbl_nombre.setWordWrap(True)
        col_info.addWidget(self.lbl_nombre)

        # Documento del beneficiario
        self.lbl_documento = QLabel("")
        self.lbl_documento.setObjectName("lblDocumentoAprendiz")
        col_info.addWidget(self.lbl_documento)

        # Fila inferior: chip de servicio/hora + instrucción de validación visual
        fila_pie = QHBoxLayout()
        fila_pie.setSpacing(12)

        self.lbl_chip = QLabel("")
        self.lbl_chip.setObjectName("lblChipServicioHora")
        self.lbl_chip.setVisible(False)
        fila_pie.addWidget(self.lbl_chip)

        self.lbl_detalles = QLabel(
            "Acerque el código QR al lector o presione F2 para canje manual."
        )
        self.lbl_detalles.setObjectName("lblDetallesAprendiz")
        self.lbl_detalles.setWordWrap(True)
        fila_pie.addWidget(self.lbl_detalles, 1)

        col_info.addLayout(fila_pie)
        col_info.addStretch()

        layout_raiz.addLayout(col_info, 1)

    def _aplicar_estado(self, estado: str):
        self.setProperty("estado", estado)
        self.lbl_estado_titulo.setProperty("estado", estado)
        self.lbl_nombre.setProperty("estado", estado)
        _refrescar_estilo(self)
        _refrescar_estilo(self.lbl_estado_titulo)
        _refrescar_estilo(self.lbl_nombre)

    def mostrar_resultado(self, tipo: str, datos: dict | None = None):
        """Muestra el resultado: 'entregado', 'ya_recibio', 'no_beneficiario', 'no_reconocido' o 'error_conexion'."""
        datos = datos or {}
        self.lbl_chip.setVisible(False)
        self.lbl_documento.setVisible(False)

        if tipo == "entregado":
            self._aplicar_estado("entregado")
            self.recuadro_foto.setVisible(True)
            self.lbl_foto.setText(
                "Sin foto" if not datos.get("foto_url") else "Foto cargada"
            )

            self.lbl_estado_icono.setText("✓")
            self.lbl_estado_titulo.setText("ENTREGA REGISTRADA")

            nombre = datos.get("nombre", "Beneficiario")
            doc = datos.get("documento", "")
            servicio = datos.get("servicio", "")
            hora = datos.get("hora", "")
            modalidad = datos.get("modalidad", "qr")

            self.lbl_nombre.setText(nombre)
            if doc:
                self.lbl_documento.setText(f"Documento {doc}")
                self.lbl_documento.setVisible(True)

            etiqueta_mod = " · Manual" if modalidad == "manual" else ""
            self.lbl_chip.setText(f"{servicio} · {hora}{etiqueta_mod}".strip(" ·"))
            _refrescar_estilo(self.lbl_chip)
            self.lbl_chip.setVisible(True)

            self.lbl_detalles.setText("Compare nombre y documento con la persona")

        elif tipo == "ya_recibio":
            self._aplicar_estado("ya_recibio")
            self.recuadro_foto.setVisible(False)

            self.lbl_estado_icono.setText("✕")
            self.lbl_estado_titulo.setText("YA RECIBIÓ HOY")

            nombre = datos.get("nombre", "Beneficiario")
            servicio = datos.get("servicio", "un servicio")
            hora = datos.get("hora", "")

            self.lbl_nombre.setText(nombre)
            self.lbl_detalles.setText(
                f"Recibió {servicio.lower()} a las {hora} · un servicio al día"
            )

        elif tipo == "no_beneficiario":
            self._aplicar_estado("no_beneficiario")
            self.recuadro_foto.setVisible(False)

            self.lbl_estado_icono.setText("✕")
            self.lbl_estado_titulo.setText("NO ESTÁ EN LA BASE")
            self.lbl_nombre.setText("No registrado")
            self.lbl_detalles.setText(
                "No es beneficiario activo · use F2 si tiene el documento"
            )

        elif tipo == "no_reconocido":
            self._aplicar_estado("no_reconocido")
            self.recuadro_foto.setVisible(False)

            self.lbl_estado_icono.setText("✕")
            self.lbl_estado_titulo.setText("CÓDIGO NO RECONOCIDO")
            self.lbl_nombre.setText("—")
            self.lbl_detalles.setText("El texto leído no es un ID de usuario válido")

        elif tipo == "error_conexion":
            self._aplicar_estado("error_conexion")
            self.recuadro_foto.setVisible(False)

            self.lbl_estado_icono.setText("!")
            self.lbl_estado_titulo.setText("SIN CONEXIÓN CON LA API")
            self.lbl_nombre.setText("Verifique el servidor")
            self.lbl_detalles.setText(
                datos.get("mensaje", "No se pudo conectar con el servidor de FoodPass.")
            )

    def limpiar(self):
        self._aplicar_estado("reposo")
        self.recuadro_foto.setVisible(True)
        self.lbl_foto.setText("Sin foto")
        self.lbl_estado_icono.setText("ℹ️")
        self.lbl_estado_titulo.setText("ESTADO DE ATENCIÓN")
        self.lbl_nombre.setText("Listo para escanear")
        self.lbl_documento.setVisible(False)
        self.lbl_chip.setVisible(False)
        self.lbl_detalles.setText(
            "El resultado se limpia a los 4 s o con la siguiente lectura · Sonido apagado"
        )