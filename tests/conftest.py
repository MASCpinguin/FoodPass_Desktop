"""Las pruebas no deben leer el .env del equipo (datos reales de conexión)."""

import os

os.environ["FOODPASS_SIN_ENV"] = "1"
