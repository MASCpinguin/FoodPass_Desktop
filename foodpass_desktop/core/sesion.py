"""Coordina la sesión del operador entre ventanas (T05 · RF-ES25 · CU-01).

Flujo:
1. Arranca en la pantalla de inicio de sesión.
2. Login correcto (y PIN creado la primera vez) -> abre la ventana principal,
   programa la renovación del token y empieza a medir la inactividad.
3. Inactividad -> oculta la ventana principal y pide el PIN.
4. PIN correcto -> vuelve a la ventana principal tal como estaba.
5. Cinco PIN errados, «Cerrar sesión» o token vencido -> borra el token y
   pide correo y contraseña.
"""

from PySide6.QtCore import QObject, QTimer, Signal

from foodpass_desktop.api.errores import SinConexionError
from foodpass_desktop.api.trabajador import ejecutar_en_segundo_plano
from foodpass_desktop.core.inactividad import DetectorInactividad
from foodpass_desktop.ui.login_window import LoginWindow
from foodpass_desktop.ui.ventana_principal import VentanaPrincipal

REINTENTO_RENOVACION_MS = 60_000
MENSAJE_SESION_VENCIDA = "Tu sesión venció. Ingresa de nuevo."


class ControladorSesion(QObject):
    # El cliente avisa del 401 desde un hilo secundario; la señal lo trae
    # de vuelta al hilo de la interfaz.
    sesion_vencida = Signal()

    def __init__(self, app, auth, cliente, minutos_bloqueo, parent=None):
        super().__init__(parent)
        self._app = app
        self._auth = auth
        self.ventana = None

        self.login = LoginWindow(auth)
        self.login.sesion_iniciada.connect(self._abrir_principal)
        self.login.desbloqueada.connect(self._desbloquear)
        self.login.pin_agotado.connect(self._terminar_sesion_local)
        self.login.cambiar_cuenta.connect(self.cerrar_sesion)

        self.detector = DetectorInactividad(app, minutos_bloqueo, self)
        self.detector.inactivo.connect(self.bloquear)

        self._renovacion = QTimer(self)
        self._renovacion.setSingleShot(True)
        self._renovacion.timeout.connect(self._renovar_token)

        self.sesion_vencida.connect(self._sesion_vencida)
        cliente.al_expirar_sesion(self.sesion_vencida.emit)
        app.aboutToQuit.connect(self._al_salir)

    def iniciar(self):
        self.login.show()

    # --- transiciones ---------------------------------------------------------
    def _abrir_principal(self, operador):
        self._descartar_ventana()
        self.ventana = VentanaPrincipal(operador=operador)
        self.ventana.cerrar_sesion_solicitado.connect(self.cerrar_sesion)
        self.ventana.show()
        self.login.hide()
        self._programar_renovacion()
        self.detector.iniciar()

    def bloquear(self):
        """Oculta la operación y pide el PIN (aunque el token haya vencido)."""
        if self.ventana is None:
            return
        self.detector.detener()
        self.login.mostrar_desbloqueo(self._auth.operador)
        self.login.show()
        self.ventana.hide()
        self.login.activateWindow()

    def _desbloquear(self):
        if self.ventana is None:
            return
        self.ventana.show()
        self.login.hide()
        self.ventana.activateWindow()
        self.detector.iniciar()

    def cerrar_sesion(self):
        """Botón «Cerrar sesión» o «Ingresar con correo y contraseña»."""
        ejecutar_en_segundo_plano(self._auth.cerrar_sesion)
        self._volver_al_login()

    def _terminar_sesion_local(self):
        """Cinco PIN errados: el servicio ya borró el token."""
        self._volver_al_login(mensaje=None, mostrar=False)

    def _sesion_vencida(self):
        if self.ventana is None:
            return  # el 401 llegó cuando ya no había sesión
        self._auth.borrar_sesion()
        self._volver_al_login(MENSAJE_SESION_VENCIDA)

    def _volver_al_login(self, mensaje=None, mostrar=True):
        self.detector.detener()
        self._renovacion.stop()
        if mostrar:
            self.login.mostrar_acceso(mensaje)
        self.login.show()  # antes de ocultar la principal: siempre hay una visible
        self._descartar_ventana()

    def _descartar_ventana(self):
        if self.ventana is not None:
            self.ventana.hide()
            self.ventana.deleteLater()
            self.ventana = None

    # --- renovación del token (EP-31) -----------------------------------------
    def _programar_renovacion(self, milisegundos=None):
        if milisegundos is None:
            milisegundos = self._auth.segundos_para_renovar() * 1000
        self._renovacion.start(max(0, int(milisegundos)))

    def _renovar_token(self):
        if self.ventana is None:
            return
        ejecutar_en_segundo_plano(
            self._auth.renovar,
            al_exito=self._token_renovado,
            al_error=self._renovacion_fallida,
        )

    def _token_renovado(self, _expira):
        self._programar_renovacion()

    def _renovacion_fallida(self, error):
        # Sin red: se reintenta cada minuto mientras el token siga vigente.
        # Un 401 lo atiende `sesion_vencida`, que avisa el propio cliente.
        if isinstance(error, SinConexionError) and self._auth.hay_sesion:
            self._programar_renovacion(REINTENTO_RENOVACION_MS)

    # --- salida -------------------------------------------------------------------
    def _al_salir(self):
        """Al cerrar la app se revoca el token (máx. 3 s, la ventana ya cerró)."""
        self.detector.detener()
        self._renovacion.stop()
        if self._auth.hay_sesion:
            self._auth.cerrar_sesion()
