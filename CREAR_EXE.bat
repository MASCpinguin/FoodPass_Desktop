@echo off
chcp 65001 >nul
setlocal
cd /d "%~dp0"
title FoodPass Escritorio - Crear ejecutable
echo.
echo  ===============================================
echo   FoodPass Escritorio - Crear FoodPass.exe
echo  ===============================================
echo.

set "PY="
for %%V in (3.14 3.13 3.12) do (
  if not defined PY (
    py -%%V -c "import sys" >nul 2>nul && set "PY=py -%%V"
  )
)
if not defined PY (
  python -c "import sys; sys.exit(0 if sys.version_info>=(3,10) else 1)" >nul 2>nul && set "PY=python"
)
if not defined PY (
  echo  No se encontro Python 3.10 o superior. Intentando instalarlo con winget...
  winget install -e --id Python.Python.3.13 --accept-package-agreements --accept-source-agreements
  echo.
  echo  Cierra esta ventana y vuelve a ejecutar CREAR_EXE.bat.
  echo  Si winget no esta disponible, instala Python desde https://www.python.org/downloads/
  echo  y marca la opcion "Add python.exe to PATH".
  pause
  exit /b 1
)

echo  [1/4] Usando: %PY%
%PY% -m venv .venv_build || goto :error
call .venv_build\Scripts\activate.bat || goto :error

echo  [2/4] Instalando dependencias (puede tardar unos minutos la primera vez)...
python -m pip install --upgrade pip >nul
python -m pip install -r requirements.txt pyinstaller || goto :error

echo  [3/4] Generando el ejecutable...
pyinstaller --noconfirm --clean FoodPass.spec || goto :error

echo  [4/4] Copiando la configuracion...
if not exist "dist\FoodPass\.env" (
  if exist ".env" (copy /y ".env" "dist\FoodPass\.env" >nul) else (copy /y ".env.example" "dist\FoodPass\.env" >nul)
)

echo.
echo  LISTO: dist\FoodPass\FoodPass.exe
echo  Revisa los datos de conexion en dist\FoodPass\.env antes de abrirlo.
echo  Para llevarlo a otro PC, copia la carpeta dist\FoodPass completa.
echo.
explorer "dist\FoodPass"
pause
exit /b 0

:error
echo.
echo  Hubo un error. Revisa los mensajes de arriba o avisa a soporte tecnico.
pause
exit /b 1
