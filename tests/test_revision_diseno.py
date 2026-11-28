"""Revisión de diseño (28 nov): indicador de conexión con la API, títulos de
la tarjeta de la ventanilla, botón «Anular» con cuenta regresiva y detalles
de Beneficiarios y del Resumen.

Corren sin monitor (QT_QPA_PLATFORM=offscreen) y sin base de datos.
"""

import os

import pytest

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
try:
    from PySide6 import QtWidgets
except ImportError as e:
    pytest.skip(f"Qt no disponible en este equipo: {e}", allow_module_level=True)

from foodpass_desktop.api.cliente import ClienteApi  # noqa: E402
from foodpass_desktop.services.canje_service import ResultadoCanje  # noqa: E402
from foodpass_desktop.ui import ventana_principal as vp  # noqa: E402
from foodpass_desktop.ui.beneficiarios_view import (  # noqa: E402
    BeneficiariosView,
    DialogoBeneficiario,
)
from foodpass_desktop.ui.panel_view import (  # noqa: E402
    MENSAJE_API_CAIDA,
    calcular_alertas,
)
from foodpass_desktop.ui.reporte_view import fecha_legible  # noqa: E402
from foodpass_desktop.ui.ventanilla_view import VentanillaView  # noqa: E402
from foodpass_desktop.ui.widgets.tarjeta_resultado import (  # noqa: E402
    TarjetaResultado,
    titulo_codigo_rechazado,
)


@pytest.fixture(scope="module")
def app():
    try:
        return QtWidgets.QApplication.instance() or QtWidgets.QApplication([])
    except Exception as e:  # pragma: no cover - depende del equipo
        pytest.skip(f"Qt no disponible: {e}")


# --- conexión con la API ---------------------------------------------------
def test_api_apagada_no_es_alcanzable():
    # Puerto 9 (discard) en local: nadie escucha, la conexión se rechaza.
    assert ClienteApi("http://127.0.0.1:9/api").alcanzable(timeout=1) is False


class ApiFalsa:
    def __init__(self, viva=True):
        self.viva = viva

    def alcanzable(self, timeout=2):
        return self.viva


def test_indicador_avisa_si_la_api_se_cae(app):
    ventana = vp.VentanaPrincipal(operador={"nombre": "Op"}, usar_bd=False)
    ventana._conexion_probada((True, True))
    assert ventana.texto_conexion.text() == "Conectado"
    assert ventana.detalle_conexion.isHidden()

    ventana._conexion_probada((True, False))
    assert ventana.texto_conexion.text() == "API sin conexión"
    assert ventana.detalle_conexion.text() == "No cierres sesión"
    assert ventana.marco_conexion.property("estado") == "parcial"
    textos = [
        ventana.panel.caja_alertas.itemAt(i).widget().text()
        for i in range(ventana.panel.caja_alertas.count())
    ]
    assert MENSAJE_API_CAIDA in textos

    ventana._conexion_probada((True, True))
    assert ventana.texto_conexion.text() == "Conectado"


def test_sin_base_de_datos_manda_sobre_la_api(app):
    ventana = vp.VentanaPrincipal(operador={"nombre": "Op"}, usar_bd=False)
    ventana._conexion_probada((False, False))
    assert ventana.texto_conexion.text() == "Sin conexión"
    assert ventana.marco_conexion.property("estado") == "sin_conexion"


def test_probar_todo_consulta_la_api(app, monkeypatch):
    monkeypatch.setattr(vp.bd, "probar", lambda: True)
    ventana = vp.VentanaPrincipal(
        operador={"nombre": "Op"}, usar_bd=False, api=ApiFalsa(viva=False)
    )
    assert ventana._probar_todo() == (True, False)


def test_alerta_de_api_en_el_panel():
    assert ("advertencia", MENSAJE_API_CAIDA) in calcular_alertas(
        None, True, api_conectada=False
    )
    assert calcular_alertas(None, True, api_conectada=True) == []


# --- tarjeta de la ventanilla ------------------------------------------------
@pytest.mark.parametrize(
    "mensaje, titulo",
    [
        ("Este código ya fue usado o fue reemplazado por uno nuevo", "CÓDIGO YA USADO"),
        ("El código venció (vence a medianoche)", "CÓDIGO VENCIDO"),
        ("Código no encontrado", "CÓDIGO NO ENCONTRADO"),
        ("No es un código de FoodPass.", "CÓDIGO NO RECONOCIDO"),
    ],
)
def test_titulo_segun_el_motivo(mensaje, titulo):
    assert titulo_codigo_rechazado(mensaje) == titulo


def test_codigo_rechazado_sin_raya_gigante(app):
    tarjeta = TarjetaResultado()
    tarjeta.mostrar_resultado("no_reconocido", {"mensaje": "El código venció"})
    assert tarjeta.lbl_estado_titulo.text() == "CÓDIGO VENCIDO"
    assert tarjeta.lbl_nombre.isHidden()
    assert tarjeta.lbl_estado_icono.property("estado") == "no_reconocido"
    tarjeta.limpiar()
    assert not tarjeta.lbl_nombre.isHidden()


class CanjeFalso:
    def es_codigo_valido(self, _texto):
        return True


def test_boton_anular_dice_a_quien_y_cuanto_queda(app):
    vista = VentanillaView(servicio_canje=CanjeFalso())
    vista.seleccionar_servicio("Almuerzo")
    vista._al_completar_canje(
        ResultadoCanje(
            tipo="entregado",
            datos={"nombre": "Mateo Rodríguez", "canje_id": 7, "servicio": "Almuerzo"},
        )
    )
    texto = vista.btn_anular.text()
    assert texto.startswith("Anular canje de Mateo")
    assert texto.endswith(("2:00", "1:59"))
    vista._vencer_anulacion()
    assert vista.btn_anular.isHidden()
    assert not vista.timer_cuenta_anular.isActive()


def test_falla_de_registro_queda_en_ultimas_lecturas(app):
    vista = VentanillaView(servicio_canje=CanjeFalso())
    vista.seleccionar_servicio("Almuerzo")
    vista._entrada_actual = "FP-A1B2C3"
    vista._al_fallar_canje(Exception("caída"))
    assert vista._lecturas[0][1] == "No se registró"
    assert vista.tarjeta.lbl_estado_titulo.text() == "NO SE REGISTRÓ"


# --- beneficiarios y resumen ---------------------------------------------------
def test_estado_del_beneficiario_con_mayuscula_pero_se_guarda_en_minuscula(app):
    dialogo = DialogoBeneficiario({"id": 1, "estado": "inactivo"})
    assert dialogo.estado.currentText() == "Inactivo"
    assert dialogo.datos()["estado"] == "inactivo"


def test_busqueda_sin_resultados_lo_dice(app):
    vista = BeneficiariosView()
    vista._cargado(
        [
            {
                "id": 1,
                "numero_documento": "1001001100",
                "nombre_completo": "Ana Gómez",
                "email": "ana@soy.sena.edu.co",
                "estado": "activo",
            }
        ]
    )
    vista.buscar.setText("zzzz")
    assert not vista.lbl_vacio.isHidden()
    assert "No hay beneficiarios que coincidan" in vista.lbl_vacio.text()
    vista.buscar.setText("")
    assert vista.lbl_vacio.isHidden()
    assert vista.lbl_pagina.text().startswith("1 resultado ·")


def test_fecha_legible_en_espanol():
    assert fecha_legible("2026-11-28") == "Sábado 28 de noviembre de 2026"
    assert fecha_legible("no-es-fecha") == "Día no-es-fecha"


# --- motivo de anulación en `detalle` ---------------------------------------------
class CursorFalso:
    def __init__(self, registro):
        self.registro = registro
        self.rowcount = 1

    def __enter__(self):
        return self

    def __exit__(self, *_):
        return False

    def execute(self, sql, params):
        self.registro.append((sql, params))


class ConexionFalsa:
    def __init__(self):
        self.consultas = []

    def __enter__(self):
        return self

    def __exit__(self, *_):
        return False

    def cursor(self):
        return CursorFalso(self.consultas)

    def commit(self):
        pass


def test_anular_guarda_el_motivo_en_detalle():
    from datetime import datetime

    from foodpass_desktop.storage.consultas_bd import anular_canje

    conexion = ConexionFalsa()
    ahora = datetime(2026, 11, 28, 12, 0)
    ok, _ = anular_canje(
        7, ahora, "Servicio equivocado", conectar=lambda: conexion, ahora=ahora
    )
    assert ok
    sql, params = conexion.consultas[0]
    assert "detalle = LEFT(CONCAT(COALESCE(detalle, ''), %s), 255)" in sql
    assert params == (" · Anulado: Servicio equivocado", 7)


def test_la_ventanilla_manda_el_motivo_elegido(app, monkeypatch):
    from datetime import datetime

    from foodpass_desktop.ui import ventanilla_view as vv

    llamadas = []

    class Canje(CanjeFalso):
        def anular(self, canje_id, registrado_en, motivo=None):
            llamadas.append((canje_id, motivo))
            return True, "Canje anulado."

    class DialogoQueAcepta(vv.DialogoAnular):
        def exec(self):
            self.combo.setCurrentText("Servicio equivocado")
            return QtWidgets.QDialog.DialogCode.Accepted

    monkeypatch.setattr(vv, "DialogoAnular", DialogoQueAcepta)
    monkeypatch.setattr(
        vv,
        "ejecutar_en_segundo_plano",
        lambda f, *a, al_exito=None, al_error=None: al_exito(f(*a)),
    )
    vista = VentanillaView(servicio_canje=Canje())
    vista._ultimo_canje = {
        "canje_id": 7,
        "registrado_en": datetime.now(),
        "nombre": "Mateo Rodríguez",
        "servicio": "Almuerzo",
    }
    vista.anular_ultimo()
    assert llamadas == [(7, "Servicio equivocado")]


def test_nombre_largo_baja_de_tamano_y_no_se_monta(app):
    tarjeta = TarjetaResultado()
    tarjeta.resize(516, 330)  # ventana de 1200 × 700
    tarjeta.show()
    tarjeta.mostrar_resultado(
        "entregado", {"nombre": "Juan Pérez", "servicio": "Almuerzo"}
    )
    assert tarjeta._tamano_nombre == 32
    tarjeta.mostrar_resultado(
        "entregado",
        {
            "nombre": "María Fernanda de los Ángeles Castañeda Villamizar",
            "servicio": "Almuerzo",
        },
    )
    assert tarjeta._tamano_nombre < 32
    assert (
        tarjeta.lbl_nombre.minimumHeight()
        >= tarjeta.lbl_nombre.heightForWidth(tarjeta.lbl_nombre.width()) - 8
    )
    assert tarjeta.recuadro_foto.width() == 150  # modo compacto
    assert " OK" in tarjeta.lbl_estado_titulo.text()
