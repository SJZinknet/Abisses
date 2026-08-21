#!/usr/bin/env python3
"""Génère les icônes PNG et ICO d'Abisses à partir de formes simples."""

from pathlib import Path

from PIL import Image, ImageDraw

ROOT = Path(__file__).resolve().parent
ICON_DIR = ROOT / "icons"
MASTER_SIZE = 1024


def build_master() -> Image.Image:
    image = Image.new("RGBA", (MASTER_SIZE, MASTER_SIZE), (0, 0, 0, 0))
    draw = ImageDraw.Draw(image)

    draw.rounded_rectangle(
        (42, 42, 982, 982),
        radius=215,
        fill="#173a5e",
    )

    # Relief valaisan stylisé.
    draw.polygon(
        [(92, 674), (355, 288), (508, 508), (654, 246), (938, 674)],
        fill="#8fc7bd",
    )
    draw.polygon(
        [(92, 674), (355, 288), (508, 508), (654, 246), (938, 674), (938, 746), (92, 746)],
        fill="#f5f7f4",
    )
    draw.polygon(
        [(278, 401), (355, 288), (420, 382), (366, 359), (331, 410)],
        fill="#d9ebe7",
    )
    draw.polygon(
        [(566, 392), (654, 246), (748, 374), (677, 337), (629, 410)],
        fill="#d9ebe7",
    )

    # Filet d'eau : un bisse traverse le paysage sans masquer la montagne.
    water = [(102, 700), (244, 668), (382, 688), (514, 650), (662, 672), (802, 636), (932, 656)]
    draw.line(water, fill="#ffffff", width=76, joint="curve")
    draw.line(water, fill="#35bfe6", width=48, joint="curve")
    draw.line(water, fill="#9be7f7", width=13, joint="curve")

    # Deux traits plus fins évoquent l'écoulement en aval.
    draw.arc((168, 706, 520, 868), 194, 341, fill="#35bfe6", width=25)
    draw.arc((474, 696, 854, 884), 198, 340, fill="#35bfe6", width=19)
    return image


def main() -> None:
    ICON_DIR.mkdir(parents=True, exist_ok=True)
    master = build_master()
    png = master.resize((512, 512), Image.Resampling.LANCZOS)
    png.save(ICON_DIR / "abisses.png", optimize=True)
    master.save(
        ICON_DIR / "abisses.ico",
        format="ICO",
        sizes=[(16, 16), (24, 24), (32, 32), (48, 48), (64, 64), (128, 128), (256, 256)],
    )
    print(ICON_DIR / "abisses.png")
    print(ICON_DIR / "abisses.ico")


if __name__ == "__main__":
    main()
