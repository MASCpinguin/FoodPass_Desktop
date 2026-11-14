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
2. Crea tu rama con el ID de la tarea: `git checkout -b feature/T09-ventanilla`
3. Commits en español con el ID: `T09: selector de servicio con F5, F6 y F7`
4. Sube tu rama: `git push -u origin feature/T09-ventanilla`
5. Abre un Pull Request hacia `develop` y pide revisión
6. Nunca hagas push directo a `main` ni a `develop`

## Equipo

- Sebastian Reyes Gómez
- Edwin David
- Marco Antonio Angulo
<<<<<<< HEAD



## Estructura del proyecto

El proyecto utiliza una arquitectura organizada por capas para separar las responsabilidades y facilitar el mantenimiento del código.

```text
FoodPass_Desktop/
│
├── .github/
│   └── workflows/
│       └── ci.yml
│
├── foodpass_desktop/
│   ├── api/
│   │   └── __init__.py
│   ├── core/
│   │   └── __init__.py
│   ├── models/
│   │   └── __init__.py
│   ├── resources/
│   ├── services/
│   │   └── __init__.py
│   ├── storage/
│   │   └── __init__.py
│   ├── ui/
│   │   └── __init__.py
│   ├── main.py
│   └── __main__.py
│
├── tests/
│   └── test_ejemplo.py
│
├── requirements.txt
├── requirements-dev.txt
├── pyproject.toml
└── README.md
```

### Responsabilidad de cada capa

- **ui:** contiene las pantallas y componentes visuales de la aplicación.
- **services:** contiene la lógica de negocio y coordina las operaciones de la aplicación.
- **api:** contiene los componentes encargados de realizar las llamadas y comunicarse con la API central.
- **storage:** gestiona los datos locales mediante SQLite, la cola de operaciones y la caché.
- **models:** contiene los modelos que representan los datos utilizados por la aplicación.
- **core:** centraliza la configuración y la gestión de sesiones.
- **resources:** almacena los recursos necesarios para la interfaz, como imágenes e iconos.
- **tests:** contiene las pruebas automatizadas del proyecto.

## Herramientas de desarrollo y pruebas

El proyecto utiliza Ruff para revisar el código Python y Pytest para ejecutar pruebas automatizadas.

### Instalar las herramientas de desarrollo

Con el entorno virtual activado, ejecutar:

```bash
pip install -r requirements-dev.txt
```

### Ejecutar Ruff

Para revisar el estilo y detectar errores en el código:

```bash
ruff check .
```

### Ejecutar Pytest

Para ejecutar las pruebas automatizadas:

```bash
pytest
```

Para obtener información detallada de cada prueba:

```bash
pytest -v
```

### Integración continua

El proyecto utiliza GitHub Actions para automatizar las revisiones de calidad.

Cuando se crea o actualiza un Pull Request dirigido a la rama `develop`, se ejecutan automáticamente:

1. La revisión del código mediante Ruff.
2. Las pruebas automatizadas mediante Pytest.

Si alguna de estas verificaciones falla, GitHub marcará el proceso de integración continua como fallido.
=======
- Juan Jose Martinez
>>>>>>> origin/develop
