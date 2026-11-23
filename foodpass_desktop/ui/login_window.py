"""Pantalla 1 · Inicio de sesión y desbloqueo con PIN (T05 · RF-ES25 · CU-01).

Manual de diseño v2.1, ficha 1: panel de marca a la izquierda y tarjeta de
acceso a la derecha. La vista de desbloqueo (PIN) reemplaza a la tarjeta de
acceso, no se muestra debajo.

Toda la lógica vive en services/auth_service.py; aquí solo se muestra.
"""

from PySide6.QtCore import Qt, QTimer, Signal
from PySide6.QtGui import QColor
from PySide6.QtWidgets import (
    QFrame,
    QGraphicsDropShadowEffect,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QStackedWidget,
    QVBoxLayout,
    QWidget,
)

from foodpass_desktop.api.trabajador import ejecutar_en_segundo_plano
from foodpass_desktop.services.auth_service import (
    LARGO_PIN,
    MENSAJES,
    interpretar_error,
    mensaje_bloqueo,
    validar_credenciales,
)
from foodpass_desktop.ui.widgets import BotonPrincipal, BotonSecundario, CampoTexto

TEXTO_INGRESAR = "Ingresar"
TEXTO_INGRESANDO = "Ingresando…"


def _etiqueta(texto, nombre, envolver=False):
    etiqueta = QLabel(texto)
    etiqueta.setObjectName(nombre)
    etiqueta.setWordWrap(envolver)
    return etiqueta


def _refrescar_estilo(widget):
    """Vuelve a aplicar el QSS tras cambiar una propiedad dinámica."""
    widget.style().unpolish(widget)
    widget.style().polish(widget)


class LoginWindow(QWidget):
    """Ventana de acceso. La coordina core/sesion.py.

    Señales:
    - sesion_iniciada(dict): login correcto y PIN listo; trae el operador.
    - desbloqueada(): PIN correcto.
    - pin_agotado(): cinco PIN errados; el token ya se borró.
    - cambiar_cuenta(): el operador pidió entrar con correo y contraseña.
    """

    sesion_iniciada = Signal(dict)
    desbloqueada = Signal()
    pin_agotado = Signal()
    cambiar_cuenta = Signal()

    def __init__(self, auth, parent=None):
        super().__init__(parent)
        self._auth = auth
        self._operador = {}
        self._modo_pin = "desbloquear"  # o "crear"
        self._segundos_bloqueo = 0

        self.setObjectName("vistaLogin")
        self.setAttribute(Qt.WidgetAttribute.WA_StyledBackground, True)
        self.setWindowTitle("FoodPass · Iniciar sesión")
        self.resize(1200, 700)
        self.setMinimumSize(900, 600)

        self._cuenta_regresiva = QTimer(self)
        self._cuenta_regresiva.setInterval(1000)
        self._cuenta_regresiva.timeout.connect(self._avanzar_cuenta_regresiva)

        raiz = QHBoxLayout(self)
        raiz.setContentsMargins(0, 0, 0, 0)
        raiz.setSpacing(0)
        raiz.addWidget(self._crear_panel_marca(), 1)

        zona = QWidget()
        centro = QVBoxLayout(zona)
        centro.setContentsMargins(40, 36, 40, 36)
        centro.addStretch()
        centro.addWidget(self._crear_tarjeta(), 0, Qt.AlignmentFlag.AlignHCenter)
        centro.addStretch()
        raiz.addWidget(zona, 1)

        self.mostrar_acceso()

    # --- construcción -------------------------------------------------------
    def _crear_panel_marca(self):
        panel = QFrame()
        panel.setObjectName("panelMarcaLogin")
        panel.setMinimumWidth(340)
        panel.setMaximumWidth(620)
        caja = QVBoxLayout(panel)
        caja.setContentsMargins(56, 48, 56, 48)
        caja.setSpacing(16)
        marca = QHBoxLayout()
        marca.setSpacing(0)
        marca.addWidget(_etiqueta("Food", "marcaLogin"))
        marca.addWidget(_etiqueta("Pass", "marcaPassLogin"))
        marca.addStretch()
        caja.addLayout(marca)
        caja.addWidget(_etiqueta("ESCRITORIO · CAFETERÍA", "subtituloMarcaLogin"))
        caja.addStretch()
        caja.addWidget(_etiqueta("Verifica\nsin filas.", "heroLogin", True))
        caja.addWidget(
            _etiqueta(
                "Entrega el apoyo de alimentación en segundos: escanea el "
                "código FoodPass y listo.",
                "descripcionMarcaLogin",
                True,
            )
        )
        caja.addStretch()
        caja.addWidget(_etiqueta("SENA · CEAI · ADSO 31", "pieMarcaLogin"))
        return panel

    def _crear_tarjeta(self):
        tarjeta = QFrame()
        tarjeta.setObjectName("tarjetaAcceso")
        tarjeta.setFixedWidth(440)
        sombra = QGraphicsDropShadowEffect(tarjeta)
        sombra.setBlurRadius(40)
        sombra.setOffset(0, 12)
        sombra.setColor(QColor(36, 51, 20, 26))  # rgba(36,51,20,0.10)
        tarjeta.setGraphicsEffect(sombra)

        caja = QVBoxLayout(tarjeta)
        caja.setContentsMargins(36, 36, 36, 36)
        self.vistas = QStackedWidget()
        self.vista_acceso = self._crear_vista_acceso()
        self.vista_pin = self._crear_vista_pin()
        self.vistas.addWidget(self.vista_acceso)
        self.vistas.addWidget(self.vista_pin)
        caja.addWidget(self.vistas)
        return tarjeta

    def _crear_vista_acceso(self):
        vista = QWidget()
        caja = QVBoxLayout(vista)
        caja.setContentsMargins(0, 0, 0, 0)
        caja.setSpacing(8)
        caja.addWidget(_etiqueta("Iniciar sesión", "tituloAcceso"))
        caja.addWidget(
            _etiqueta(
                "Ingresa con el correo y la contraseña de tu cuenta FoodPass.",
                "descripcionAcceso",
                True,
            )
        )
        caja.addSpacing(14)

        caja.addWidget(_etiqueta("CORREO", "etiquetaCampoLogin"))
        self.campo_email = CampoTexto("operador@foodpass.com")
        self.campo_email.setObjectName("campoLogin")
        self.campo_email.returnPressed.connect(self._enviar_login)
        caja.addWidget(self.campo_email)
        caja.addSpacing(6)

        caja.addWidget(_etiqueta("CONTRASEÑA", "etiquetaCampoLogin"))
        self.campo_password = CampoTexto("Tu contraseña")
        self.campo_password.setObjectName("campoLogin")
        self.campo_password.setEchoMode(QLineEdit.EchoMode.Password)
        self.campo_password.returnPressed.connect(self._enviar_login)
        caja.addWidget(self.campo_password)

        self.mensaje_acceso = _etiqueta("", "mensajeLogin", True)
        self.mensaje_acceso.setProperty("tipo", "error")
        self.mensaje_acceso.hide()
        caja.addSpacing(6)
        caja.addWidget(self.mensaje_acceso)
        caja.addSpacing(10)

        self.boton_ingresar = BotonPrincipal(TEXTO_INGRESAR)
        self.boton_ingresar.setObjectName("botonIngresar")
        self.boton_ingresar.setCursor(Qt.CursorShape.PointingHandCursor)
        self.boton_ingresar.clicked.connect(self._enviar_login)
        caja.addWidget(self.boton_ingresar)
        caja.addStretch()
        return vista

    def _crear_vista_pin(self):
        vista = QWidget()
        caja = QVBoxLayout(vista)
        caja.setContentsMargins(0, 0, 0, 0)
        caja.setSpacing(8)
        self.titulo_pin = _etiqueta("", "tituloAcceso")
        self.descripcion_pin = _etiqueta("", "descripcionAcceso", True)
        caja.addWidget(self.titulo_pin)
        caja.addWidget(self.descripcion_pin)
        caja.addSpacing(14)

        self.etiqueta_pin = _etiqueta("PIN", "etiquetaCampoLogin")
        caja.addWidget(self.etiqueta_pin)
        self.campo_pin = self._crear_campo_pin()
        self.campo_pin.returnPressed.connect(self._enviar_pin)
        caja.addWidget(self.campo_pin)

        self.etiqueta_confirmacion = _etiqueta("CONFIRMA EL PIN", "etiquetaCampoLogin")
        self.etiqueta_confirmacion.setContentsMargins(0, 8, 0, 0)
        caja.addWidget(self.etiqueta_confirmacion)
        self.campo_confirmacion = self._crear_campo_pin()
        self.campo_confirmacion.returnPressed.connect(self._enviar_pin)
        caja.addWidget(self.campo_confirmacion)

        self.mensaje_pin = _etiqueta("", "mensajeLogin", True)
        self.mensaje_pin.setProperty("tipo", "error")
        self.mensaje_pin.hide()
        caja.addSpacing(6)
        caja.addWidget(self.mensaje_pin)
        caja.addSpacing(10)

        self.boton_pin = BotonPrincipal("Desbloquear")
        self.boton_pin.setCursor(Qt.CursorShape.PointingHandCursor)
        self.boton_pin.clicked.connect(self._enviar_pin)
        caja.addWidget(self.boton_pin)

        self.boton_otra_cuenta = BotonSecundario("Ingresar con correo y contraseña")
        self.boton_otra_cuenta.setCursor(Qt.CursorShape.PointingHandCursor)
        self.boton_otra_cuenta.clicked.connect(self.cambiar_cuenta.emit)
        caja.addWidget(self.boton_otra_cuenta)
        caja.addStretch()
        return vista

    def _crear_campo_pin(self):
        campo = QLineEdit()
        campo.setObjectName("campoPin")
        campo.setEchoMode(QLineEdit.EchoMode.Password)
        campo.setMaxLength(LARGO_PIN[1])
        campo.setAlignment(Qt.AlignmentFlag.AlignCenter)
        campo.setPlaceholderText("••••")
        campo.setMinimumHeight(64)
        campo.setInputMethodHints(Qt.InputMethodHint.ImhDigitsOnly)
        return campo

    # --- cambiar de vista ---------------------------------------------------
    def mostrar_acceso(self, mensaje=None):
        """Vista de correo y contraseña. `mensaje` explica por qué se llegó aquí."""
        self.vistas.setCurrentWidget(self.vista_acceso)
        self.setWindowTitle("FoodPass · Iniciar sesión")
        self.campo_password.clear()
        self._fijar_ocupado(False)
        if mensaje:
            self._mostrar_mensaje(self.mensaje_acceso, mensaje)
        elif not self._cuenta_regresiva.isActive():
            self.mensaje_acceso.hide()
        destino = self.campo_password if self.campo_email.text() else self.campo_email
        destino.setFocus()
        # Bloqueo local vigente (por ejemplo, tras reiniciar la aplicación)
        consultar = getattr(self._auth, "segundos_bloqueo", None)
        restantes = consultar() if callable(consultar) else 0
        if restantes > 0 and not self._cuenta_regresiva.isActive():
            self._iniciar_cuenta_regresiva(restantes)

    def mostrar_desbloqueo(self, operador=None):
        """Vista de PIN tras la inactividad. No muestra datos de la operación."""
        self._operador = operador or self._operador
        self._preparar_pin("desbloquear")

    def mostrar_crear_pin(self, operador):
        """Primer ingreso en este equipo: el operador elige su PIN."""
        self._operador = operador or {}
        self._preparar_pin("crear")

    def _preparar_pin(self, modo):
        self._modo_pin = modo
        crear = modo == "crear"
        nombre = self._operador.get("nombre") or "operador"
        if crear:
            self.titulo_pin.setText("Crea tu PIN")
            self.descripcion_pin.setText(
                f"Hola, {nombre}. Elige un PIN de 4 a 6 dígitos. Lo usarás para "
                "desbloquear la pantalla cuando no uses el equipo por un rato."
            )
            self.boton_pin.setText("Guardar PIN")
        else:
            self.titulo_pin.setText("Pantalla bloqueada")
            self.descripcion_pin.setText(
                f"Sesión de {nombre}. Escribe tu PIN para continuar."
            )
            self.boton_pin.setText("Desbloquear")
        self.etiqueta_confirmacion.setVisible(crear)
        self.campo_confirmacion.setVisible(crear)
        self.boton_otra_cuenta.setVisible(not crear)
        self.campo_pin.clear()
        self.campo_confirmacion.clear()
        self.mensaje_pin.hide()
        self.vistas.setCurrentWidget(self.vista_pin)
        self.setWindowTitle("FoodPass · " + self.titulo_pin.text())
        self.campo_pin.setFocus()

    # --- inicio de sesión ---------------------------------------------------
    def _enviar_login(self):
        if not self.boton_ingresar.isEnabled():
            return  # ya hay una petición en curso o la cuenta está bloqueada
        email = self.campo_email.text().strip()
        password = self.campo_password.text()
        codigo = validar_credenciales(email, password)
        if codigo:
            self._mostrar_mensaje(self.mensaje_acceso, MENSAJES[codigo])
            campo = (
                self.campo_email if codigo == "CORREO_INVALIDO" else self.campo_password
            )
            campo.setFocus()
            return
        self.mensaje_acceso.hide()
        self._fijar_ocupado(True)
        ejecutar_en_segundo_plano(
            self._auth.iniciar_sesion,
            email,
            password,
            al_exito=self._login_exitoso,
            al_error=self._login_fallido,
        )

    def _login_exitoso(self, operador):
        self._fijar_ocupado(False)
        self.campo_password.clear()
        if self._auth.hay_pin():
            self.sesion_iniciada.emit(operador or {})
        else:
            self.mostrar_crear_pin(operador)

    def _login_fallido(self, error):
        error = interpretar_error(error)
        self._fijar_ocupado(False)
        self.campo_password.clear()
        if error.codigo == "CUENTA_BLOQUEADA" and error.segundos_restantes > 0:
            self._iniciar_cuenta_regresiva(error.segundos_restantes)
            return
        self._mostrar_mensaje(self.mensaje_acceso, error.mensaje)
        self.campo_password.setFocus()

    def _fijar_ocupado(self, ocupado):
        self.campo_email.setEnabled(not ocupado)
        self.campo_password.setEnabled(not ocupado)
        bloqueada = self._cuenta_regresiva.isActive()
        self.boton_ingresar.setEnabled(not ocupado and not bloqueada)
        self.boton_ingresar.setText(TEXTO_INGRESANDO if ocupado else TEXTO_INGRESAR)

    # --- cuenta regresiva (423 CUENTA_BLOQUEADA) ------------------------------
    def _iniciar_cuenta_regresiva(self, segundos):
        self._segundos_bloqueo = int(segundos)
        self._cuenta_regresiva.start()
        self.boton_ingresar.setEnabled(False)
        self.campo_email.setEnabled(False)
        self.campo_password.setEnabled(False)
        self.mensaje_acceso.setProperty("tipo", "aviso")
        self._mostrar_mensaje(self.mensaje_acceso, mensaje_bloqueo(segundos))

    def _avanzar_cuenta_regresiva(self):
        self._segundos_bloqueo -= 1
        if self._segundos_bloqueo > 0:
            self.mensaje_acceso.setText(mensaje_bloqueo(self._segundos_bloqueo))
            return
        self._cuenta_regresiva.stop()
        self.mensaje_acceso.hide()
        self.mensaje_acceso.setProperty("tipo", "error")
        self.campo_email.setEnabled(True)
        self.campo_password.setEnabled(True)
        self.boton_ingresar.setEnabled(True)
        self.campo_password.setFocus()

    # --- PIN ------------------------------------------------------------------
    def _enviar_pin(self):
        pin = self.campo_pin.text()
        if self._modo_pin == "crear":
            error = self._auth.crear_pin(pin, self.campo_confirmacion.text())
            if error:
                self._mostrar_mensaje(self.mensaje_pin, error)
                self.campo_pin.clear()
                self.campo_confirmacion.clear()
                self.campo_pin.setFocus()
                return
            self.sesion_iniciada.emit(self._operador)
            return

        resultado = self._auth.verificar_pin(pin)
        if resultado.correcto:
            self.mensaje_pin.hide()
            self.campo_pin.clear()
            self.desbloqueada.emit()
        elif resultado.agotado:
            self.mostrar_acceso(resultado.mensaje)
            self.pin_agotado.emit()
        else:
            self._mostrar_mensaje(self.mensaje_pin, resultado.mensaje)
            self.campo_pin.clear()
            self.campo_pin.setFocus()

    # --- utilidades -------------------------------------------------------------
    def _mostrar_mensaje(self, etiqueta, texto):
        etiqueta.setText(texto)
        etiqueta.show()
        _refrescar_estilo(etiqueta)

    @property
    def cuenta_bloqueada(self):
        return self._cuenta_regresiva.isActive()
