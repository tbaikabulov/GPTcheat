import os
import subprocess
from pathlib import Path

def convert_svg_to_icns():
    # Пути
    svg_path = Path("resources/icons/app_icon.svg")
    iconset_path = Path("resources/icons/app_icon.iconset")
    icns_path = Path("resources/icons/app_icon.icns")
    
    # Создаем директорию для iconset
    iconset_path.mkdir(parents=True, exist_ok=True)
    
    # Размеры иконок для macOS
    sizes = [16, 32, 64, 128, 256, 512, 1024]
    
    # Конвертируем SVG в PNG разных размеров
    for size in sizes:
        # Обычная иконка
        subprocess.run([
            "rsvg-convert",
            "-w", str(size),
            "-h", str(size),
            str(svg_path),
            "-o", str(iconset_path / f"icon_{size}x{size}.png")
        ])
        
        # Retina иконка (2x)
        if size <= 512:  # Максимальный размер для Retina
            subprocess.run([
                "rsvg-convert",
                "-w", str(size * 2),
                "-h", str(size * 2),
                str(svg_path),
                "-o", str(iconset_path / f"icon_{size}x{size}@2x.png")
            ])
    
    # Создаем ICNS файл
    subprocess.run([
        "iconutil",
        "-c", "icns",
        str(iconset_path),
        "-o", str(icns_path)
    ])
    
    # Удаляем временную директорию iconset
    for file in iconset_path.glob("*"):
        file.unlink()
    iconset_path.rmdir()
    
    print(f"ICNS файл создан: {icns_path}")

if __name__ == "__main__":
    convert_svg_to_icns() 