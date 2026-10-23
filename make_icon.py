"""
Generates the modern 256x256 icon.ico and icon.png for InitControl.
No text, professional, high-tech neon lime & dark slate cybernetic startup symbol.
"""
import os
import math
from pathlib import Path
from PIL import Image, ImageDraw, ImageFilter

BASE_DIR = Path(__file__).resolve().parent
ICON_DIR = BASE_DIR / "Icona"
ICON_DIR.mkdir(exist_ok=True)

PNG_PATH = ICON_DIR / "icon.png"
ICO_PATH = ICON_DIR / "icon.ico"


def create_modern_startup_icon():
    # Base canvas 512x512 for supersampled anti-aliasing, then downscale to 256x256
    size = 512
    img = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)

    # 1. Subtle Outer Glow
    glow_img = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    glow_draw = ImageDraw.Draw(glow_img)
    glow_draw.rounded_rectangle([32, 32, size - 32, size - 32], radius=110, fill=(212, 248, 106, 35))
    glow_img = glow_img.filter(ImageFilter.GaussianBlur(radius=25))
    img.alpha_composite(glow_img)

    # 2. Main Squircle Base (Dark Obsidian Gradient Simulation)
    base_box = [40, 40, size - 40, size - 40]
    draw.rounded_rectangle(base_box, radius=100, fill=(14, 20, 29, 255))

    # Inner subtle background lighting
    inner_box = [46, 46, size - 46, size - 46]
    draw.rounded_rectangle(inner_box, radius=95, fill=(18, 25, 38, 255))

    # 3. Outer Neon Border (Electric Lime #D4F86A)
    draw.rounded_rectangle(base_box, radius=100, outline=(212, 248, 106, 230), width=8)

    # Secondary inner technical ring / accent ticks
    draw.rounded_rectangle([60, 60, size - 60, size - 60], radius=85, outline=(0, 230, 118, 90), width=3)

    # 4. Central Motif: Futuristic Supersonic Startup Rocket & Energy Chevron
    cx, cy = size // 2, size // 2

    # A. Propulsion Energy Rings (speed waves)
    for i, r in enumerate([90, 130]):
        alpha = 80 - (i * 30)
        draw.arc([cx - r, cy + 30 - r, cx + r, cy + 30 + r], start=30, end=150, fill=(212, 248, 106, alpha), width=5)

    # B. Cyber Jet Thruster Plasma Plume (Gradient orange-yellow to lime)
    thruster_pts = [
        (cx - 24, cy + 90),
        (cx + 24, cy + 90),
        (cx + 34, cy + 140),
        (cx, cy + 195),
        (cx - 34, cy + 140)
    ]
    draw.polygon(thruster_pts, fill=(212, 248, 106, 220))
    inner_flame = [
        (cx - 14, cy + 90),
        (cx + 14, cy + 90),
        (cx + 18, cy + 130),
        (cx, cy + 165),
        (cx - 18, cy + 130)
    ]
    draw.polygon(inner_flame, fill=(255, 255, 255, 240))

    # C. Rocket Wings / Stabilizers (Geometric sleek fins)
    left_fin = [
        (cx - 36, cy + 20),
        (cx - 105, cy + 105),
        (cx - 95, cy + 130),
        (cx - 40, cy + 95)
    ]
    draw.polygon(left_fin, fill=(0, 200, 110, 240))
    draw.polygon(left_fin, outline=(212, 248, 106, 255), width=4)

    right_fin = [
        (cx + 36, cy + 20),
        (cx + 105, cy + 105),
        (cx + 95, cy + 130),
        (cx + 40, cy + 95)
    ]
    draw.polygon(right_fin, fill=(0, 200, 110, 240))
    draw.polygon(right_fin, outline=(212, 248, 106, 255), width=4)

    # D. Rocket Fuselage Body (Aerodynamic dart)
    body_pts = [
        (cx, cy - 145),        # Sharp Nose Cone
        (cx + 42, cy - 35),
        (cx + 40, cy + 85),
        (cx - 40, cy + 85),
        (cx - 42, cy - 35)
    ]
    draw.polygon(body_pts, fill=(240, 246, 252, 255))
    draw.polygon(body_pts, outline=(212, 248, 106, 255), width=6)

    # Center fuselage split shading
    body_half = [
        (cx, cy - 145),
        (cx + 42, cy - 35),
        (cx + 40, cy + 85),
        (cx, cy + 85)
    ]
    draw.polygon(body_half, fill=(210, 225, 235, 255))

    # E. Circular Core Energy Reactor Window (Lime glowing port)
    reactor_center = (cx, cy + 10)
    rr = 28
    draw.ellipse([reactor_center[0] - rr, reactor_center[1] - rr, reactor_center[0] + rr, reactor_center[1] + rr], fill=(14, 20, 29, 255), outline=(212, 248, 106, 255), width=5)
    draw.ellipse([reactor_center[0] - 14, reactor_center[1] - 14, reactor_center[0] + 14, reactor_center[1] + 14], fill=(212, 248, 106, 255))
    draw.ellipse([reactor_center[0] - 6, reactor_center[1] - 6, reactor_center[0] + 6, reactor_center[1] + 6], fill=(255, 255, 255, 240))

    # F. High-tech Chevron Accents on Nose
    chevron_pts = [
        (cx, cy - 105),
        (cx + 18, cy - 70),
        (cx + 10, cy - 65),
        (cx, cy - 85),
        (cx - 10, cy - 65),
        (cx - 18, cy - 70)
    ]
    draw.polygon(chevron_pts, fill=(212, 248, 106, 255))

    # Resize down to 256x256 with high quality Lanczos resampling
    final_256 = img.resize((256, 256), Image.Resampling.LANCZOS)
    final_256.save(PNG_PATH, "PNG")
    print(f"Saved PNG to {PNG_PATH}")

    # Generate multi-size ICO: 256, 128, 64, 48, 32, 16
    sizes = [(256, 256), (128, 128), (64, 64), (48, 48), (32, 32), (16, 16)]
    final_256.save(ICO_PATH, format="ICO", sizes=sizes)
    print(f"Saved multi-resolution ICO to {ICO_PATH}")


if __name__ == "__main__":
    create_modern_startup_icon()
