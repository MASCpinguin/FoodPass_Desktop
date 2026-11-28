"""Tarjeta de resultado de la ventanilla (Estación 1 · Manual de diseño v2.2, sección 7).

Cada estado se comunica con color de borde, icono, título en mayúsculas y un
detalle en lenguaje claro (RF-ES20, RNF-ES11). El avatar es de 200 × 200 px;
la base no guarda fotos, así que muestra «Sin foto».
"""

from PySide6.QtCore import QRect, Qt
from PySide6.QtGui import QFont, QFontMetrics
from PySide6.QtWidgets import QFrame, QHBoxLayout, QLabel, QVBoxLayout


def _refrescar_estilo(widget):
    widget.style().unpolish(widget)
    widget.style().polish(widget)
    widget.update()


ESTADOS = {
    "reposo": ("◎", "LISTO PARA ESCANEAR"),
    # Espacios que no se parten: si el título no cabe, baja «ALMUERZO OK» completo.
    "entregado": ("✓", "VALIDADO\u00a0— {servicio}\u00a0OK"),
    "ya_recibio": ("✕", "YA RECIBIÓ HOY"),
    "no_beneficiario": ("✕", "NO ESTÁ EN LA BASE"),
    "no_reconocido": ("✕", "CÓDIGO NO RECONOCIDO"),
    "error_conexion": ("!", "NO SE REGISTRÓ"),
    "anulado": ("↺", "CANJE ANULADO"),
}


def titulo_codigo_rechazado(mensaje):
    """Título según el motivo, para que no diga «no reconocido» si el código
    sí es de FoodPass pero ya se usó o venció."""
    texto = (mensaje or "").lower()
    if "usado" in texto or "reemplazado" in texto:
        return "CÓDIGO YA USADO"
    if "venció" in texto or "vencido" in texto:
        return "CÓDIGO VENCIDO"
    if "no encontrado" in texto:
        return "CÓDIGO NO ENCONTRADO"
    return "CÓDIGO NO RECONOCIDO"


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
        self._tamano_nombre = self.TAMANOS_NOMBRE[0]
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

    TAMANOS_NOMBRE = (32, 28, 24, 20)  # px, del más grande al más pequeño
    ANCHO_COMPACTO = 580  # por debajo (ventana de 1200 px) se usa el modo compacto

    def _medir(self, texto, ancho, px):
        fuente = QFont(self.lbl_nombre.font())
        fuente.setPixelSize(px)
        medidas = QFontMetrics(fuente)
        alto = medidas.boundingRect(
            QRect(0, 0, ancho, 10_000), Qt.TextFlag.TextWordWrap, texto
        ).height()
        return alto, round(alto / medidas.lineSpacing())

    def _ajustar_nombre(self):
        """El nombre usa 32 px. Si no cabe en una línea baja hasta 24 px; si
        aun así no cabe, usa dos líneas desde 28 px hasta 20 px. Así un nombre
        largo nunca se monta sobre el documento, ni con la ventana pequeña."""
        self.lbl_nombre.ensurePolished()
        texto = self.lbl_nombre.text()
        ancho = self.lbl_nombre.width() if self.lbl_nombre.width() > 120 else 300
        elegido = None
        for px in self.TAMANOS_NOMBRE[:3]:
            alto, lineas = self._medir(texto, ancho, px)
            if lineas <= 1:
                elegido = (px, alto)
                break
        if elegido is None:
            for px in self.TAMANOS_NOMBRE[1:]:
                alto, lineas = self._medir(texto, ancho, px)
                elegido = (px, alto)
                if lineas <= 2:
                    break
        px, alto = elegido
        self._tamano_nombre = px
        self.lbl_nombre.setStyleSheet(f"font-size: {px}px;")
        self.lbl_nombre.setMinimumHeight(alto + 4)

    def resizeEvent(self, evento):
        super().resizeEvent(evento)
        self._fijar_modo_compacto(self.width() < self.ANCHO_COMPACTO)
        self._ajustar_nombre()

    def _fijar_modo_compacto(self, compacto):
        """Ventana pequeña (1200 × 700): avatar de 150 px, márgenes y título
        más pequeños, para que el nombre y el documento quepan sin montarse."""
        if getattr(self, "_compacto", None) == compacto:
            return
        self._compacto = compacto
        lado = 150 if compacto else 200
        self.recuadro_foto.setFixedSize(lado, lado)
        self.recuadro_foto.setStyleSheet(f"border-radius: {lado // 2}px;")
        if compacto:
            self.layout().setContentsMargins(24, 16, 24, 16)
            self.layout().setSpacing(20)
            self.lbl_estado_titulo.setStyleSheet("font-size: 20px;")
        else:
            self.layout().setContentsMargins(32, 28, 32, 28)
            self.layout().setSpacing(32)
            self.lbl_estado_titulo.setStyleSheet("")

    def _aplicar_estado(self, estado, **formato):
        self._estado = estado
        icono, titulo = ESTADOS[estado]
        for w in (self, self.lbl_estado_icono, self.lbl_estado_titulo, self.lbl_nombre):
            w.setProperty("estado", estado)
            _refrescar_estilo(w)
        self.lbl_estado_icono.setText(icono)
        self.lbl_estado_titulo.setText(titulo.format(**formato))

    def mostrar_resultado(self, tipo: str, datos: dict | None = None):
        datos = datos or {}
        self.lbl_chip.setVisible(False)
        self.lbl_documento.setVisible(False)
        self.recuadro_foto.setVisible(tipo in ("entregado", "ya_recibio", "reposo"))
        self.lbl_nombre.setVisible(True)
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
            mensaje = datos.get("mensaje", "No es un código de FoodPass.")
            self.lbl_estado_titulo.setText(titulo_codigo_rechazado(mensaje))
            # Sin persona que mostrar: no se deja un «—» gigante.
            self.lbl_nombre.setVisible(False)
            self.lbl_detalles.setText(mensaje)
        elif tipo == "anulado":
            self._aplicar_estado("anulado")
            self.lbl_nombre.setText(nombre or "Canje anulado")
            self.lbl_detalles.setText(
                datos.get("mensaje", "El aprendiz puede reclamar de nuevo hoy.")
            )
        else:  # error_conexion
            self._aplicar_estado("error_conexion")
            self.lbl_nombre.setText(datos.get("accion", "Vuelve a escanear"))
            self.lbl_detalles.setText(
                datos.get(
                    "mensaje",
                    "No hay conexión con la base de datos. Avisa a soporte técnico.",
                )
            )
        self._ajustar_nombre()

    def _mostrar_documento(self, documento):
        if documento:
            self.lbl_documento.setText(f"Documento {documento}")
            self.lbl_documento.setVisible(True)

    def limpiar(self):
        self._aplicar_estado("reposo")
        self.recuadro_foto.setVisible(True)
        self.lbl_nombre.setVisible(True)
        self.lbl_nombre.setText("Esperando código")
        self.lbl_documento.setVisible(False)
        self.lbl_chip.setVisible(False)
        self.lbl_detalles.setText(
            "Elige el servicio y escanea, o usa F2 para buscar por documento."
        )
        self._ajustar_nombre()
