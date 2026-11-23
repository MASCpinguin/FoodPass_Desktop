"""Tarjeta de resultado de la ventanilla (Estación 1 · Manual de diseño v2.2, sección 7).

Cada estado se comunica con color de borde, icono, título en mayúsculas y un
detalle en lenguaje claro (RF-ES20, RNF-ES11). El avatar es de 200 × 200 px;
la base no guarda fotos, así que muestra «Sin foto».
"""

from PySide6.QtCore import Qt
from PySide6.QtWidgets import QFrame, QHBoxLayout, QLabel, QVBoxLayout


def _refrescar_estilo(widget):
    widget.style().unpolish(widget)
    widget.style().polish(widget)
    widget.update()


ESTADOS = {
    "reposo": ("◎", "LISTO PARA ESCANEAR"),
    "entregado": ("✓", "VALIDADO — {servicio} OK"),
    "ya_recibio": ("✕", "YA RECIBIÓ HOY"),
    "no_beneficiario": ("✕", "NO ESTÁ EN LA BASE"),
    "no_reconocido": ("✕", "CÓDIGO NO RECONOCIDO"),
    "error_conexion": ("!", "SIN CONEXIÓN"),
    "anulado": ("↺", "CANJE ANULADO"),
}


class TarjetaResultado(QFrame):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("tarjetaResultado")
        self.setMinimumHeight(300)
        self._estado = "reposo"
        self.setup_ui()
        self.limpiar()

    @property
    def estado(self):
        return self._estado

    def setup_ui(self):
        raiz = QHBoxLayout(self)
        raiz.setContentsMargins(32, 28, 32, 28)
        raiz.setSpacing(32)

        self.recuadro_foto = QFrame()
        self.recuadro_foto.setObjectName("recuadroFoto")
        self.recuadro_foto.setFixedSize(200, 200)
        caja_foto = QVBoxLayout(self.recuadro_foto)
        caja_foto.setAlignment(Qt.AlignmentFlag.AlignCenter)
        silueta = QLabel("👤")
        silueta.setAlignment(Qt.AlignmentFlag.AlignCenter)
        silueta.setStyleSheet("font-size: 64px; background: transparent;")
        self.lbl_foto = QLabel("Sin foto")
        self.lbl_foto.setObjectName("lblSinFoto")
        self.lbl_foto.setAlignment(Qt.AlignmentFlag.AlignCenter)
        caja_foto.addWidget(silueta)
        caja_foto.addWidget(self.lbl_foto)
        raiz.addWidget(self.recuadro_foto, 0, Qt.AlignmentFlag.AlignVCenter)

        col = QVBoxLayout()
        col.setSpacing(10)
        col.addStretch()
        fila = QHBoxLayout()
        fila.setSpacing(10)
        self.lbl_estado_icono = QLabel("◎")
        self.lbl_estado_icono.setObjectName("lblEstadoIcono")
        self.lbl_estado_titulo = QLabel("")
        self.lbl_estado_titulo.setObjectName("lblEstadoTitulo")
        self.lbl_estado_titulo.setWordWrap(True)
        fila.addWidget(self.lbl_estado_icono)
        fila.addWidget(self.lbl_estado_titulo, 1)
        col.addLayout(fila)

        self.lbl_nombre = QLabel("")
        self.lbl_nombre.setObjectName("lblNombreAprendiz")
        self.lbl_nombre.setWordWrap(True)
        self.lbl_nombre.setMinimumHeight(
            92
        )  # espacio para dos líneas de 32 px: nunca se corta
        self.lbl_nombre.setAlignment(
            Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter
        )
        col.addWidget(self.lbl_nombre)

        self.lbl_documento = QLabel("")
        self.lbl_documento.setObjectName("lblDocumentoAprendiz")
        col.addWidget(self.lbl_documento)

        fila_chip = QHBoxLayout()
        self.lbl_chip = QLabel("")
        self.lbl_chip.setObjectName("lblChipServicioHora")
        fila_chip.addWidget(self.lbl_chip)
        fila_chip.addStretch()
        col.addLayout(fila_chip)
        self.lbl_detalles = QLabel("")
        self.lbl_detalles.setObjectName("lblDetallesAprendiz")
        self.lbl_detalles.setWordWrap(True)
        col.addWidget(self.lbl_detalles)
        col.addStretch()
        raiz.addLayout(col, 1)

    def _aplicar_estado(self, estado, **formato):
        self._estado = estado
        icono, titulo = ESTADOS[estado]
        for w in (self, self.lbl_estado_titulo, self.lbl_nombre):
            w.setProperty("estado", estado)
            _refrescar_estilo(w)
        self.lbl_estado_icono.setText(icono)
        self.lbl_estado_titulo.setText(titulo.format(**formato))

    def mostrar_resultado(self, tipo: str, datos: dict | None = None):
        datos = datos or {}
        self.lbl_chip.setVisible(False)
        self.lbl_documento.setVisible(False)
        self.recuadro_foto.setVisible(tipo in ("entregado", "ya_recibio", "reposo"))
        nombre = datos.get("nombre", "")
        documento = datos.get("documento", "")

        if tipo == "entregado":
            servicio = datos.get("servicio", "")
            self._aplicar_estado("entregado", servicio=servicio.upper())
            self.lbl_nombre.setText(nombre or "Beneficiario")
            self._mostrar_documento(documento)
            manual = " · Manual" if datos.get("modalidad") == "manual" else ""
            self.lbl_chip.setText(
                f"{servicio} · {datos.get('hora', '')}{manual}".strip(" ·")
            )
            self.lbl_chip.setVisible(True)
            self.lbl_detalles.setText("Compara nombre y documento con la persona.")
        elif tipo == "ya_recibio":
            self._aplicar_estado("ya_recibio")
            self.lbl_nombre.setText(nombre or "Beneficiario")
            self._mostrar_documento(documento)
            servicio = (datos.get("servicio") or "un servicio").lower()
            hora = datos.get("hora", "")
            texto = f"Recibió {servicio}" + (f" a las {hora}" if hora else "")
            self.lbl_detalles.setText(texto + ". Solo un servicio al día.")
        elif tipo == "no_beneficiario":
            self._aplicar_estado("no_beneficiario")
            self.lbl_nombre.setText("No registrado")
            self.lbl_detalles.setText(
                datos.get(
                    "mensaje",
                    "No es beneficiario activo. Usa F2 si tiene su documento.",
                )
            )
        elif tipo == "no_reconocido":
            self._aplicar_estado("no_reconocido")
            self.lbl_nombre.setText("—")
            self.lbl_detalles.setText(
                datos.get("mensaje", "No es un código de FoodPass.")
            )
        elif tipo == "anulado":
            self._aplicar_estado("anulado")
            self.lbl_nombre.setText(nombre or "Canje anulado")
            self.lbl_detalles.setText(
                datos.get("mensaje", "El aprendiz puede reclamar de nuevo hoy.")
            )
        else:  # error_conexion
            self._aplicar_estado("error_conexion")
            self.lbl_nombre.setText("Sin conexión")
            self.lbl_detalles.setText(
                datos.get(
                    "mensaje",
                    "No hay conexión con la base de datos. Avisa a soporte técnico.",
                )
            )

    def _mostrar_documento(self, documento):
        if documento:
            self.lbl_documento.setText(f"Documento {documento}")
            self.lbl_documento.setVisible(True)

    def limpiar(self):
        self._aplicar_estado("reposo")
        self.recuadro_foto.setVisible(True)
        self.lbl_nombre.setText("Esperando código")
        self.lbl_documento.setVisible(False)
        self.lbl_chip.setVisible(False)
        self.lbl_detalles.setText(
            "Elige el servicio y escanea, o usa F2 para buscar por documento."
        )
