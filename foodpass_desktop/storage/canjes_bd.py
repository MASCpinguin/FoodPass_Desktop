"""Registro de canjes directo en MySQL (C2.2-04).

Reglas que aplica este módulo (la API no las aplica):
- RN01: un beneficiario recibe un solo servicio al día. Se revisa antes de
  insertar y, además, la clave única (usuario_id, periodo) de la tabla canjes
  rechaza el segundo registro aunque lleguen dos lecturas al mismo tiempo.
- RN04: solo recibe quien está activo en beneficiarios_sena (por documento
  o, como hace la web, por correo).
- El QR se marca como usado al entregar.

Códigos que acepta (se trabaja con lo que ya generan la web y el móvil):
- "web":   QR de la web Laravel, guardado en canjes.codigo_qr ("FP-QR-…" o "FP-…").
- "movil": código corto del móvil, qr_tokens.code ("FP-XXXXXX").
- "token": token de 64 caracteres del móvil, qr_tokens.token.

Cada método devuelve (tipo, datos) con los tipos que entiende la tarjeta de
resultado: entregado, ya_recibio, no_beneficiario, no_reconocido, error_conexion.
"""

from datetime import datetime, timedelta, timezone

import pymysql

from foodpass_desktop.storage import bd

# Colombia no tiene horario de verano: UTC-5 todo el año.
BOGOTA = timezone(timedelta(hours=-5), "America/Bogota")


def ahora_bogota() -> datetime:
    return datetime.now(BOGOTA)


def hoy_bogota() -> str:
    """Día del beneficio (RN12) en formato AAAA-MM-DD, que se guarda en periodo."""
    return ahora_bogota().date().isoformat()


class _Resultado(Exception):
    """Corta la transacción y devuelve un resultado a la ventanilla."""

    def __init__(self, tipo, datos=None):
        super().__init__(tipo)
        self.tipo = tipo
        self.datos = datos or {}


class CanjesBD:
    def __init__(self, conectar=bd.conexion):
        self._conectar = conectar
        self._tiene_servicio = None  # se averigua una vez por sesión

    # ------------------------------------------------------------------ API
    def canjear_codigo(self, servicio: str, tipo_codigo: str, codigo: str):
        """Canje por QR o código del móvil (RF-ES17)."""
        return self._ejecutar(self._canje_codigo, servicio, tipo_codigo, codigo)

    def canjear_documento(self, servicio: str, documento: str, motivo: str):
        """Canje manual por documento con F2 (RF-ES21)."""
        return self._ejecutar(self._canje_documento, servicio, documento, motivo)

    # ------------------------------------------------------------ interno
    def _ejecutar(self, funcion, *args):
        try:
            with self._conectar() as conn:
                try:
                    with conn.cursor() as cur:
                        resultado = funcion(cur, *args)
                    conn.commit()
                    return resultado
                except _Resultado as r:
                    conn.rollback()
                    return r.tipo, r.datos
                except pymysql.err.IntegrityError as err:
                    conn.rollback()
                    # 1062 = clave duplicada: otra lectura ganó la carrera.
                    if err.args and err.args[0] == 1062:
                        return "ya_recibio", {
                            "servicio": "un servicio",
                            "hora": "hace un momento",
                        }
                    raise
        except pymysql.err.OperationalError:
            return "error_conexion", {
                "mensaje": "No hay conexión con la base de datos de FoodPass."
            }

    def _canje_codigo(self, cur, servicio, tipo_codigo, codigo):
        ahora = ahora_bogota().replace(tzinfo=None)

        if tipo_codigo == "web":
            cur.execute(
                "SELECT id, usuario_id, estado, expira_en FROM canjes "
                "WHERE codigo_qr = %s FOR UPDATE",
                (codigo,),
            )
            fila = cur.fetchone()
            if not fila:
                raise _Resultado(
                    "no_reconocido", {"mensaje": "Código QR no encontrado en FoodPass"}
                )
            if fila["estado"] != "pendiente":
                raise _Resultado(
                    "no_reconocido", {"mensaje": "Este código QR ya fue usado"}
                )
            if fila["expira_en"] and fila["expira_en"] <= ahora:
                raise _Resultado(
                    "no_reconocido",
                    {"mensaje": "El código QR venció (vence a medianoche)"},
                )
            return self._entregar(
                cur, fila["usuario_id"], servicio, "qr", canje_web_id=fila["id"]
            )

        columna = "code" if tipo_codigo == "movil" else "token"
        cur.execute(
            f"SELECT id, usuario_id, expires_at, usado FROM qr_tokens "
            f"WHERE {columna} = %s ORDER BY id DESC LIMIT 1 FOR UPDATE",
            (codigo,),
        )
        fila = cur.fetchone()
        if not fila:
            raise _Resultado(
                "no_reconocido", {"mensaje": "Código no encontrado en FoodPass"}
            )
        if fila["usado"]:
            raise _Resultado(
                "no_reconocido",
                {"mensaje": "Este código ya fue usado o fue reemplazado por uno nuevo"},
            )
        if fila["expires_at"] and fila["expires_at"] <= ahora:
            raise _Resultado(
                "no_reconocido", {"mensaje": "El código venció (vence a medianoche)"}
            )
        return self._entregar(
            cur, fila["usuario_id"], servicio, "qr", qr_token_id=fila["id"]
        )

    def _canje_documento(self, cur, servicio, documento, motivo):
        cur.execute(
            "SELECT id FROM usuarios WHERE documento = %s ORDER BY id LIMIT 1",
            (documento,),
        )
        fila = cur.fetchone()
        if not fila:
            cur.execute(
                "SELECT id FROM beneficiarios_sena WHERE numero_documento = %s AND activo = 1 LIMIT 1",
                (documento,),
            )
            if cur.fetchone():
                # La tabla canjes exige usuario: sin cuenta no hay canje.
                raise _Resultado(
                    "no_beneficiario",
                    {"mensaje": "Es beneficiario pero no tiene cuenta en FoodPass"},
                )
            raise _Resultado("no_beneficiario")
        return self._entregar(cur, fila["id"], servicio, "manual", motivo=motivo)

    def _entregar(
        self,
        cur,
        usuario_id,
        servicio,
        modalidad,
        canje_web_id=None,
        qr_token_id=None,
        motivo="",
    ):
        # 1. Usuario activo
        cur.execute(
            "SELECT id, nombre, documento, email, activo FROM usuarios WHERE id = %s",
            (usuario_id,),
        )
        usuario = cur.fetchone()
        if not usuario or not usuario["activo"]:
            raise _Resultado("no_beneficiario")

        # 2. Beneficiario activo (RN04): por documento o por correo, como la web
        cur.execute(
            "SELECT id FROM beneficiarios_sena WHERE activo = 1 AND "
            "((numero_documento = %s AND numero_documento <> '') OR LOWER(email) = LOWER(%s)) "
            "ORDER BY id LIMIT 1",
            (usuario["documento"] or "", usuario["email"] or ""),
        )
        beneficiario = cur.fetchone()
        if not beneficiario:
            raise _Resultado("no_beneficiario")

        # 3. Un servicio al día (RN01)
        hoy = hoy_bogota()
        tiene_servicio = self._columna_servicio(cur)
        columnas = (
            "servicio, detalle, actualizado_en"
            if tiene_servicio
            else "detalle, actualizado_en"
        )
        cur.execute(
            f"SELECT {columnas} FROM canjes WHERE usuario_id = %s AND periodo = %s "
            "AND estado = 'entregado' LIMIT 1 FOR UPDATE",
            (usuario_id, hoy),
        )
        previo = cur.fetchone()
        if previo:
            raise _Resultado(
                "ya_recibio",
                {
                    "nombre": usuario["nombre"],
                    "documento": usuario["documento"] or "",
                    "servicio": _servicio_de(previo),
                    "hora": previo["actualizado_en"].strftime("%I:%M %p")
                    if previo["actualizado_en"]
                    else "",
                },
            )

        # 4. Registrar
        servicio_bd = servicio.lower()
        detalle = f"Escritorio · {servicio} · {'Manual: ' + motivo if modalidad == 'manual' else 'QR'}"[
            :255
        ]

        if canje_web_id:
            sets = "estado = 'entregado', periodo = %s, fecha_canje = %s, beneficiario_sena_id = %s, detalle = %s"
            valores = [hoy, hoy, beneficiario["id"], detalle]
            if tiene_servicio:
                sets += ", servicio = %s"
                valores.append(servicio_bd)
            cur.execute(
                f"UPDATE canjes SET {sets} WHERE id = %s", (*valores, canje_web_id)
            )
        else:
            cur.execute("SELECT id FROM restaurantes ORDER BY id LIMIT 1")
            restaurante = cur.fetchone()
            columnas = "usuario_id, beneficiario_sena_id, restaurante_id, monto, fecha_canje, periodo, estado, detalle"
            marcas = "%s, %s, %s, 0, %s, %s, 'entregado', %s"
            valores = [
                usuario_id,
                beneficiario["id"],
                restaurante["id"] if restaurante else 1,
                hoy,
                hoy,
                detalle,
            ]
            if tiene_servicio:
                columnas += ", servicio"
                marcas += ", %s"
                valores.append(servicio_bd)
            cur.execute(f"INSERT INTO canjes ({columnas}) VALUES ({marcas})", valores)

        if qr_token_id:
            cur.execute("UPDATE qr_tokens SET usado = 1 WHERE id = %s", (qr_token_id,))

        return "entregado", {
            "nombre": usuario["nombre"],
            "documento": usuario["documento"] or "",
            "foto_url": None,
            "servicio": servicio,
            "hora": ahora_bogota().strftime("%I:%M %p"),
            "modalidad": modalidad,
        }

    def _columna_servicio(self, cur) -> bool:
        """La columna servicio llega con sql/C22_04_escritorio.sql; si falta, se usa detalle."""
        if self._tiene_servicio is None:
            cur.execute("SHOW COLUMNS FROM canjes LIKE 'servicio'")
            self._tiene_servicio = cur.fetchone() is not None
        return self._tiene_servicio


def _servicio_de(fila) -> str:
    if fila.get("servicio"):
        return str(fila["servicio"]).capitalize()
    detalle = fila.get("detalle") or ""
    for nombre in ("Desayuno", "Almuerzo", "Refrigerio"):
        if nombre in detalle:
            return nombre
    return "un servicio"
