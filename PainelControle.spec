# -*- mode: python ; coding: utf-8 -*-

block_cipher = None

# Adicione aqui qualquer import oculto necessario
hidden_imports = [
    'engineio.async_drivers.threading', 
    'flask_socketio', 
    'serial', # pyserial
    'serial.tools.list_ports'
]

a = Analysis(
    ['main.py'],
    pathex=[],
    binaries=[],
    datas=[
        ('templates', 'templates'),
        ('fotos', 'fotos'),
        ('presets', 'presets'),
        ('Manual_de_Hardware.html', '.'),
        ('CH34x_Install_Windows_v3_4.EXE', '.'),
        ('vereadores.json', '.'),
        # session_config.json nao sera incluido para nao sobrescrever, 
        # o app deve criar se nao existir. Mas se quiser padrao, descomente abaixo:
        # ('session_config.json', '.') 
    ],
    hiddenimports=hidden_imports,
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)
pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name='PainelControle',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=False, # GUI Application (No black terminal window)
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
)
coll = COLLECT(
    exe,
    a.binaries,
    a.zipfiles,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name='PainelControle',
)
