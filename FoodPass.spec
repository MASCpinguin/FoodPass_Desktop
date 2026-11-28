# -*- mode: python ; coding: utf-8 -*-
# Empaquetado de FoodPass Escritorio con PyInstaller (RNF-ES23).
# Uso: pyinstaller --noconfirm --clean FoodPass.spec  (lo hace CREAR_EXE.bat)

a = Analysis(
    ["lanzar_foodpass.py"],
    pathex=["."],
    datas=[("foodpass_desktop/resources", "foodpass_desktop/resources")],
    hiddenimports=[
        "keyring.backends.Windows",
        "keyring.backends.fail",
        "pymysql",
        "openpyxl",
    ],
    excludes=["tkinter", "unittest", "pytest", "tools"],
    noarchive=False,
)
pyz = PYZ(a.pure)
exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name="FoodPass",
    icon="foodpass_desktop/resources/icons/foodpass.ico",
    console=False,
    disable_windowed_traceback=False,
    upx=False,
)
coll = COLLECT(exe, a.binaries, a.datas, name="FoodPass", upx=False)
