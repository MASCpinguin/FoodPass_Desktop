"""Ventana compartida y puntos de integración de las pantallas."""
from PySide6.QtCore import Qt
from PySide6.QtWidgets import (QButtonGroup, QFrame, QHBoxLayout, QLabel,
                               QMainWindow, QPushButton, QStackedWidget,
                               QVBoxLayout, QWidget)

from foodpass_desktop.ui.ventanilla_view import VentanillaView

PANTALLAS = (
    ("panel", "Panel"),
    ("ventanilla", "Ventanilla"),
    ("produccion", "Producción"),
    ("reportes", "Cierre y reportes"),
    ("beneficiarios", "Beneficiarios"),
    ("auditoria", "Auditoría"),
    ("productos", "Productos"),
    ("configuracion", "Configuración"),
)


def pantalla_pendiente(titulo):
    pantalla = QWidget()
    layout = QVBoxLayout(pantalla)
    layout.setContentsMargins(36, 32, 36, 32)
    etiqueta = QLabel(titulo)
    etiqueta.setObjectName("tituloPantalla")
    etiqueta.setWordWrap(True)
    layout.addWidget(etiqueta)
    descripcion = QLabel("Espacio disponible para el módulo de " + titulo.lower() + ".")
    descripcion.setObjectName("descripcionPantalla")
    descripcion.setWordWrap(True)
    layout.addWidget(descripcion)
    layout.addStretch()
    return pantalla


class VentanaPrincipal(QMainWindow):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("FoodPass · Escritorio")
        self.resize(1200, 700)
        self.setMinimumSize(900, 600)
        self.paginas = {}
        self.botones = {}
        central = QWidget()
        central.setObjectName("contenedorPrincipal")
        self.setCentralWidget(central)
        layout = QHBoxLayout(central)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        barra = QFrame()
        barra.setObjectName("barraLateral")
        barra.setFixedWidth(230)
        menu = QVBoxLayout(barra)
        menu.setContentsMargins(16, 24, 16, 20)
        menu.setSpacing(5)
        marca = QLabel("FoodPass")
        marca.setObjectName("marca")
        menu.addWidget(marca)
        subtitulo = QLabel("ESCRITORIO · CAFETERÍA")
        subtitulo.setObjectName("subtituloMarca")
        menu.addWidget(subtitulo)
        menu.addSpacing(24)
        self.grupo_navegacion = QButtonGroup(self)
        self.grupo_navegacion.setExclusive(True)
        self.contenido = QStackedWidget()
        self.contenido.setObjectName("areaContenido")
        for clave, titulo in PANTALLAS:
            boton = QPushButton(titulo)
            boton.setObjectName("botonNavegacion")
            boton.setCheckable(True)
            boton.setMinimumHeight(44)
            boton.setCursor(Qt.PointingHandCursor)
            boton.clicked.connect(lambda _checked=False, c=clave: self.mostrar_pantalla(c))
            self.grupo_navegacion.addButton(boton)
            self.botones[clave] = boton
            menu.addWidget(boton)
            pagina = VentanillaView() if clave == "ventanilla" else pantalla_pendiente(titulo)
            self.paginas[clave] = pagina
            self.contenido.addWidget(pagina)
        menu.addStretch()
        pie = QLabel("FOODPASS  /  ADSO")
        pie.setObjectName("pieBarra")
        menu.addWidget(pie)
        layout.addWidget(barra)
        layout.addWidget(self.contenido, 1)
        self.mostrar_pantalla("panel")

    def mostrar_pantalla(self, clave):
        """Muestra una página registrada y actualiza la navegación."""
        self.contenido.setCurrentWidget(self.paginas[clave])
        self.botones[clave].setChecked(True)

    def reemplazar_pantalla(self, clave, pagina):
        """Sustituye una página existente sin alterar su opción en el menú."""
        anterior = self.paginas[clave]
        indice = self.contenido.indexOf(anterior)
        activa = self.contenido.currentWidget() is anterior
        self.contenido.removeWidget(anterior)
        self.contenido.insertWidget(indice, pagina)
        self.paginas[clave] = pagina
        anterior.deleteLater()
        if activa:
            self.contenido.setCurrentWidget(pagina)
