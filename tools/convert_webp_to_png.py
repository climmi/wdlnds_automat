import os
from pathlib import Path

from PIL import Image


def main() -> None:
    root = Path(__file__).resolve().parent.parent
    images_dir = root / "app" / "assets" / "images"
    if not images_dir.exists():
        print(f"Missing folder: {images_dir}")
        return

    webps = list(images_dir.glob("*.webp"))
    if not webps:
        print("No .webp files found in app/assets/images")
        return

    for src in webps:
        dst = src.with_suffix(".png")
        try:
            with Image.open(src) as img:
                img.save(dst, "PNG")
            print(f"Converted: {src.name} -> {dst.name}")
        except Exception as exc:
            print(f"Failed: {src.name}: {exc}")


if __name__ == "__main__":
    main()
