# Manual de Usuario — Módulo de Beneficiarios (`FoodPass_Desktop`)

Esta guía explica cómo consultar y filtrar registros en **FoodPass_Desktop**, y detalla las funciones de plantilla de Excel, importación y caché cifrada que se encuentran `(Pendiente)`.

---

## 1. Descargar y llenar la plantilla de Excel `(Pendiente)`

> **Estado:** `(Pendiente)` — La descarga y gestión de la plantilla de Excel aún no está disponible en `develop`.

1. Generar o abrir la plantilla oficial (`plantilla_beneficiarios.xlsx`) `(Pendiente)`.
2. Revisar la hoja **Instrucciones** para confirmar los formatos permitidos antes de diligenciar datos `(Pendiente)`.
3. En la hoja **Beneficiarios**, completar las columnas en este orden exacto `(Pendiente)`:
   - `tipo_documento`: tipo de documento (por ejemplo `CC`, `TI`, `CE`).
   - `numero_documento`: número sin puntos, comas ni espacios.
   - `nombre_completo`: nombre y apellidos del beneficiario.
   - `programa`: programa de formación.
   - `ficha`: número de ficha.
   - `estado`: debe ser exactamente `activo` o `inactivo`.

> **Importante:** No escribir fórmulas ni valores que inicien con `=`, `+`, `-` o `@` en ninguna celda; el sistema los bloquea por seguridad `(Pendiente)`.

---

## 2. Reglas de validación al importar el archivo `(Pendiente)`

> **Estado:** `(Pendiente)` — La carga y validación de archivos de beneficiarios aún no está integrada en `develop`.

Al cargar un archivo de beneficiarios, el sistema revisará fila por fila y separará los registros válidos de los errores `(Pendiente)`:

- **Campos obligatorios `(Pendiente)`:** `numero_documento` y `nombre_completo` no pueden estar vacíos.
- **Estado válido `(Pendiente)`:** `estado` solo acepta `activo` o `inactivo` (sin importar mayúsculas o minúsculas).
- **Sin duplicados `(Pendiente)`:** no se permiten dos filas con el mismo `numero_documento` (ni el mismo número asociado a distintos tipos de documento).
- **Filas vacías `(Pendiente)`:** las filas completamente en blanco se ignoran automáticamente.

Si una fila tiene algún error, se reportará con su número de fila y motivo para corregir en el Excel y volver a intentar `(Pendiente)`.

---

## 3. Buscar y filtrar beneficiarios en pantalla

En la vista de **Beneficiarios** puedes localizar registros rápidamente:

1. **Buscador por texto:** escribe un número de documento o parte del nombre completo para filtrar en tiempo real.
2. **Filtro por estado:** selecciona `todos`, `activo` o `inactivo`.
3. **Filtro por programa:** elige `todos` o un programa específico de la lista desplegable.
4. **Contador:** revisa el indicador superior para ver cuántos beneficiarios coinciden con los filtros activos.

---

## 4. Caché cifrada y seguridad de datos locales `(Pendiente)`

> **Estado:** `(Pendiente)` — La caché cifrada aún no está integrada en el flujo principal de `develop`.

- Los datos de beneficiarios guardados en caché local se almacenan **cifrados** en disco (`beneficiarios_cache.bin`), no en texto plano `(Pendiente)`.
- La clave de cifrado (`cache.key` o variable de entorno `FOODPASS_CACHE_KEY`) se mantiene fuera del control de versiones para proteger la información en el equipo `(Pendiente)`.
- Si el archivo de caché no existe o no puede descifrarse, la aplicación inicia con la lista vacía de forma segura sin interrumpir el uso `(Pendiente)`.

---

## 5. Solución rápida a problemas comunes

- **Un beneficiario no aparece tras cargar el Excel `(Pendiente)`:** la carga/validación desde Excel está pendiente de integración.
- **La tabla aparece vacía al filtrar:** verifica que el buscador no tenga texto residual y que los filtros de **Estado** y **Programa** estén en `todos`.