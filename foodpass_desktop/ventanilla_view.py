import sys
import re
from PySide6.QtWidgets import (
    QApplication, QWidget, QVBoxLayout, QHBoxLayout, 
    QPushButton, QLineEdit, QLabel, QFrame, QMessageBox, QListWidget
)
from PySide6.QtCore import Qt, QEvent
from PySide6.QtGui import QShortcut, QKeySequence, QFont

class VentanillaWindow(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("FoodPass - Ventanilla de Priorización (T09)")
        self.resize(700, 600)

        self.selected_service = None
        # Simulación de últimas lecturas para cumplir con la anulación (RF-ES34)
        self.recent_scans = [] 

        self.setup_ui()
        self.setup_shortcuts()

        # Al iniciar, ningún servicio está seleccionado (RF-ES33 / CU-03)
        self.update_input_state()

    def setup_ui(self):
        main_layout = QVBoxLayout(self)

        # --- 1. Selector de Servicio (RF-ES33 / CU-03) ---
        service_layout = QHBoxLayout()
        self.btn_desayuno = QPushButton("Desayuno (F5)")
        self.btn_almuerzo = QPushButton("Almuerzo (F6)")
        self.btn_refrigerio = QPushButton("Refrigerio (F7)")

        for btn, name in [(self.btn_desayuno, "Desayuno"), 
                          (self.btn_almuerzo, "Almuerzo"), 
                          (self.btn_refrigerio, "Refrigerio")]:
            btn.setCheckable(True)
            btn.setFixedHeight(50)
            btn.setFont(QFont("Arial", 11, QFont.Bold))
            btn.clicked.connect(lambda checked, s=name: self.select_service(s))
            service_layout.addWidget(btn)

        main_layout.addLayout(service_layout)

        # --- 2. Campo de Lectura QR / Manual (RF-ES20) ---
        self.input_code = QLineEdit()
        self.input_code.setFixedHeight(45)
        self.input_code.setFont(QFont("Arial", 14))
        self.input_code.setAlignment(Qt.AlignCenter)
        self.input_code.returnPressed.connect(self.process_code)
        main_layout.addWidget(self.input_code)

        # Filtro para asegurar el foco permanente (RF-ES20)
        self.input_code.installEventFilter(self)

        # --- 3. Tarjeta de Resultado Visual en Grande (RF-ES20) ---
        self.card_result = QFrame()
        self.card_result.setFrameShape(QFrame.StyledPanel)
        self.card_result.setFixedHeight(250)
        
        card_layout = QHBoxLayout(self.card_result)
        
        # Recuadro de Foto / Sin Foto (RF-ES20)
        self.lbl_photo = QLabel("Sin foto")
        self.lbl_photo.setFixedSize(120, 150)
        self.lbl_photo.setAlignment(Qt.AlignCenter)
        self.lbl_photo.setStyleSheet("background-color: #cccccc; color: #333333; font-weight: bold; border: 1px solid #999999;")
        card_layout.addWidget(self.lbl_photo)

        # Detalles del aprendiz (Texto ≥ 32px para legibilidad a 2m según RF-ES20)
        details_layout = QVBoxLayout()
        self.lbl_status = QLabel("Seleccione un servicio para comenzar")
        self.lbl_status.setFont(QFont("Arial", 18, QFont.Bold))
        
        self.lbl_info = QLabel("")
        self.lbl_info.setFont(QFont("Arial", 12))

        details_layout.addWidget(self.lbl_status)
        details_layout.addWidget(self.lbl_info)
        card_layout.addLayout(details_layout)

        main_layout.addWidget(self.card_result)

        # --- 4. Historial de Últimas Lecturas para Anulación (RF-ES34) ---
        lbl_history = QLabel("Últimas lecturas (para anulación en < 2 min):")
        lbl_history.setFont(QFont("Arial", 10, QFont.Bold))
        main_layout.addWidget(lbl_history)

        self.list_recent = QListWidget()
        self.list_recent.setFixedHeight(100)
        main_layout.addWidget(self.list_recent)

        btn_annul = QPushButton("Anular lectura seleccionada (RF-ES34)")
        btn_annul.clicked.connect(self.annul_selected_scan)
        main_layout.addWidget(btn_annul)

    def setup_shortcuts(self):
        # Atajos obligatorios F5, F6, F7 para selección rápida de servicio (RF-ES33 / CU-03)[cite: 5, 6]
        QShortcut(QKeySequence(Qt.Key_F5), self, lambda: self.select_service("Desayuno"))
        QShortcut(QKeySequence(Qt.Key_F6), self, lambda: self.select_service("Almuerzo"))
        QShortcut(QKeySequence(Qt.Key_F7), self, lambda: self.select_service("Refrigerio"))
        # Atajo F2 para canje manual (RF-ES21 / CU-05)[cite: 5, 6]
        QShortcut(QKeySequence(Qt.Key_F2), self, lambda: self.input_code.setFocus())

    def select_service(self, service_name):
        self.selected_service = service_name
        
        # Estilos visuales para el botón activo
        style_selected = "background-color: #1b4d3e; color: white; font-weight: bold;"
        style_normal = ""

        self.btn_desayuno.setStyleSheet(style_selected if service_name == "Desayuno" else style_normal)
        self.btn_almuerzo.setStyleSheet(style_selected if service_name == "Almuerzo" else style_normal)
        self.btn_refrigerio.setStyleSheet(style_selected if service_name == "Refrigerio" else style_normal)

        self.update_input_state()

    def update_input_state(self):
        # Si no hay servicio elegido, el campo de lectura se bloquea (RF-ES33 / CU-03)[cite: 5, 6]
        if not self.selected_service:
            self.input_code.setEnabled(False)
            self.input_code.setPlaceholderText("«Elige un servicio» (Usa F5, F6 o F7)")
        else:
            self.input_code.setEnabled(True)
            self.input_code.setPlaceholderText(f"Escanea QR o digita documento para {self.selected_service}...")
            self.input_code.setFocus()

    def eventFilter(self, obj, event):
        # Mantiene el foco permanentemente en el campo de lectura (RF-ES20)[cite: 5]
        if obj == self.input_code and event.type() == QEvent.FocusOut:
            if self.selected_service and self.input_code.isEnabled():
                self.input_code.setFocus()
        return super().eventFilter(obj, event)

    def process_code(self):
        code = self.input_code.text().strip()
        self.input_code.clear()

        # Validación del contenido del QR (debe ser numérico de 1 a 10 dígitos según C-03 y CU-04)[cite: 5, 6]
        if not re.fullmatch(r"\d{1,10}", code):
            self.show_result("CÓDIGO NO RECONOCIDO", "El código leído no es un ID válido.", "#d9534f", "Sin foto")
            return

        # Simulación de validación de reglas de negocio para la demo de la Parte 1
        last_digit = int(code[-1])
        if last_digit % 3 == 0:
            # Estado Exitoso: Entregado (RF-ES17 / CU-04)[cite: 5, 6]
            status_title = "ENTREGADO"
            details = f"Servicio: {self.selected_service}\nNombre: Marco Antonio Angulo\nDocumento: {code}\nPrograma: ADSO (Ficha 3173467)"
            bg_color = "#5cb85c" # Verde
            
            # Registrar en las últimas lecturas para permitir anulación (RF-ES34)[cite: 5]
            self.recent_scans.insert(0, f"Doc: {code} - {self.selected_service} (Válido)")
            self.list_recent.clear()
            self.list_recent.addItems(self.recent_scans)

        elif last_digit % 3 == 1:
            # Estado de conflicto: Ya recibió hoy (CU-04 A1)[cite: 6]
            status_title = "YA RECIBIÓ HOY"
            details = f"El aprendiz ya reclamó beneficio hoy.\nServicio anterior: Almuerzo\nHora: 12:15 PM"
            bg_color = "#d9534f" # Rojo
        else:
            # Estado de error: No es beneficiario / Inactivo (CU-04 A2)[cite: 6]
            status_title = "NO ES BENEFICIARIO"
            details = f"Documento: {code}\nEl usuario no se encuentra activo en la base del SENA."
            bg_color = "#d9534f" # Rojo

        self.show_result(status_title, details, bg_color, "Sin foto")

    def show_result(self, title, details, bg_color, photo_text):
        self.card_result.setStyleSheet(f"background-color: {bg_color}; color: white; border-radius: 8px;")
        self.lbl_status.setText(title)
        self.lbl_info.setText(details)
        self.lbl_photo.setText(photo_text)

    def annul_selected_scan(self):
        # Funcionalidad de anulación solicitada en RF-ES34[cite: 5]
        selected_item = self.list_recent.currentItem()
        if not selected_item:
            QMessageBox.warning(self, "Aviso", "Selecciona una lectura reciente de la lista para anular.")
            return
        
        row = self.list_recent.row(selected_item)
        self.list_recent.takeItem(row)
        self.recent_scans.pop(row)
        QMessageBox.information(self, "Anulación Exitosa", "El canje ha sido anulado correctamente y se liberó el beneficio (RF-ES34).")

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = VentanillaWindow()
    window.show()
    sys.exit(app.exec())