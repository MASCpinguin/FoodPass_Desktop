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
## Servidor simulado de la API
Mientras la API central no esté lista, trabajamos contra un servidor simulado que responde como el 05 Contrato de endpoints.

Instalar las dependencias de desarrollo (una sola vez):
```bat
pip install -r requirements-dev.txt
```

Arrancarlo en una terminal aparte (queda corriendo; se apaga con Ctrl + C):
```bat
python -m tools.mock_api
```

En el `.env`: `API_URL=http://localhost:8000/api/v1/escritorio`

Datos de prueba:
| Caso | Dato |
|---|---|
| Operador válido | `operador@foodpass.co` / `123456` |
| Cuenta sin rol de cafetería (error 403) | `sinrol@foodpass.co` / `123456` |
| Beneficiarios (QR = usuario_id) | 1001 a 1020 · inactivos: 1005, 1010, 1015, 1020 · sin foto: 1003, 1006, 1009… |

Tres contraseñas erradas seguidas bloquean la cuenta 5 minutos (error 423). Los datos se reinician al apagar el servidor.

Endpoints disponibles: `GET /estado`, `POST /auth/login`, `POST /auth/renovar`, `POST /auth/logout`.

Pruebas:
```bat
python -m pytest
```
```

## Flujo de trabajo
1. Actualiza develop: `git checkout develop` y `git pull`
2. Crea tu rama: `git checkout -b feature/HU-XX-descripcion`
3. Haz commits con prefijo: `feat:`, `fix:`, `chore:`, `docs:`
4. Sube tu rama: `git push -u origin feature/HU-XX-descripcion`
5. Abre un Pull Request hacia `develop` y pide revisión
6. Nunca hagas push directo a `main` ni a `develop`

## Equipo

- Sebastian Reyes Gómez
- Edwin David
- Marco Antonio Angulo
- Juan Jose Martinez