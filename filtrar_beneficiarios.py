def filtrar_beneficiarios(
    beneficiarios: list[dict],
    texto_busqueda: str = "",
    estado: str = "todos",
    programa: str = "todos",
) -> list[dict]:
    """
    Filtra una lista de beneficiarios por:
    - texto_busqueda: coincide en numero_documento o nombre_completo
    - estado: 'todos', 'activo' o 'inactivo'
    - programa: 'todos' o texto coincidente en programa
    """
    texto = (texto_busqueda or "").strip().lower()
    estado_limpio = (estado or "todos").strip().lower()
    programa_limpio = (programa or "todos").strip().lower()

    resultado = []
    for item in beneficiarios:
        num_doc = str(item.get("numero_documento", "")).strip().lower()
        nombre = str(item.get("nombre_completo", "")).strip().lower()
        est = str(item.get("estado", "")).strip().lower()
        prog = str(item.get("programa", "")).strip().lower()

        if texto and texto not in num_doc and texto not in nombre:
            continue

        if estado_limpio != "todos" and est != estado_limpio:
            continue

        if programa_limpio != "todos" and programa_limpio not in prog:
            continue

        resultado.append(item)

    return resultado