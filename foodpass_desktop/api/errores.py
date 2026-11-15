"""Errores propios del cliente de la API."""


class ApiError(Exception):
    """El servidor respondió con un error en el formato del contrato.

    Las pantallas deben decidir con `codigo`, no con el texto del mensaje.
    """

    def __init__(self, codigo, mensaje="", datos=None, status=None):
        super().__init__(mensaje or codigo)
        self.codigo = codigo
        self.mensaje = mensaje
        self.datos = datos or {}
        self.status = status


class SinConexionError(Exception):
    """No hubo respuesta a tiempo (timeout o sin red).

    Quien llame debe pasar a registro diferido.
    """