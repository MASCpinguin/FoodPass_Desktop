"""Almacén seguro de credenciales (RF-ES25).

El token y el PIN se guardan en el almacén de credenciales del sistema
operativo (en Windows, el Administrador de credenciales) mediante `keyring`.
Nunca se escriben en archivos de texto.
"""

import logging

SERVICIO = "FoodPass Escritorio"

log = logging.getLogger(__name__)


class AlmacenKeyring:
    """Guarda pares clave/valor en el almacén de credenciales del sistema."""

    def __init__(self, servicio=SERVICIO):
        import keyring  # import diferido: las pruebas no lo necesitan

        self._keyring = keyring
        self._servicio = servicio

    def leer(self, clave):
        return self._keyring.get_password(self._servicio, clave)

    def guardar(self, clave, valor):
        self._keyring.set_password(self._servicio, clave, valor)

    def borrar(self, clave):
        try:
            self._keyring.delete_password(self._servicio, clave)
        except self._keyring.errors.PasswordDeleteError:
            pass  # no existía: no hay nada que borrar


class AlmacenMemoria:
    """Almacén en memoria. Para pruebas o equipos sin almacén de credenciales.

    Lo guardado se pierde al cerrar la aplicación.
    """

    def __init__(self):
        self._datos = {}

    def leer(self, clave):
        return self._datos.get(clave)

    def guardar(self, clave, valor):
        self._datos[clave] = valor

    def borrar(self, clave):
        self._datos.pop(clave, None)


def crear_almacen():
    """Devuelve el almacén del sistema; si no hay ninguno, uno en memoria.

    En Windows siempre existe. El respaldo en memoria evita que la app se caiga
    en equipos Linux sin llavero (por ejemplo, el servidor de integración).
    """
    try:
        almacen = AlmacenKeyring()
        almacen.leer("prueba")
        return almacen
    except Exception as e:  # keyring ausente o sin backend
        log.warning("Sin almacén de credenciales (%s); se usa memoria.", e)
        return AlmacenMemoria()
