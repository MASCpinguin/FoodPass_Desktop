# FoodPass Desktop

Aplicación de escritorio de FoodPass para la operación de la cafetería del SENA: verificación de beneficiarios, ventas y reportes. Construida con Python y PySide6, se comunica con la API central de FoodPass.

## Requisitos
- Python 3.10 o superior
- Git
- VS Code (recomendado)

## Instalación
```bat
git clone https://github.com/MASCpinguin/FoodPass_Desktop.git
cd FoodPass_Desktop
py -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
copy .env.example .env
```

> Clona el proyecto fuera de OneDrive (por ejemplo en `C:\dev`).

## Ejecutar
```bat
python -m foodpass_desktop
```

## Flujo de trabajo
1. Actualiza develop: `git checkout develop` y `git pull`
2. Crea tu rama con el ID de la tarea: `git checkout -b feature/T09-ventanilla`
3. Commits en español con el ID: `T09: selector de servicio con F5, F6 y F7`
4. Sube tu rama: `git push -u origin feature/T09-ventanilla`
5. Abre un Pull Request hacia `develop` y pide revisión
6. Nunca hagas push directo a `main` ni a `develop`


## Equipo

- Sebastian Reyes Gómez