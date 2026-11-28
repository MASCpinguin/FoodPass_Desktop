@echo off
chcp 65001 >nul
cd /d "%~dp0"
if not exist ".venv_build\Scripts\python.exe" (
  echo Primero ejecuta CREAR_EXE.bat una vez para instalar las dependencias.
  pause
  exit /b 1
)
if not exist ".env" copy /y ".env.example" ".env" >nul
".venv_build\Scripts\python.exe" -m foodpass_desktop
