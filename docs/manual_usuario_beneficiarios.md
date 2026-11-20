# Manual de Usuario — Módulo de Beneficiarios (`FoodPass_Desktop`)

Esta guía explica cómo preparar la plantilla de beneficiarios, cargar información, consultar/filtrar registros y proteger los datos locales en **FoodPass_Desktop**.

---

## 1. Descargar y llenar la plantilla de Excel

1. Genera o abre la plantilla oficial (`plantilla_beneficiarios.xlsx`).
2. Revisa la hoja **Instrucciones** para confirmar los formatos permitidos antes de diligenciar datos.
3. En la hoja **Beneficiarios**, completa las columnas en este orden exacto:
   - `tipo_documento`: tipo de documento (por ejemplo `CC`, `TI`, `CE`).
   - `numero_documento`: número sin puntos, comas ni espacios.
   - `nombre_completo`: nombre y apellidos del beneficiario.
   - `programa`: programa de formación.
   - `ficha`: número de ficha.
   - `estado`: debe ser exactamente `activo` o `inactivo`.

> **Importante:** No escribas fórmulas ni valores que inicien con `=`, `+`, `-` o `@` en ninguna celda; el sistema los bloquea por seguridad.

---

## 2. Reglas de validación al importar el archivo

Al cargar un archivo de beneficiarios, el sistema revisa fila por fila y separa los registros válidos de los errores:

- **Campos obligatorios:** `numero_documento` y `nombre_completo` no pueden estar vacíos.
- **Estado válido:** `estado` solo acepta `activo` o `inactivo` (sin importar mayúsculas o minúsculas).
- **Sin duplicados:** no se permiten dos filas con el mismo `numero_documento` (ni el mismo número asociado a distintos tipos de documento).
- **Filas vacías:** las filas completamente en blanco se ignoran automáticamente.

Si una fila tiene algún error, se reporta con su número de fila y motivo para que puedas corregirlo en el Excel y volver a intentar.

---

## 3. Buscar y filtrar beneficiarios en pantalla

En la vista de **Beneficiarios** puedes localizar registros rápidamente:

1. **Buscador por texto:** escribe un número de documento o parte del nombre completo para filtrar en tiempo real.
2. **Filtro por estado:** selecciona `todos`, `activo` o `inactivo`.
3. **Filtro por programa:** elige `todos` o un programa específico de la lista desplegable.
4. **Contador:** revisa el indicador superior para ver cuántos beneficiarios coinciden con los filtros activos.

---

## 4. Caché cifrada y seguridad de datos locales

- Los datos de beneficiarios guardados en caché local se almacenan **cifrados** en disco (`beneficiarios_cache.bin`), no en texto plano.
- La clave de cifrado (`cache.key` o variable de entorno `FOODPASS_CACHE_KEY`) se mantiene fuera del control de versiones para proteger la información en el equipo.
- Si el archivo de caché no existe o no puede descifrarse, la aplicación inicia con la lista vacía de forma segura sin interrumpir el uso.

---

## 5. Solución rápida a problemas comunes

- **Un beneficiario no aparece tras cargar el Excel:** revisa si tuvo error de documento vacío, nombre vacío, estado distinto de `activo`/`inactivo`, documento duplicado o celda iniciando con `=`, `+`, `-` o `@`.
- **La tabla aparece vacía al filtrar:** verifica que el buscador no tenga texto residual y que los filtros de **Estado** y **Programa** estén en `todos`.