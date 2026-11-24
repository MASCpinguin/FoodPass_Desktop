"""Consultas directas a foodpass_v2 (C2.2-04): rol, panel, resumen, reportes,
anulación de canjes y beneficiarios.

Todas abren y cierran su propia conexión (storage/bd.py) y devuelven datos
simples (dict / list) para que las pantallas no conozcan SQL.
"""

from datetime import date, timedelta

import pymysql

from foodpass_desktop.storage import bd
from foodpass_desktop.storage.canjes_bd import ahora_bogota, hoy_bogota

ROLES_PERMITIDOS = ("operador_restaurante", "restaurante", "tecnico", "admin")
SERVICIOS = ("desayuno", "almuerzo", "refrigerio")
MINUTOS_ANULACION = 2
MAX_DIAS_REPORTE = 93


def _servicio_de(fila):
    if fila.get("servicio"):
        return str(fila["servicio"]).lower()
    detalle = (fila.get("detalle") or "").lower()
    for s in SERVICIOS:
        if s in detalle:
            return s
    return "almuerzo"


def _modalidad_de(fila):
    return "manual" if "manual" in (fila.get("detalle") or "").lower() else "qr"


def _tiene_columna_servicio(cur):
    cur.execute("SHOW COLUMNS FROM canjes LIKE 'servicio'")
    return cur.fetchone() is not None


# --------------------------------------------------------------- acceso
def rol_permitido(usuario_id, conectar=bd.conexion):
    """RN16: solo entran los roles de cafetería y admin."""
    with conectar() as conn, conn.cursor() as cur:
        cur.execute(
            "SELECT LOWER(r.nombre) AS rol FROM rol_usuario ru "
            "JOIN roles r ON r.id = ru.rol_id WHERE ru.usuario_id = %s",
            (usuario_id,),
        )
        roles = {f["rol"] for f in cur.fetchall()}
    return bool(roles & set(ROLES_PERMITIDOS))


# ------------------------------------------------------ canjes del día
def _canjes_de(cur, desde, hasta):
    columnas = "c.id, c.estado, c.detalle, c.actualizado_en, c.fecha_canje, u.nombre, u.documento"
    if _tiene_columna_servicio(cur):
        columnas += ", c.servicio"
    cur.execute(
        f"SELECT {columnas} FROM canjes c JOIN usuarios u ON u.id = c.usuario_id "
        "WHERE c.fecha_canje BETWEEN %s AND %s AND c.estado IN ('entregado','rechazado') "
        "AND c.detalle LIKE 'Escritorio%%' ORDER BY c.actualizado_en, c.id",
        (desde, hasta),
    )
    return cur.fetchall()


def resumen_dia(fecha=None, conectar=bd.conexion):
    """RF-ES05 y RF-ES01: entregas por servicio y modalidad, anulados y total."""
    fecha = fecha or hoy_bogota()
    with conectar() as conn, conn.cursor() as cur:
        filas = _canjes_de(cur, fecha, fecha)
    por_servicio = {s: 0 for s in SERVICIOS}
    por_modalidad = {"qr": 0, "manual": 0}
    anulados = 0
    for f in filas:
        if f["estado"] == "rechazado":
            anulados += 1
            continue
        por_servicio[_servicio_de(f)] += 1
        por_modalidad[_modalidad_de(f)] += 1
    return {
        "fecha": fecha,
        "por_servicio": por_servicio,
        "por_modalidad": por_modalidad,
        "anulados": anulados,
        "total": sum(por_servicio.values()),
    }


def reporte_entregas(desde, hasta, servicio=None, conectar=bd.conexion):
    """RF-ES24: detalle de entregas con totales por servicio (máx. 93 días)."""
    d1 = date.fromisoformat(str(desde))
    d2 = date.fromisoformat(str(hasta))
    if d2 < d1:
        raise ValueError("La fecha final es anterior a la inicial.")
    if (d2 - d1).days + 1 > MAX_DIAS_REPORTE:
        raise ValueError(f"El rango máximo es de {MAX_DIAS_REPORTE} días.")
    with conectar() as conn, conn.cursor() as cur:
        filas = _canjes_de(cur, d1.isoformat(), d2.isoformat())
    detalle = []
    totales = {s: 0 for s in SERVICIOS}
    for f in filas:
        if f["estado"] != "entregado":
            continue
        s = _servicio_de(f)
        if servicio and s != servicio.lower():
            continue
        totales[s] += 1
        momento = f["actualizado_en"]
        detalle.append(
            {
                "fecha_hora": momento.strftime("%Y-%m-%d %H:%M:%S")
                if momento
                else str(f["fecha_canje"]),
                "documento": f["documento"] or "",
                "nombre": f["nombre"],
                "servicio": s.capitalize(),
                "modalidad": "Manual" if _modalidad_de(f) == "manual" else "Código",
            }
        )
    return {
        "desde": d1.isoformat(),
        "hasta": d2.isoformat(),
        "servicio": servicio.capitalize() if servicio else None,
        "detalle": detalle,
        "totales": totales,
        "total": sum(totales.values()),
    }


def anular_canje(canje_id, registrado_en, conectar=bd.conexion, ahora=None):
    """RF-ES34: anula dentro de los 2 minutos; libera el día (periodo NULL)."""
    ahora = ahora or ahora_bogota()
    if ahora - registrado_en > timedelta(minutes=MINUTOS_ANULACION):
        return False, "Ya no se puede anular: pasaron más de 2 minutos."
    with conectar() as conn:
        with conn.cursor() as cur:
            cur.execute(
                "UPDATE canjes SET estado = 'rechazado', periodo = NULL "
                "WHERE id = %s AND estado = 'entregado'",
                (canje_id,),
            )
            cambiados = cur.rowcount
        conn.commit()
    if not cambiados:
        return False, "Este canje ya estaba anulado."
    return True, "Canje anulado. El aprendiz puede reclamar de nuevo hoy."


# ------------------------------------------------------------ beneficiarios
def listar_beneficiarios(conectar=bd.conexion):
    """Todos los beneficiarios (para la tabla y la vista previa de importación)."""
    with conectar() as conn, conn.cursor() as cur:
        cur.execute(
            "SELECT id, numero_documento, nombre_completo, email, activo "
            "FROM beneficiarios_sena ORDER BY nombre_completo"
        )
        filas = cur.fetchall()
    return [
        {
            "id": f["id"],
            "numero_documento": f["numero_documento"] or "",
            "nombre_completo": f["nombre_completo"],
            "email": f["email"] or "",
            "estado": "activo" if f["activo"] else "inactivo",
        }
        for f in filas
    ]


def aplicar_importacion(altas, cambios, bajas, conectar=bd.conexion):
    """RF-ES18: aplica la vista previa en una sola transacción."""
    with conectar() as conn:
        try:
            with conn.cursor() as cur:
                for c in cambios:
                    cur.execute(
                        "UPDATE beneficiarios_sena SET nombre_completo=%s, email=%s, activo=%s "
                        "WHERE numero_documento=%s",
                        (
                            c["nombre_completo"],
                            c["email"],
                            c["estado"] == "activo",
                            c["numero_documento"],
                        ),
                    )
                for a in altas:
                    cur.execute(
                        "INSERT INTO beneficiarios_sena (numero_documento, nombre_completo, email, activo) "
                        "VALUES (%s, %s, %s, %s)",
                        (
                            a["numero_documento"],
                            a["nombre_completo"],
                            a["email"],
                            a["estado"] == "activo",
                        ),
                    )
                for b in bajas:
                    cur.execute(
                        "UPDATE beneficiarios_sena SET activo = 0 WHERE numero_documento = %s",
                        (b["numero_documento"],),
                    )
            conn.commit()
        except pymysql.MySQLError:
            conn.rollback()
            raise
    return {"altas": len(altas), "cambios": len(cambios), "bajas": len(bajas)}


def guardar_beneficiario(datos, conectar=bd.conexion):
    """RF-ES28: alta o cambio individual. Devuelve (ok, mensaje)."""
    doc = (datos.get("numero_documento") or "").strip()
    email = (datos.get("email") or "").strip().lower()
    with conectar() as conn:
        with conn.cursor() as cur:
            cur.execute(
                "SELECT id, numero_documento FROM beneficiarios_sena "
                "WHERE (numero_documento = %s OR LOWER(email) = %s)",
                (doc, email),
            )
            existentes = cur.fetchall()
            propio = datos.get("id")
            for e in existentes:
                if e["id"] != propio:
                    return (
                        False,
                        "Ya existe un beneficiario con ese documento o correo.",
                    )
            activo = datos.get("estado", "activo") == "activo"
            if propio:
                cur.execute(
                    "UPDATE beneficiarios_sena SET numero_documento=%s, nombre_completo=%s, email=%s, activo=%s WHERE id=%s",
                    (doc, datos["nombre_completo"].strip(), email, activo, propio),
                )
            else:
                cur.execute(
                    "INSERT INTO beneficiarios_sena (numero_documento, nombre_completo, email, activo) VALUES (%s,%s,%s,%s)",
                    (doc, datos["nombre_completo"].strip(), email, activo),
                )
        conn.commit()
    return True, "Beneficiario guardado."


def hora_servidor(conectar=bd.conexion):
    """Para el control del reloj del equipo."""
    with conectar() as conn, conn.cursor() as cur:
        cur.execute("SELECT NOW() AS ahora")
        return cur.fetchone()["ahora"]
