"""Ventana principal: barra lateral, indicador de conexión y las cuatro
pantallas de la v2.2 (Panel, Ventanilla, Beneficiarios y Resumen del día).

Cada 30 s (y después de cada canje) consulta el resumen del día una sola vez
y lo reparte al panel, a la ventanilla y al resumen (RF-ES01). Cada 5 s
comprueba la conexión con la base (RF-ES16).
"""

from PySide6.QtCore import Qt, QTimer, Signal
from PySide6.QtWidgets import (
    QButtonGroup,
    QFrame,
    QHBoxLayout,
    QLabel,
    QMainWindow,
    QPushButton,
    QStackedWidget,
    QVBoxLayout,
    QWidget,
)

from foodpass_desktop.api.trabajador import ejecutar_en_segundo_plano
from foodpass_desktop.storage import bd, consultas_bd
from foodpass_desktop.ui.beneficiarios_view import BeneficiariosView
from foodpass_desktop.ui.panel_view import PanelView
from foodpass_desktop.ui.reporte_view import DialogoReporteEntregas, ResumenView
from foodpass_desktop.ui.ventanilla_view import VentanillaView
from foodpass_desktop.ui.widgets import LogoFoodPass, refrescar_estilo

PANTALLAS = (
    ("panel", "Panel"),
    ("ventanilla", "Ventanilla"),
    ("beneficiarios", "Beneficiarios"),
    ("resumen", "Resumen del día"),
)
REFRESCO_MS = 30_000
CONEXION_MS = 5_000


class VentanaPrincipal(QMainWindow):
    cerrar_sesion_solicitado = Signal()

    def __init__(self, parent=None, operador=None, usar_bd=None):
        super().__init__(parent)
        self.operador = operador or {}
        self._usar_bd = bd.configurada() if usar_bd is None else usar_bd
        self._conectado = True
        self._consultando = False
        self.setWindowTitle("FoodPass · Escritorio")
        self.resize(1366, 768)
        self.setMinimumSize(1200, 700)
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
        barra.setFixedWidth(248)
        menu = QVBoxLayout(barra)
        menu.setContentsMargins(20, 28, 20, 20)
        menu.setSpacing(6)
        menu.addWidget(LogoFoodPass(ancho_logo=208))
        menu.addSpacing(22)

        self.contenido = QStackedWidget()
        self.contenido.setObjectName("areaContenido")
        self.panel = PanelView()
        self.ventanilla = VentanillaView()
        self.beneficiarios = BeneficiariosView()
        self.resumen = ResumenView()
        vistas = {
            "panel": self.panel,
            "ventanilla": self.ventanilla,
            "beneficiarios": self.beneficiarios,
            "resumen": self.resumen,
        }
        self.grupo_navegacion = QButtonGroup(self)
        self.grupo_navegacion.setExclusive(True)
        for clave, titulo in PANTALLAS:
            boton = QPushButton(titulo)
            boton.setObjectName("botonNavegacion")
            # El foco se queda en el contenido (campo de lectura de la ventanilla);
            # así Windows no dibuja el recuadro punteado sobre el menú.
            boton.setFocusPolicy(Qt.FocusPolicy.NoFocus)
            boton.setCheckable(True)
            boton.setCursor(Qt.CursorShape.PointingHandCursor)
            boton.clicked.connect(lambda _c=False, c=clave: self.mostrar_pantalla(c))
            self.grupo_navegacion.addButton(boton)
            self.botones[clave] = boton
            menu.addWidget(boton)
            self.paginas[clave] = vistas[clave]
            self.contenido.addWidget(vistas[clave])
        menu.addStretch()
        menu.addWidget(self._crear_indicador())
        menu.addSpacing(10)
        menu.addWidget(self._crear_tarjeta_operador())
        menu.addSpacing(10)
        pie = QLabel("SENA · CEAI · ADSO 31")
        pie.setObjectName("pieBarra")
        menu.addWidget(pie)
        layout.addWidget(barra)
        layout.addWidget(self.contenido, 1)

        self.ventanilla.canje_registrado.connect(self.refrescar)
        self.ventanilla.abrir_reporte.connect(self.abrir_reporte)
        self.resumen.abrir_reporte.connect(self.abrir_reporte)
        self.resumen.actualizar_solicitado.connect(self.refrescar)

        self._timer_refresco = QTimer(self)
        self._timer_refresco.setInterval(REFRESCO_MS)
        self._timer_refresco.timeout.connect(self.refrescar)
        self._timer_conexion = QTimer(self)
        self._timer_conexion.setInterval(CONEXION_MS)
        self._timer_conexion.timeout.connect(self.probar_conexion)
        if self._usar_bd:
            self._timer_refresco.start()
            self._timer_conexion.start()
            self.refrescar()
            self.probar_conexion()
            self.beneficiarios.cargar()
        self.mostrar_pantalla("panel")

    # --- barra lateral --------------------------------------------------------
    def _crear_indicador(self):
        marco = QFrame()
        marco.setObjectName("indicadorConexion")
        fila = QHBoxLayout(marco)
        fila.setContentsMargins(14, 10, 14, 10)
        self.punto_conexion = QLabel("●")
        self.punto_conexion.setObjectName("puntoConexion")
        self.texto_conexion = QLabel("Conectado")
        self.texto_conexion.setObjectName("textoConexion")
        fila.addWidget(self.punto_conexion)
        fila.addWidget(self.texto_conexion, 1)
        self._pintar_conexion(True)
        return marco

    def _pintar_conexion(self, conectado):
        self._conectado = conectado
        self.punto_conexion.setProperty(
            "estado", "conectado" if conectado else "sin_conexion"
        )
        refrescar_estilo(self.punto_conexion)
        self.texto_conexion.setText("Conectado" if conectado else "Sin conexión")

    def _crear_tarjeta_operador(self):
        tarjeta = QFrame()
        tarjeta.setObjectName("tarjetaOperador")
        caja = QVBoxLayout(tarjeta)
        caja.setContentsMargins(14, 12, 14, 12)
        caja.setSpacing(6)
        etiqueta = QLabel("OPERADOR")
        etiqueta.setObjectName("etiquetaOperador")
        caja.addWidget(etiqueta)
        self.nombre_operador = QLabel(self.operador.get("nombre") or "Sin sesión")
        self.nombre_operador.setObjectName("nombreOperador")
        self.nombre_operador.setWordWrap(True)
        caja.addWidget(self.nombre_operador)
        self.boton_cerrar_sesion = QPushButton("Cerrar sesión")
        self.boton_cerrar_sesion.setObjectName("botonCerrarSesion")
        self.boton_cerrar_sesion.setCursor(Qt.CursorShape.PointingHandCursor)
        self.boton_cerrar_sesion.clicked.connect(self.cerrar_sesion_solicitado.emit)
        caja.addWidget(self.boton_cerrar_sesion)
        return tarjeta

    # --- navegación ---------------------------------------------------------------
    def mostrar_pantalla(self, clave):
        self.contenido.setCurrentWidget(self.paginas[clave])
        self.botones[clave].setChecked(True)
        if clave == "beneficiarios" and self._usar_bd:
            self.beneficiarios.cargar()

    def abrir_reporte(self):
        DialogoReporteEntregas(self).exec()

    # --- datos del día --------------------------------------------------------------
    def refrescar(self):
        if not self._usar_bd or self._consultando:
            return
        self._consultando = True
        ejecutar_en_segundo_plano(
            consultas_bd.resumen_dia,
            al_exito=self._resumen_listo,
            al_error=self._resumen_fallo,
        )

    def _resumen_listo(self, resumen):
        self._consultando = False
        self._pintar_conexion(True)
        self.panel.actualizar(resumen, True)
        self.resumen.actualizar(resumen, True)
        self.ventanilla.fijar_conteo_del_dia(resumen["por_servicio"])

    def _resumen_fallo(self, _error):
        self._consultando = False
        self._pintar_conexion(False)
        self.panel.actualizar(None, False)
        self.resumen.actualizar(None, False)

    def probar_conexion(self):
        ejecutar_en_segundo_plano(bd.probar, al_exito=self._conexion_probada)

    def _conexion_probada(self, ok):
        estaba = self._conectado
        self._pintar_conexion(bool(ok))
        if ok and not estaba:
            self.refrescar()
        elif not ok:
            self.panel.actualizar(None, False)
