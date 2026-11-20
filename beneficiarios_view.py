from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QApplication,
    QComboBox,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
    QWidget,
)

from beneficiarios_service import COLUMNAS
from filtrar_beneficiarios import filtrar_beneficiarios


class BeneficiariosView(QWidget):
    def __init__(self, beneficiarios: list[dict] | None = None, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Beneficiarios - Lista, búsqueda y filtros")
        self.resize(900, 500)
        self._beneficiarios = beneficiarios or []
        self._init_ui()
        self._cargar_programas()
        self._actualizar_tabla()

    def _init_ui(self):
        layout_principal = QVBoxLayout(self)

        # Fila de búsqueda y filtros
        layout_filtros = QHBoxLayout()

        self.txt_busqueda = QLineEdit()
        self.txt_busqueda.setPlaceholderText("Buscar por documento o nombre...")
        self.txt_busqueda.textChanged.connect(self._actualizar_tabla)

        self.cmb_estado = QComboBox()
        self.cmb_estado.addItems(["todos", "activo", "inactivo"])
        self.cmb_estado.currentTextChanged.connect(self._actualizar_tabla)

        self.cmb_programa = QComboBox()
        self.cmb_programa.addItem("todos")
        self.cmb_programa.currentTextChanged.connect(self._actualizar_tabla)

        layout_filtros.addWidget(QLabel("Buscar:"))
        layout_filtros.addWidget(self.txt_busqueda)
        layout_filtros.addWidget(QLabel("Estado:"))
        layout_filtros.addWidget(self.cmb_estado)
        layout_filtros.addWidget(QLabel("Programa:"))
        layout_filtros.addWidget(self.cmb_programa)

        layout_principal.addLayout(layout_filtros)

        # Contador de registros visibles
        self.lbl_contador = QLabel("Mostrando 0 beneficiarios")
        layout_principal.addWidget(self.lbl_contador)

        # Tabla con las columnas de beneficiarios_service.py
        self.tabla = QTableWidget(0, len(COLUMNAS))
        self.tabla.setHorizontalHeaderLabels(COLUMNAS)
        self.tabla.setSelectionBehavior(QTableWidget.SelectRows)
        layout_principal.addWidget(self.tabla)

    def set_beneficiarios(self, beneficiarios: list[dict]):
        self._beneficiarios = beneficiarios or []
        self._cargar_programas()
        self._actualizar_tabla()

    def _cargar_programas(self):
        programa_actual = self.cmb_programa.currentText()
        programas = sorted(
            {
                str(b.get("programa", "")).strip()
                for b in self._beneficiarios
                if str(b.get("programa", "")).strip()
            }
        )
        self.cmb_programa.blockSignals(True)
        self.cmb_programa.clear()
        self.cmb_programa.addItem("todos")
        self.cmb_programa.addItems(programas)
        indice = self.cmb_programa.findText(programa_actual)
        self.cmb_programa.setCurrentIndex(indice if indice >= 0 else 0)
        self.cmb_programa.blockSignals(False)

    def _actualizar_tabla(self):
        datos_filtrados = filtrar_beneficiarios(
            self._beneficiarios,
            texto_busqueda=self.txt_busqueda.text(),
            estado=self.cmb_estado.currentText(),
            programa=self.cmb_programa.currentText(),
        )

        self.tabla.setRowCount(len(datos_filtrados))
        for fila, beneficiario in enumerate(datos_filtrados):
            for col, nombre_col in enumerate(COLUMNAS):
                valor = str(beneficiario.get(nombre_col, ""))
                item = QTableWidgetItem(valor)
                item.setFlags(item.flags() & ~Qt.ItemIsEditable)
                self.tabla.setItem(fila, col, item)

        self.lbl_contador.setText(f"Mostrando {len(datos_filtrados)} beneficiarios")


if __name__ == "__main__":
    import sys

    datos_prueba = [
        {
            "tipo_documento": "CC",
            "numero_documento": "1001",
            "nombre_completo": "Ana Maria Lopez",
            "programa": "ADSO",
            "ficha": "2857123",
            "estado": "activo",
        },
        {
            "tipo_documento": "CC",
            "numero_documento": "1002",
            "nombre_completo": "Carlos Perez",
            "programa": "Sistemas",
            "ficha": "2857124",
            "estado": "inactivo",
        },
    ]

    app = QApplication(sys.argv)
    ventana = BeneficiariosView(datos_prueba)
    ventana.show()
    sys.exit(app.exec())