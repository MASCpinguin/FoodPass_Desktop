# FoodPass Desktop

Aplicación de escritorio de FoodPass para la ventanilla de la cafetería del SENA (CEAI): entrega del apoyo de alimentación con el QR de la web o el código del celular, canje por documento (F2), anulación, panel del día, beneficiarios y reporte de entregas en Excel.

Inicia sesión con la API FoodPass (Node.js) y trabaja directamente sobre la base MySQL `foodpass_v2`, la misma que usan la web y la API.

## Requisitos
- Windows 10/11
- Python 3.14 (sirve desde 3.12)
- Git
- XAMPP (MySQL y phpMyAdmin) para la base de prueba
- Node.js LTS para la API FoodPass ([valencia4414/FoodPass_API](https://github.com/valencia4414/FoodPass_API))

## Puesta en marcha (unos 10 minutos)

### 1. Base de datos
1. En XAMPP, enciende **MySQL** y abre `http://localhost/phpmyadmin`.
2. Crea la base `foodpass_v2` con cotejamiento `utf8mb4_unicode_ci`.
3. Pestaña **Importar** → `sql/foodpass_v2_escritorio_demo.sql`.
   > Ese archivo borra y recrea las tablas: impórtalo solo en una base nueva.
4. Pestaña **SQL** → pega y ejecuta `sql/codigos_prueba.sql` (crea códigos para probar la ventanilla).

### 2. API FoodPass
En la carpeta de la API crea un `.env`:
```
PORT=3000
DB_HOST=127.0.0.1
DB_PORT=3306
DB_USER=root
DB_PASSWORD=
DB_NAME=foodpass_v2
JWT_SECRET=una-frase-larga
JWT_EXPIRES_IN=7d
```
y enciéndela (deja la terminal abierta):
```bat
npm install
node index.js
```

### 3. Escritorio
Clona fuera de OneDrive, por ejemplo en `C:\dev`:
```bat
git clone https://github.com/MASCpinguin/FoodPass_Desktop.git
cd FoodPass_Desktop
py -3.14 -m venv .venv
.venv\Scripts\activate
pip install -r requirements-dev.txt
copy .env.example .env
python -m foodpass_desktop
```
El `.env.example` ya trae los valores para XAMPP y la API en el mismo equipo.

**Sin usar la terminal:** doble clic en `CREAR_EXE.bat` (instala todo y genera el ejecutable) y luego `ABRIR_SIN_EXE.bat` para abrir la app.

### Cuentas de prueba
| Cuenta | Correo | Contraseña |
|---|---|---|
| Operador | operador@foodpass.com | FoodPass2026! |
| Aprendices | aprendiz1@soy.sena.edu.co … aprendiz19@soy.sena.edu.co | Aprendiz2026! |

Códigos para la ventanilla (después de `sql/codigos_prueba.sql`, elige el servicio con F5/F6/F7):

| Código | Resultado |
|---|---|
| `FP-A1B2C3`, `FP-B2C3D4`, `FP-C3D4E5`, `FP-D4E5F6` | Entrega registrada |
| `FP-QR-PRUEBA-0001` … `0003` | Entrega con QR de la web |
| `FP-E5F6A7` | No está en la base (no es beneficiario) |
| `FP-F6A7B8` | No está en la base (inactivo) |
| `FP-0A0B0C` | Código vencido |
| F2 + documento `1001001100` | Canje manual |

## Ejecutable (.exe)
```bat
pip install pyinstaller
pyinstaller FoodPass.spec --noconfirm
```
Queda en `dist\FoodPass\FoodPass.exe`. Copia tu `.env` junto al `.exe`; nunca va dentro del ejecutable. Para repartirlo se copia la carpeta `dist\FoodPass` completa.

## Pruebas
```bat
ruff check .
pytest
```
El CI de GitHub corre ambos en cada Pull Request hacia `develop`.

## Flujo de trabajo
1. Actualiza develop: `git switch develop` y `git pull`
2. Crea tu rama con el ID de la tarea: `git switch -c feature/T09-ventanilla`
3. Commits en español con el ID: `T09: selector de servicio con F5, F6 y F7`
4. Sube tu rama: `git push -u origin feature/T09-ventanilla`
5. Abre un Pull Request hacia `develop` y pide revisión
6. Nunca hagas push directo a `main` ni a `develop`

## Estructura
```text
foodpass_desktop/
├── api/          Cliente HTTP de la API y tareas en segundo plano
├── core/         Configuración (.env), sesión e inactividad
├── services/     Reglas: sesión, canje, beneficiarios, reportes
├── storage/      MySQL (canje transaccional, consultas) y token (keyring)
├── ui/           Ventanas, pantallas y componentes (PySide6)
├── utils/        Seguridad de Excel y control del reloj
└── resources/    Tema (tema.qss), fuentes Poppins, logos e iconos
sql/              Base de demostración, códigos de prueba y cambios para la base real
tests/            Pruebas pytest
tools/mock_api/   Servidor simulado de la API (primeras versiones)
```
Más detalle en el **Manual técnico** (documento 09).

## Equipo
Miguel Ángel Sevillano (Product Owner) · Edwin David Estupiñán (líder técnico) · Marco Antonio Angulo (Scrum Master) · Juan Manuel · Sebastián Reyes Gómez · Juan José Martínez

SENA · CEAI · ADSO 31 · Ficha 3173467
