"""Componentes básicos que comparten los módulos de FoodPass."""
from PySide6.QtWidgets import QFrame, QLineEdit, QPushButton, QVBoxLayout


class BotonPrincipal(QPushButton):
    def __init__(self, texto="", parent=None):
        super().__init__(texto, parent)
        self.setProperty("variante", "principal")
        self.setMinimumHeight(44)


class BotonSecundario(QPushButton):
    def __init__(self, texto="", parent=None):
        super().__init__(texto, parent)
        self.setProperty("variante", "secundario")
        self.setMinimumHeight(44)


class CampoTexto(QLineEdit):
    def __init__(self, placeholder="", parent=None):
        super().__init__(parent)
        self.setPlaceholderText(placeholder)
        self.setMinimumHeight(44)


class Tarjeta(QFrame):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("tarjeta")
        contenido = QVBoxLayout(self)
        contenido.setContentsMargins(20, 20, 20, 20)
        contenido.setSpacing(12)
