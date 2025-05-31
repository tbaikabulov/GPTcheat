import os
import sys
import shutil
from pathlib import Path

def create_dmg():
    # Пути
    app_name = "InterviewAssistant"
    build_dir = Path("build")
    dist_dir = Path("dist")
    resources_dir = Path("resources")
    
    # Создаем директории
    build_dir.mkdir(exist_ok=True)
    dist_dir.mkdir(exist_ok=True)
    
    # Копируем ресурсы
    shutil.copytree(resources_dir, build_dir / "resources", dirs_exist_ok=True)
    
    # Создаем spec файл для PyInstaller
    spec_content = f"""
# -*- mode: python ; coding: utf-8 -*-

block_cipher = None

a = Analysis(
    ['src/main.py'],
    pathex=[],
    binaries=[],
    datas=[('resources', 'resources')],
    hiddenimports=[],
    hookspath=[],
    hooksconfig={{}},
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
    name='{app_name}',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=True,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon='resources/icons/app_icon.icns'
)

coll = COLLECT(
    exe,
    a.binaries,
    a.zipfiles,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name='{app_name}',
)

app = BUNDLE(
    coll,
    name='{app_name}.app',
    icon='resources/icons/app_icon.icns',
    bundle_identifier='com.interviewassistant.app',
    info_plist={{
        'CFBundleShortVersionString': '1.0.0',
        'CFBundleVersion': '1.0.0',
        'NSHighResolutionCapable': 'True'
    }},
)
"""
    
    with open("InterviewAssistant.spec", "w") as f:
        f.write(spec_content)
    
    # Запускаем PyInstaller
    os.system("pyinstaller InterviewAssistant.spec")
    
    # Создаем DMG
    os.system(f"create-dmg --volname '{app_name}' --window-pos 200 120 --window-size 800 400 --icon-size 100 --icon '{app_name}.app' 200 190 --hide-extension '{app_name}.app' --app-drop-link 600 185 'dist/{app_name}.dmg' 'dist/{app_name}.app'")

if __name__ == "__main__":
    create_dmg() 