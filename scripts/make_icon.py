"""Génère l'icône de l'application Clavier-Propre (clavier + bouclier).

Produit un fichier .ico multi-résolutions (16, 32, 48, 64, 128, 256) et un
.png 256x256. Lancé sans argument, il écrit dans le dossier du script.

Dessin :
  - fond rond dégradé rouge (#c0392b -> #922b21) évoquant la protection active
  - clavier stylisé blanc (rangées de touches) au centre
  - bouclier de validation par-dessus, bordure blanche
"""
from __future__ import annotations

from pathlib import Path

from PIL import Image, ImageDraw, ImageFilter


def _lerp(c1, c2, t):
    return tuple(int(c1[i] + (c2[i] - c1[i]) * t) for i in range(3))


def _radial_gradient(size, center, inner, outer):
    img = Image.new("RGB", (size, size), outer)
    px = img.load()
    cx, cy = center
    maxd = (size * 0.70)
    for y in range(size):
        for x in range(size):
            d = ((x - cx) ** 2 + (y - cy) ** 2) ** 0.5
            t = min(d / maxd, 1.0)
            px[x, y] = _lerp(inner, outer, t)
    return img


def _rounded_mask(size, radius):
    mask = Image.new("L", (size, size), 0)
    d = ImageDraw.Draw(mask)
    d.rounded_rectangle((0, 0, size - 1, size - 1), radius=radius, fill=255)
    return mask


def draw_icon(size: int) -> Image.Image:
    inner = (192, 57, 43)   # #c0392b
    outer = (110, 35, 30)   # plus sombre pour le dégradé
    bg = _radial_gradient(size, (size // 2, size // 2), inner, outer)

    # Coins arrondis.
    mask = _rounded_mask(size, int(size * 0.22))
    rounded = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    rounded.paste(bg, (0, 0), mask)

    img = rounded.convert("RGBA")
    draw = ImageDraw.Draw(img, "RGBA")

    # --- Clavier stylisé blanc ---
    kw = int(size * 0.62)   # largeur du clavier
    kh = int(size * 0.40)   # hauteur
    kx = (size - kw) // 2
    ky = int(size * 0.30)
    pad = max(2, size // 64)
    # Fond du clavier (blanc cassé).
    draw.rounded_rectangle(
        (kx, ky, kx + kw, ky + kh),
        radius=max(3, size // 40),
        fill=(245, 245, 245, 255),
    )
    # Touches : 3 rangées de 6 touches.
    rows = 3
    cols = 6
    gap = max(1, size // 80)
    key_w = (kw - 2 * pad - (cols - 1) * gap) / cols
    key_h = (kh - 2 * pad - (rows - 1) * gap) / rows
    for r in range(rows):
        for c in range(cols):
            x0 = kx + pad + c * (key_w + gap)
            y0 = ky + pad + r * (key_h + gap)
            x1 = x0 + key_w
            y1 = y0 + key_h
            draw.rounded_rectangle(
                (x0, y0, x1, y1), radius=max(1, size // 100), fill=(60, 60, 60, 230)
            )

    # --- Bouclier de validation (bas-droite) ---
    sw = int(size * 0.42)
    sx = int(size * 0.50)
    sy = int(size * 0.46)
    # Forme bouclier via polygone.
    tip_y = sy + sw
    pts = [
        (sx + sw / 2, sy),
        (sx + sw, sy + sw * 0.18),
        (sx + sw * 0.96, sy + sw * 0.55),
        (sx + sw / 2, tip_y),
        (sx + sw * 0.04, sy + sw * 0.55),
        (sx, sy + sw * 0.18),
    ]
    # Ombre.
    shadow = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    sdraw = ImageDraw.Draw(shadow, "RGBA")
    sdraw.polygon([(p[0] + 2, p[1] + 3) for p in pts], fill=(0, 0, 0, 90))
    img.alpha_composite(shadow)

    # Bouclier vert.
    draw.polygon(pts, fill=(39, 174, 96, 255), outline=(255, 255, 255, 255), width=max(1, size // 128))
    # Coche blanche dans le bouclier.
    cx_b = sx + sw / 2
    cy_b = sy + sw * 0.42
    lw = max(2, size // 48)
    draw.line(
        [(cx_b - sw * 0.18, cy_b), (cx_b - sw * 0.04, cy_b + sw * 0.16)],
        fill=(255, 255, 255, 255), width=lw, joint="curve"
    )
    draw.line(
        [(cx_b - sw * 0.04, cy_b + sw * 0.16), (cx_b + sw * 0.22, cy_b - sw * 0.16)],
        fill=(255, 255, 255, 255), width=lw, joint="curve"
    )

    return img


def main(out_dir: Path | None = None) -> None:
    out_dir = out_dir or Path(__file__).resolve().parent
    sizes = [16, 32, 48, 64, 128, 256]
    images = [draw_icon(s) for s in sizes]
    ico_path = out_dir / "clavier.ico"
    images[-1].save(ico_path, format="ICO", sizes=[(s, s) for s in sizes], append_images=images[:-1])
    png_path = out_dir / "clavier.png"
    images[-1].save(png_path, format="PNG")
    print(f"Icône générée : {ico_path} ({len(sizes)} résolutions)")
    print(f"PNG 256x256 : {png_path}")


if __name__ == "__main__":
    main()
