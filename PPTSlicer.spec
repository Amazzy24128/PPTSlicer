# -*- mode: python ; coding: utf-8 -*-

block_cipher = None

numpy_hooks_path = 'D:\\envs_dirs\\PPTSlicerEnv\\lib\\site-packages\\numpy\\hooks'
cv2_data_path = 'D:\\envs_dirs\\PPTSlicerEnv\\lib\\site-packages\\cv2\\data'

a = Analysis(
    ['app_ui.py'],
    pathex=[],
    binaries=[],
    datas=[
        ('notify', 'notify'),
        ('assets', 'assets'),
        (cv2_data_path, 'cv2/data')
    ],
    hiddenimports=[],  
    hookspath=[numpy_hooks_path],
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
    name='PPTSlicer',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=False,
    disable_windowed_traceback=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon='assets/icon.ico',
)
coll = COLLECT(
    exe,
    a.binaries,
    a.zipfiles,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name='PPTSlicer',
)