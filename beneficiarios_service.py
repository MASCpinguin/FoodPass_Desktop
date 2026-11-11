import openpyxl
from openpyxl import Workbook

COLUMNAS = ["tipo_documento", "numero_documento", "nombre_completo", "programa", "ficha", "estado"]

def generar_plantilla(ruta_salida="plantilla_beneficiarios.xlsx"):
    wb = Workbook()
    
    # Hoja 1: Beneficiarios con cabeceras
    ws = wb.active
    ws.title = "Beneficiarios"
    ws.append(COLUMNAS)
    
    # Fila de ejemplo
    ws.append(["CC", "12345678", "Ejemplo Nombre", "Sistemas", "2857123", "activo"])
    
    # Hoja 2: Instrucciones
    ws_instrucciones = wb.create_sheet(title="Instrucciones")
    ws_instrucciones.append(["Columna", "Descripción", "Valores Válidos"])
    ws_instrucciones.append(["tipo_documento", "Tipo de documento de identidad", "CC, TI, CE, etc."])
    ws_instrucciones.append(["numero_documento", "Número de documento sin puntos ni comas", "Numérico / Texto"])
    ws_instrucciones.append(["nombre_completo", "Nombre y apellido del beneficiario", "Texto"])
    ws_instrucciones.append(["programa", "Programa de formación SENA", "Texto"])
    ws_instrucciones.append(["ficha", "Número de la ficha SENA", "Numérico / Texto"])
    ws_instrucciones.append(["estado", "Estado del beneficiario", "activo / inactivo"])

    wb.save(ruta_salida)
    return ruta_salida

def validar_archivo_beneficiarios(file_path):
    wb = openpyxl.load_workbook(file_path)
    ws = wb.active
    
    filas_validas = []
    errores = []
    
    documentos_vistos = {} # Para detectar duplicados y tipos distintos
    
    for index, row in enumerate(ws.iter_rows(min_row=2, values_only=True), start=2):
        # Ignorar filas totalmente vacías
        if not any(row):
            continue
            
        tipo_doc, num_doc, nombre, programa, ficha, estado = [str(cell).strip() if cell is not None else "" for cell in row]
        
        # Regla: Contenido no permitido (=, +, -, @)
        fila_con_formula = False
        for val in [tipo_doc, num_doc, nombre, programa, ficha, estado]:
            if val.startswith(('=', '+', '-', '@')):
                errores.append({"fila": index, "motivo": "Contenido no permitido"})
                fila_con_formula = True
                break
        if fila_con_formula:
            continue
            
        # Regla: numero_documento vacío
        if not num_doc:
            errores.append({"fila": index, "motivo": "Documento vacío"})
            continue
            
        # Regla: nombre_completo vacío
        if not nombre:
            errores.append({"fila": index, "motivo": "Nombre vacío"})
            continue
            
        # Regla: estado distinto de activo/inactivo
        if estado.lower() not in ["activo", "inactivo"]:
            errores.append({"fila": index, "motivo": "Estado inválido"})
            continue
            
        # Regla: Mismo número con distinto tipo / repetido
        doc_key = num_doc
        if doc_key in documentos_vistos:
            tipo_previo, fila_previa = documentos_vistos[doc_key]
            if tipo_previo != tipo_doc:
                errores.append({"fila": index, "motivo": "Mismo número con otro tipo de documento"})
                continue
            else:
                errores.append({"fila": index, "motivo": f"Documento repetido (también en la fila {fila_previa})"})
                continue
        else:
            documentos_vistos[doc_key] = (tipo_doc, index)
            
        filas_validas.append({
            "tipo_documento": tipo_doc,
            "numero_documento": num_doc,
            "nombre_completo": nombre,
            "programa": programa,
            "ficha": ficha,
            "estado": estado
        })
        
    return filas_validas, errores