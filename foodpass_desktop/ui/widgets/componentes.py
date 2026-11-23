"""Componentes básicos según la Guía de Estilos de FoodPass (Manual de diseño v2.2)."""

from pathlib import Path

from PySide6.QtCore import Qt
from PySide6.QtGui import QPixmap
from PySide6.QtWidgets import (
    QFrame,
    QLabel,
    QLineEdit,
    QProgressBar,
    QPushButton,
    QVBoxLayout,
)

ALTO_BOTON = 56  # POS de escritorio: alto mínimo de la Guía
CARPETA_IMG = Path(__file__).resolve().parents[2] / "resources" / "img"
LOGOS = {
    "principal": CARPETA_IMG / "logo_foodpass.png",  # fondos claros
    "fondo_verde": CARPETA_IMG / "logo_fondo_verde.png",  # boleto blanco
}


def refrescar_estilo(widget):
    """Vuelve a aplicar el QSS tras cambiar una propiedad dinámica."""
    widget.style().unpolish(widget)
    widget.style().polish(widget)
    widget.update()


def etiqueta(texto="", nombre="", envolver=True):
    lbl = QLabel(texto)
    if nombre:
        lbl.setObjectName(nombre)
    lbl.setWordWrap(envolver)
    return lbl


class _Boton(QPushButton):
    variante = ""

    def __init__(self, texto="", parent=None):
        super().__init__(texto, parent)
        if self.variante:
            self.setProperty("variante", self.variante)
        self.setMinimumHeight(ALTO_BOTON)
        self.setCursor(Qt.CursorShape.PointingHandCursor)


class BotonPrincipal(_Boton):
    variante = "principal"


class BotonSecundario(_Boton):
    variante = "secundario"


class BotonDestructivo(_Boton):
    variante = "destructivo"


class BotonNeutro(_Boton):
    variante = ""


class CampoTexto(QLineEdit):
    def __init__(self, placeholder="", parent=None):
        super().__init__(parent)
        self.setPlaceholderText(placeholder)
        self.setMinimumHeight(46)


class Tarjeta(QFrame):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("tarjeta")
        contenido = QVBoxLayout(self)
        contenido.setContentsMargins(20, 20, 20, 20)
        contenido.setSpacing(12)


class Aviso(QLabel):
    """Aviso con borde izquierdo de color: error, advertencia, atencion o info."""

    def __init__(self, texto="", tipo="info", parent=None):
        super().__init__(texto, parent)
        self.setObjectName("aviso")
        self.setWordWrap(True)
        self.fijar(texto, tipo)

    def fijar(self, texto, tipo="info"):
        self.setText(texto)
        self.setProperty("tipo", tipo)
        refrescar_estilo(self)
        self.setVisible(bool(texto))


class Badge(QLabel):
    def __init__(self, texto="", tipo="neutro", parent=None):
        super().__init__(texto, parent)
        self.setObjectName("badge")
        self.setProperty("tipo", tipo)
        self.setAlignment(Qt.AlignmentFlag.AlignCenter)


class TarjetaMetrica(QFrame):
    """Cifra grande con etiqueta y, opcionalmente, barra de progreso."""

    def __init__(self, etiqueta_texto, con_barra=False, destacada=False, parent=None):
        super().__init__(parent)
        self.setObjectName("tarjetaMetrica")
        self.setProperty("destacada", "true" if destacada else "false")
        caja = QVBoxLayout(self)
        caja.setContentsMargins(22, 20, 22, 20)
        caja.setSpacing(6)
        self.lbl_etiqueta = etiqueta(etiqueta_texto, "etiquetaMetrica")
        self.lbl_cifra = etiqueta("0", "cifraMetrica", False)
        self.lbl_detalle = etiqueta("", "detalleMetrica")
        caja.addWidget(self.lbl_etiqueta)
        caja.addWidget(self.lbl_cifra)
        self.barra = None
        if con_barra:
            self.barra = QProgressBar()
            self.barra.setTextVisible(False)
            self.barra.setRange(0, 100)
            caja.addWidget(self.barra)
        caja.addWidget(self.lbl_detalle)
        caja.addStretch()

    def fijar(self, cifra, detalle="", porcentaje=None):
        self.lbl_cifra.setText(str(cifra))
        self.lbl_detalle.setText(detalle)
        if self.barra is not None and porcentaje is not None:
            self.barra.setValue(max(0, min(100, int(porcentaje))))


class LogoFoodPass(QFrame):
    """Logo oficial de FoodPass (Manual de diseño, 3.6).

    - "fondo_verde": boleto blanco con reloj negro, para la barra lateral y el
      panel de marca (#283618). Sus muescas dejan ver el fondo.
    - "principal": boleto naranja y verde, para fondos claros.
    """

    def __init__(self, ancho_logo=200, variante="fondo_verde", parent=None):
        super().__init__(parent)
        self.setObjectName("placaLogo")
        caja = QVBoxLayout(self)
        caja.setContentsMargins(0, 0, 0, 0)
        self.imagen = QLabel()
        self.imagen.setObjectName("imagenLogo")
        self.imagen.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.imagen.setAccessibleName("FoodPass")
        original = QPixmap(str(LOGOS.get(variante, LOGOS["fondo_verde"])))
        if original.isNull():  # sin el recurso, se muestra el nombre
            self.imagen.setText("FoodPass")
        else:
            # Nitidez en pantallas con escala alta, sin agrandar la imagen.
            escala = max(1.0, min(2.0, original.width() / ancho_logo))
            pix = original.scaledToWidth(
                int(ancho_logo * escala), Qt.TransformationMode.SmoothTransformation
            )
            pix.setDevicePixelRatio(escala)
            self.imagen.setPixmap(pix)
            self.imagen.setFixedSize(ancho_logo, round(pix.height() / escala))
        caja.addWidget(self.imagen, 0, Qt.AlignmentFlag.AlignLeft)
