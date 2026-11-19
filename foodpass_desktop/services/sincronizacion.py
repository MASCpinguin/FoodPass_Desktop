"""Registro diferido: envía al instante o, sin conexión, guarda en la cola.

Un worker (ver temporizador_sync.py) llama a `ciclo()` cada 30 s para vaciar
la cola en lotes de hasta 50 registros.
"""

import threading

from foodpass_desktop.api.errores import ApiError, SinConexionError
from foodpass_desktop.storage.cola import TAMANO_LOTE, TIPOS, ahora_iso, nuevo_uuid

RUTA_LOTE = "/sincronizacion/lote"
ESTADOS_CONFIRMADOS = {"ok", "duplicado"}


def _interpretar(respuesta):
    """Convierte la respuesta del servidor en {uuid: (confirmado, codigo)}.

    SUPUESTO (confirmar con el 05 Contrato de endpoints):
    {"resultados": [{"uuid": "...", "estado": "ok|duplicado|error",
                     "codigo": "..."}]}
    Si el contrato real es distinto, solo se cambia esta función y el
    cuerpo que se envía ({"registros": [...]}).
    """
    resultados = {}
    for r in (respuesta or {}).get("resultados", []):
        confirmado = r.get("estado") in ESTADOS_CONFIRMADOS
        resultados[r.get("uuid")] = (confirmado, r.get("codigo") or r.get("estado"))
    return resultados


class Sincronizador:
    def __init__(self, cola, api):
        self._cola = cola
        self._api = api
        self._ciclo_activo = threading.Lock()

    def registrar(self, tipo, payload):
        """Registra un canje, venta o anulación. Devuelve (uuid, enviado).

        El UUID se crea antes de intentar enviar. Si no hay conexión, el
        registro queda en la cola y se enviará solo. Si el servidor lo
        rechaza (error de negocio), lanza ApiError y NO se encola.
        """
        if tipo not in TIPOS:
            raise ValueError(f"Tipo inválido: {tipo!r}")
        uid = nuevo_uuid()
        creado = ahora_iso()
        registro = {"uuid": uid, "tipo": tipo, "payload": payload, "creado_en": creado}

        # Si ya hay registros esperando, este va detrás de ellos para que
        # una anulación no llegue antes que su venta.
        if self._cola.contar("pendiente") or self._cola.contar("enviando"):
            self._cola.encolar(tipo, payload, uuid_registro=uid, creado_en=creado)
            return uid, False

        try:
            respuesta = self._api.post(RUTA_LOTE, json={"registros": [registro]})
        except SinConexionError:
            self._cola.encolar(tipo, payload, uuid_registro=uid, creado_en=creado)
            return uid, False
        except ApiError as e:
            if e.status and e.status >= 500:
                self._cola.encolar(tipo, payload, uuid_registro=uid, creado_en=creado)
                return uid, False
            raise

        confirmado, codigo = _interpretar(respuesta).get(uid, (False, "SIN_RESPUESTA"))
        if confirmado:
            return uid, True
        raise ApiError(codigo or "RECHAZADO", "El servidor rechazó el registro.")

    def ciclo(self):
        """Envía lotes hasta vaciar la cola o hasta que algo falle.

        Seguro de llamar desde un hilo. Si ya hay un ciclo corriendo, no
        hace nada. Devuelve un resumen: enviados, fallidos, detenido_por.
        """
        resumen = {"enviados": 0, "fallidos": 0, "detenido_por": None}
        if not self._ciclo_activo.acquire(blocking=False):
            resumen["detenido_por"] = "CICLO_EN_CURSO"
            return resumen
        try:
            while True:
                lote = self._cola.tomar_lote(TAMANO_LOTE)
                if not lote:
                    break
                uuids = [r["uuid"] for r in lote]
                try:
                    respuesta = self._api.post(RUTA_LOTE, json={"registros": lote})
                except SinConexionError:
                    # Sin red no es culpa del registro: no suma intento.
                    self._cola.devolver_a_pendiente(
                        uuids, "SIN_CONEXION", contar_intento=False
                    )
                    resumen["detenido_por"] = "SIN_CONEXION"
                    break
                except ApiError as e:
                    sesion_vencida = e.status == 401
                    self._cola.devolver_a_pendiente(
                        uuids, e.codigo, contar_intento=not sesion_vencida
                    )
                    resumen["detenido_por"] = e.codigo
                    break
                except Exception as e:
                    self._cola.devolver_a_pendiente(uuids, repr(e))
                    raise

                resultados = _interpretar(respuesta)
                confirmados = []
                for u in uuids:
                    ok, codigo = resultados.get(u, (False, "SIN_RESPUESTA"))
                    if ok:
                        confirmados.append(u)
                    else:
                        self._cola.devolver_a_pendiente([u], codigo)
                        resumen["fallidos"] += 1
                self._cola.marcar_enviados(confirmados)
                resumen["enviados"] += len(confirmados)
                if not confirmados:
                    resumen["detenido_por"] = "LOTE_RECHAZADO"
                    break
        finally:
            self._ciclo_activo.release()
        return resumen