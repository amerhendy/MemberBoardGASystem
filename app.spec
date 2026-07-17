# -*- mode: python ; coding: utf-8 -*-
"""
app.spec
ملف تجميع PyInstaller لبناء ملف exe واحد (Windows) للتطبيق مع الأيقونة والملفات المساعدة.
يُشغَّل بالأمر:  pyinstaller app.spec
"""

a = Analysis(
    ['main.py'],
    pathex=[],
    binaries=[],
    # 👇 هنا نقوم بضم قاعدة البيانات، ملف الستايل، ومجلد الأيقونات ليكونوا داخل الـ EXE
    datas=[
        ('database/schema.sql', 'database'),
    ],
    hiddenimports=[
        'PyQt6.QtCore',
        'PyQt6.QtGui',
        'PyQt6.QtWidgets',
    ],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    noarchive=False,
)

pyz = PYZ(a.pure, a.zipped_data)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.zipfiles,
    a.datas,
    [],
    name='MemberBoardGASystem',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon='assets/app_icon.ico'
)