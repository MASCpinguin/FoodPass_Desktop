"""Pantalla 5 · Cierre de caja (T30 · RF-ES05).

Muestra el resumen del día calculado por la API y cierra la caja en 2 clics:
«Cerrar caja» y la confirmación. Las llamadas a la API corren en segundo
plano para no congelar la ventana (RNF-ES03).
"""

from PySide6.QtCore import QObject, QRunnable, Qt, QThreadPool, Signal
from PySide6.QtWidgets import (
    QFrame,
    QGridLayout,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QMessageBox,
    QPushButton,
    QVBoxLayout,
    QWidget,
)

from foodpass_desktop.services.caja_service import ErrorCaja, formato_pesos

# Colores del 04 Manual de diseño (sección 3.1).
# Pasarlos a resources/styles/tokens.py cuando se fusione T02.
C = {
    "fondo": "#EEFDD6",
    "blanco": "#FFFFFF",
    "verde_bosque": "#243314",
    "verde_claro": "#E2F3C5",
    "verde_muy_claro": "#F1F8E4",
    "naranja": "#FA7D2D",
    "texto_naranja": "#2B1600",
    "texto": "#1B2A0E",
    "texto_2": "#5B6B45",
    "sobre_oscuro": "#C9D8B0",
    "exito_texto": "#1E5C1E",
    "exito_fondo": "#D6F0D0",
    "error_borde": "#C0392B",
    "error_fondo": "#FBE9E6",
    "gris_chip": "#E7E7E7",
    "gris_texto": "#444444",
}

NOMBRES_METODO = {"nequi": "Nequi", "transferencia": "Transferencia", "efectivo": "Efectivo"}
NOMBRES_SERVICIO = {"desayuno": "Desayunos", "almuerzo": "Almuerzos", "refrigerio": "Refrigerios"}
DIAS = ["lunes", "martes", "miércoles", "jueves", "viernes", "sábado", "domingo"]
MESES = ["enero", "febrero", "marzo", "abril", "mayo", "junio", "julio", "agosto",
         "septiembre", "octubre", "noviembre", "diciembre"]


def fecha_larga(fecha):
    """date -> 'sábado 14 de noviembre de 2026'."""
    return f"{DIAS[fecha.weekday()]} {fecha.day} de {MESES[fecha.month - 1]} de {fecha.year}"


class _Senales(QObject):
    listo = Signal(object)
    fallo = Signal(object)


class _Tarea(QRunnable):
    """Ejecuta una función en segundo plano y avisa con señales."""

    def __init__(self, funcion, *args, **kwargs):
        super().__init__()
        self.funcion = funcion
        self.args = args
        self.kwargs = kwargs
        self.senales = _Senales()

    def run(self):
        try:
            resultado = self.funcion(*self.args, **self.kwargs)
        except Exception as exc:  # se muestra en la pantalla
            self.senales.fallo.emit(exc)
        else:
            self.senales.listo.emit(resultado)


def _tarjeta(oscura=False):
    marco = QFrame()
    fondo = C["verde_bosque"] if oscura else C["blanco"]
    marco.setObjectName("tarjeta")
    marco.setStyleSheet(f"#tarjeta {{ background: {fondo}; border-radius: 14px; }}")
    capa = QVBoxLayout(marco)
    capa.setContentsMargins(20, 18, 20, 18)
    capa.setSpacing(6)
    return marco, capa


def _etiqueta(texto, tam=14, peso=400, color=None):
    lbl = QLabel(texto)
    lbl.setStyleSheet(
        f"color: {color or C['texto']}; font-size: {tam}px; font-weight: {peso};"
        " background: transparent;"
    )
    return lbl


class CierreCajaView(QWidget):
    """Resumen del día y cierre de caja."""

    caja_cerrada = Signal(object)  # CierreCaja

    def __init__(self, servicio, parent=None):
        super().__init__(parent)
        self.servicio = servicio
        self.resumen = None
        self.pool = QThreadPool.globalInstance()
        self._tareas = set()  # evita que Python libere una tarea en curso
        self.setObjectName("cierreCaja")
        self.setAttribute(Qt.WA_StyledBackground, True)  # pinta el fondo del QSS
        self.setStyleSheet(
            f"#cierreCaja {{ background: {C['fondo']}; }}"
            " QLabel { font-family: 'Plus Jakarta Sans', 'Segoe UI', sans-serif; }"
        )
        self._construir()
        self.cargar()

    # ---------- Construcción ----------
    def _construir(self):
        raiz = QVBoxLayout(self)
        raiz.setContentsMargins(32, 28, 32, 28)
        raiz.setSpacing(18)

        # Encabezado
        encabezado = QHBoxLayout()
        titulos = QVBoxLayout()
        titulos.setSpacing(2)
        titulos.addWidget(_etiqueta("Cierre de caja", 28, 800))
        self.lbl_fecha = _etiqueta("Cargando…", 15, 500, C["texto_2"])
        titulos.addWidget(self.lbl_fecha)
        encabezado.addLayout(titulos)
        encabezado.addStretch()
        self.chip_estado = QLabel()
        self.chip_estado.setAlignment(Qt.AlignCenter)
        self.chip_estado.setMinimumHeight(32)
        encabezado.addWidget(self.chip_estado, alignment=Qt.AlignTop)
        raiz.addLayout(encabezado)

        # Fila de tarjetas
        fila = QHBoxLayout()
        fila.setSpacing(16)

        tarjeta_total, capa = _tarjeta(oscura=True)
        capa.addWidget(_etiqueta("TOTAL DEL DÍA", 12, 700, C["sobre_oscuro"]))
        self.lbl_total = _etiqueta("$ 0", 40, 800, C["blanco"])
        capa.addWidget(self.lbl_total)
        self.lbl_n_ventas = _etiqueta("0 ventas", 14, 500, C["sobre_oscuro"])
        capa.addWidget(self.lbl_n_ventas)
        capa.addStretch()
        fila.addWidget(tarjeta_total, 3)

        tarjeta_entregas, capa = _tarjeta()
        capa.addWidget(_etiqueta("ENTREGAS DEL DÍA", 12, 700, C["texto_2"]))
        self.lbl_total_canjes = _etiqueta("0", 32, 800)
        capa.addWidget(self.lbl_total_canjes)
        self.lbl_servicios = {}
        for clave, nombre in NOMBRES_SERVICIO.items():
            linea = QHBoxLayout()
            linea.addWidget(_etiqueta(nombre, 14, 500, C["texto_2"]))
            linea.addStretch()
            self.lbl_servicios[clave] = _etiqueta("0", 14, 700)
            linea.addWidget(self.lbl_servicios[clave])
            capa.addLayout(linea)
        fila.addWidget(tarjeta_entregas, 2)

        tarjeta_pedidos, capa = _tarjeta()
        capa.addWidget(_etiqueta("PEDIDOS WEB ATENDIDOS", 12, 700, C["texto_2"]))
        self.lbl_pedidos = _etiqueta("0", 32, 800)
        capa.addWidget(self.lbl_pedidos)
        capa.addWidget(_etiqueta("Entregados hoy al cliente", 13, 500, C["texto_2"]))
        capa.addStretch()
        fila.addWidget(tarjeta_pedidos, 2)
        raiz.addLayout(fila)

        # Ventas por medio de pago
        tarjeta_metodos, capa = _tarjeta()
        capa.addWidget(_etiqueta("VENTAS POR MEDIO DE PAGO", 12, 700, C["texto_2"]))
        tabla = QGridLayout()
        tabla.setHorizontalSpacing(24)
        tabla.setVerticalSpacing(10)
        for col, titulo in enumerate(["Medio de pago", "Ventas", "Total"]):
            lbl = _etiqueta(titulo, 13, 700, C["texto_2"])
            if col:
                lbl.setAlignment(Qt.AlignRight)
            tabla.addWidget(lbl, 0, col)
        self.lbl_metodos = {}
        for fila_n, (clave, nombre) in enumerate(NOMBRES_METODO.items(), start=1):
            tabla.addWidget(_etiqueta(nombre, 15, 600), fila_n, 0)
            n = _etiqueta("0", 15, 600)
            total = _etiqueta("$ 0", 15, 700)
            n.setAlignment(Qt.AlignRight)
            total.setAlignment(Qt.AlignRight)
            tabla.addWidget(n, fila_n, 1)
            tabla.addWidget(total, fila_n, 2)
            self.lbl_metodos[clave] = (n, total)
        tabla.setColumnStretch(0, 1)
        capa.addLayout(tabla)
        self.lbl_anuladas = _etiqueta("", 13, 500, C["texto_2"])
        self.lbl_anuladas.setStyleSheet(
            self.lbl_anuladas.styleSheet()
            + f" background: {C['verde_muy_claro']}; border-radius: 8px; padding: 8px 10px;"
        )
        capa.addWidget(self.lbl_anuladas)
        raiz.addWidget(tarjeta_metodos)

        # Observación y acciones
        acciones = QHBoxLayout()
        acciones.setSpacing(12)
        self.txt_observacion = QLineEdit()
        self.txt_observacion.setPlaceholderText("Observación del cierre (opcional)")
        self.txt_observacion.setMaxLength(200)
        self.txt_observacion.setMinimumHeight(48)
        self.txt_observacion.setStyleSheet(
            f"QLineEdit {{ background: {C['verde_claro']}; border: none; border-radius: 10px;"
            f" padding: 0 14px; font-size: 14px; color: {C['texto']}; }}"
        )
        acciones.addWidget(self.txt_observacion, 1)

        self.btn_actualizar = QPushButton("Actualizar")
        self.btn_actualizar.setMinimumHeight(48)
        self.btn_actualizar.setCursor(Qt.PointingHandCursor)
        self.btn_actualizar.setStyleSheet(
            f"QPushButton {{ background: {C['verde_claro']}; color: {C['texto']};"
            " border: none; border-radius: 10px; padding: 0 20px; font-size: 14px;"
            " font-weight: 700; }"
            f" QPushButton:disabled {{ color: {C['texto_2']}; }}"
        )
        self.btn_actualizar.clicked.connect(self.cargar)
        acciones.addWidget(self.btn_actualizar)

        self.btn_cerrar = QPushButton("Cerrar caja")
        self.btn_cerrar.setMinimumHeight(48)
        self.btn_cerrar.setMinimumWidth(180)
        self.btn_cerrar.setCursor(Qt.PointingHandCursor)
        self.btn_cerrar.setStyleSheet(
            f"QPushButton {{ background: {C['naranja']}; color: {C['texto_naranja']};"
            " border: none; border-radius: 10px; padding: 0 24px; font-size: 15px;"
            " font-weight: 800; }"
            f" QPushButton:disabled {{ background: {C['gris_chip']}; color: {C['gris_texto']}; }}"
        )
        self.btn_cerrar.clicked.connect(self.confirmar_cierre)
        acciones.addWidget(self.btn_cerrar)
        raiz.addLayout(acciones)

        self.lbl_mensaje = QLabel()
        self.lbl_mensaje.setWordWrap(True)
        self.lbl_mensaje.hide()
        raiz.addWidget(self.lbl_mensaje)
        raiz.addStretch()

    # ---------- Datos ----------
    def cargar(self):
        """Pide a la API el resumen del día."""
        self._ocupado(True)
        self._ejecutar(self.servicio.obtener_resumen, self._mostrar_resumen, self._mostrar_error)

    def _mostrar_resumen(self, resumen):
        self.resumen = resumen
        self.lbl_fecha.setText(fecha_larga(resumen.fecha).capitalize())
        self.lbl_total.setText(formato_pesos(resumen.total))
        self.lbl_n_ventas.setText(_plural(resumen.n_ventas, "venta", "ventas"))
        self.lbl_total_canjes.setText(str(resumen.total_canjes))
        for clave, lbl in self.lbl_servicios.items():
            lbl.setText(str(resumen.canjes_por_servicio.get(clave, 0)))
        self.lbl_pedidos.setText(str(resumen.pedidos_web_atendidos))
        for clave, (n, total) in self.lbl_metodos.items():
            conteo = resumen.ventas_por_metodo[clave]
            n.setText(str(conteo.n))
            total.setText(formato_pesos(conteo.total))
        anuladas = resumen.anuladas
        if anuladas.n:
            self.lbl_anuladas.setText(
                f"Anuladas: {_plural(anuladas.n, 'venta', 'ventas')} por"
                f" {formato_pesos(anuladas.total)}. No suman en el total."
            )
        else:
            self.lbl_anuladas.setText("Sin ventas anuladas hoy.")
        if resumen.sin_movimientos:
            self.lbl_n_ventas.setText("Sin registros hoy")
        self._ocupado(False)
        self._estado(resumen.cerrada)  # después: si está cerrada, desactiva el botón
        if not resumen.cerrada:
            self.lbl_mensaje.hide()

    def confirmar_cierre(self):
        """Segundo clic: confirmación de la acción irreversible (RNF-ES08)."""
        if self.resumen is None or self.resumen.cerrada:
            return
        texto = (
            f"Vas a cerrar la caja del {fecha_larga(self.resumen.fecha)}.\n\n"
            f"Total: {formato_pesos(self.resumen.total)}"
            f" ({_plural(self.resumen.n_ventas, 'venta', 'ventas')})\n"
            f"Entregas: {self.resumen.total_canjes}\n\n"
            "Un cierre guardado no se puede editar."
        )
        caja = QMessageBox(self)
        caja.setIcon(QMessageBox.Question)
        caja.setWindowTitle("Cerrar caja")
        caja.setText(texto)
        btn_si = caja.addButton("Sí, cerrar caja", QMessageBox.AcceptRole)
        caja.addButton("Cancelar", QMessageBox.RejectRole)
        caja.setDefaultButton(btn_si)
        caja.exec()
        if caja.clickedButton() is btn_si:
            self.cerrar()

    def cerrar(self):
        self._ocupado(True)
        self._ejecutar(
            self.servicio.cerrar_caja,
            self._cierre_listo,
            self._mostrar_error,
            fecha=self.resumen.fecha,
            observacion=self.txt_observacion.text(),
        )

    def _cierre_listo(self, cierre):
        self._mostrar_resumen(cierre.resumen)
        hora = cierre.creado[11:16] if len(cierre.creado) >= 16 else ""
        detalle = f" a las {hora}" if hora else ""
        self._mensaje(f"✔ Caja cerrada{detalle} por {cierre.cerrado_por}.", exito=True)
        self.caja_cerrada.emit(cierre)

    def _mostrar_error(self, exc):
        self._ocupado(False)
        if self.resumen is not None:
            self._estado(self.resumen.cerrada)
        mensaje = exc.mensaje if isinstance(exc, ErrorCaja) else "Ocurrió un error inesperado."
        if getattr(exc, "codigo", None) == "YA_CERRADA":
            self.cargar()
        self._mensaje(f"⚠ {mensaje}", exito=False)

    # ---------- Apoyo ----------
    def _ejecutar(self, funcion, al_terminar, al_fallar, *args, **kwargs):
        tarea = _Tarea(funcion, *args, **kwargs)
        self._tareas.add(tarea)
        tarea.senales.listo.connect(al_terminar)
        tarea.senales.fallo.connect(al_fallar)
        tarea.senales.listo.connect(lambda _: self._tareas.discard(tarea))
        tarea.senales.fallo.connect(lambda _: self._tareas.discard(tarea))
        tarea.setAutoDelete(False)
        self.pool.start(tarea)

    def _ocupado(self, ocupado):
        self.btn_actualizar.setEnabled(not ocupado)
        self.btn_cerrar.setEnabled(not ocupado)
        if ocupado:
            self.btn_cerrar.setText("Procesando…")
        else:
            self.btn_cerrar.setText("Cerrar caja")

    def _estado(self, cerrada):
        if cerrada:
            texto, fondo, color = "  ● Caja cerrada  ", C["exito_fondo"], C["exito_texto"]
        else:
            texto, fondo, color = "  ● Caja abierta  ", C["verde_claro"], C["texto"]
        self.chip_estado.setText(texto)
        self.chip_estado.setStyleSheet(
            f"background: {fondo}; color: {color}; border-radius: 16px;"
            " padding: 0 10px; font-size: 13px; font-weight: 700;"
        )
        self.btn_cerrar.setEnabled(not cerrada)
        self.txt_observacion.setEnabled(not cerrada)
        if cerrada:
            self.btn_cerrar.setText("Caja cerrada")

    def _mensaje(self, texto, exito):
        fondo = C["exito_fondo"] if exito else C["error_fondo"]
        color = C["exito_texto"] if exito else C["error_borde"]
        self.lbl_mensaje.setText(texto)
        self.lbl_mensaje.setStyleSheet(
            f"background: {fondo}; color: {color}; border-radius: 10px;"
            " padding: 12px 14px; font-size: 14px; font-weight: 600;"
        )
        self.lbl_mensaje.show()


def _plural(n, singular, plural):
    return f"{n} {singular if n == 1 else plural}"
