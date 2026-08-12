#!/usr/bin/env python3
"""Build and validate Lumina's platform icons from the canonical PNG master."""

from __future__ import annotations

import argparse
import shutil
import sys
import tempfile
from pathlib import Path

try:
    from PIL import Image, ImageDraw
except ImportError as exc:  # pragma: no cover - dependency guidance for local tooling
    raise SystemExit(
        "Pillow is required. Install frontend/scripts/requirements-icons.txt first."
    ) from exc


ASSET_DIR = Path(__file__).resolve().parent.parent / "assets"
MASTER_PATH = ASSET_DIR / "lumina-app-icon.png"
ICNS_PATH = ASSET_DIR / "lumina-app-icon.icns"
ICO_PATH = ASSET_DIR / "lumina-app-icon.ico"

MASTER_SIZE = 1024
TARGET_BACKGROUND = (28, 28, 30)
ORIGINAL_CORNER = (1, 4, 14)
BACKGROUND_FADE_START = 16.0
BACKGROUND_FADE_END = 72.0
WINDOWS_CORNER_RADIUS_RATIO = 0.2237

ICNS_PIXEL_SIZES = (32, 64, 128, 256, 512, 1024)
ICNS_LOGICAL_SIZES = {
    (16, 16, 2),
    (32, 32, 2),
    (128, 128, 1),
    (128, 128, 2),
    (256, 256, 1),
    (256, 256, 2),
    (512, 512, 1),
    (512, 512, 2),
}
ICO_SIZES = (16, 24, 32, 48, 64, 128, 256)


def load_master() -> Image.Image:
    with Image.open(MASTER_PATH) as source:
        if source.mode != "RGBA":
            raise ValueError(f"master must use RGBA mode, got {source.mode}")
        image = source.convert("RGBA")
    if image.size != (MASTER_SIZE, MASTER_SIZE):
        raise ValueError(f"master must be {MASTER_SIZE}x{MASTER_SIZE}, got {image.size}")
    if image.getchannel("A").getextrema() != (255, 255):
        raise ValueError("master must be fully opaque so macOS can apply its native mask")
    return image


def smoothstep(value: float) -> float:
    value = max(0.0, min(1.0, value))
    return value * value * (3.0 - 2.0 * value)


def lighten_master_background() -> None:
    """Apply the approved charcoal lift once, preserving every bright subject pixel."""
    image = load_master()
    corner = image.getpixel((0, 0))[:3]
    if corner == TARGET_BACKGROUND:
        print(f"Master already uses #{''.join(f'{value:02X}' for value in corner)}")
        return
    if corner != ORIGINAL_CORNER:
        raise ValueError(
            f"unexpected master corner {corner}; expected {ORIGINAL_CORNER} before calibration"
        )

    delta = tuple(
        TARGET_BACKGROUND[index] - ORIGINAL_CORNER[index] for index in range(3)
    )
    pixels = image.load()
    changed = 0
    preserved_bright = 0
    for y in range(image.height):
        for x in range(image.width):
            red, green, blue, alpha = pixels[x, y]
            luminance = (54 * red + 183 * green + 19 * blue) / 256
            if luminance >= BACKGROUND_FADE_END:
                preserved_bright += 1
                continue
            fade = (BACKGROUND_FADE_END - luminance) / (
                BACKGROUND_FADE_END - BACKGROUND_FADE_START
            )
            weight = smoothstep(fade)
            adjusted = (
                round(min(255, red + delta[0] * weight)),
                round(min(255, green + delta[1] * weight)),
                round(min(255, blue + delta[2] * weight)),
                alpha,
            )
            if adjusted != pixels[x, y]:
                changed += 1
                pixels[x, y] = adjusted

    if image.getpixel((0, 0))[:3] != TARGET_BACKGROUND:
        raise ValueError("background calibration did not reach the target corner color")
    image.save(MASTER_PATH, format="PNG", compress_level=9)
    print(
        f"Calibrated {changed} dark pixels to the #{''.join(f'{value:02X}' for value in TARGET_BACKGROUND)} palette; "
        f"preserved {preserved_bright} bright pixels exactly"
    )


def resize(image: Image.Image, size: int) -> Image.Image:
    return image.resize((size, size), Image.Resampling.LANCZOS)


def build_icns(master: Image.Image, destination: Path) -> None:
    frames = [resize(master, size) for size in ICNS_PIXEL_SIZES[:-1]]
    master.save(destination, format="ICNS", append_images=frames)


def rounded_mask(size: int) -> Image.Image:
    scale = 8
    canvas_size = size * scale
    mask = Image.new("L", (canvas_size, canvas_size), 0)
    radius = round(canvas_size * WINDOWS_CORNER_RADIUS_RATIO)
    ImageDraw.Draw(mask).rounded_rectangle(
        (0, 0, canvas_size - 1, canvas_size - 1),
        radius=radius,
        fill=255,
    )
    mask = mask.resize((size, size), Image.Resampling.LANCZOS)
    return mask.point(lambda value: 0 if value <= 3 else 255 if value >= 252 else value)


def build_ico(master: Image.Image, destination: Path) -> None:
    frames: list[Image.Image] = []
    for size in ICO_SIZES:
        frame = resize(master, size)
        frame.putalpha(rounded_mask(size))
        frames.append(frame)
    frames[-1].save(
        destination,
        format="ICO",
        sizes=[(size, size) for size in ICO_SIZES],
        append_images=frames[:-1],
    )


def icns_pixels(path: Path) -> dict[tuple[int, int, int], bytes]:
    with Image.open(path) as icon:
        sizes = set(icon.info.get("sizes", []))
        if sizes != ICNS_LOGICAL_SIZES:
            raise ValueError(
                f"ICNS sizes are {sorted(sizes)}, expected {sorted(ICNS_LOGICAL_SIZES)}"
            )
        return {
            size: icon.icns.getimage(size).convert("RGBA").tobytes() for size in sizes
        }


def ico_pixels(path: Path) -> dict[tuple[int, int], bytes]:
    with Image.open(path) as icon:
        frames = {}
        for size in icon.ico.sizes():
            frames[size] = icon.ico.getimage(size).convert("RGBA").tobytes()
        return frames


def validate_master(master: Image.Image) -> None:
    border_points = (
        (0, 0),
        (MASTER_SIZE // 2, 0),
        (MASTER_SIZE - 1, 0),
        (0, MASTER_SIZE // 2),
        (MASTER_SIZE - 1, MASTER_SIZE // 2),
        (0, MASTER_SIZE - 1),
        (MASTER_SIZE - 1, MASTER_SIZE - 1),
    )
    for point in border_points:
        color = master.getpixel(point)[:3]
        if max(abs(color[index] - TARGET_BACKGROUND[index]) for index in range(3)) > 2:
            raise ValueError(f"master border at {point} is {color}, outside target tolerance")


def validate_icns(path: Path) -> None:
    with Image.open(path) as icon:
        sizes = set(icon.info.get("sizes", []))
        if sizes != ICNS_LOGICAL_SIZES:
            raise ValueError(
                f"ICNS sizes are {sorted(sizes)}, expected {sorted(ICNS_LOGICAL_SIZES)}"
            )
        for size in sizes:
            frame = icon.icns.getimage(size).convert("RGBA")
            if frame.getchannel("A").getextrema() != (255, 255):
                raise ValueError(f"ICNS frame {size} must remain unmasked and opaque")


def validate_ico(path: Path) -> None:
    with Image.open(path) as icon:
        sizes = icon.ico.sizes()
        expected = {(size, size) for size in ICO_SIZES}
        if sizes != expected:
            raise ValueError(f"ICO sizes are {sorted(sizes)}, expected {sorted(expected)}")
        for size in expected:
            frame = icon.ico.getimage(size).convert("RGBA")
            alpha = frame.getchannel("A")
            if frame.getpixel((0, 0))[3] != 0:
                raise ValueError(f"ICO {size[0]}px corner is not transparent")
            if frame.getpixel((size[0] // 2, size[1] // 2))[3] != 255:
                raise ValueError(f"ICO {size[0]}px center is not opaque")
            if alpha.getextrema() != (0, 255):
                raise ValueError(f"ICO {size[0]}px lacks a valid antialiased mask")
            if not any(alpha.histogram()[1:255]):
                raise ValueError(f"ICO {size[0]}px mask is not antialiased")


def build_outputs(icns_path: Path, ico_path: Path) -> None:
    master = load_master()
    validate_master(master)
    build_icns(master, icns_path)
    build_ico(master, ico_path)
    validate_icns(icns_path)
    validate_ico(ico_path)


def build() -> None:
    with tempfile.TemporaryDirectory(prefix="lumina-icon-build-") as temp_dir:
        temp_root = Path(temp_dir)
        generated_icns = temp_root / ICNS_PATH.name
        generated_ico = temp_root / ICO_PATH.name
        build_outputs(generated_icns, generated_ico)
        shutil.copyfile(generated_icns, ICNS_PATH)
        shutil.copyfile(generated_ico, ICO_PATH)
    print(f"Built {ICNS_PATH.relative_to(ASSET_DIR.parent)} and {ICO_PATH.relative_to(ASSET_DIR.parent)}")


def check() -> None:
    master = load_master()
    validate_master(master)
    validate_icns(ICNS_PATH)
    validate_ico(ICO_PATH)
    with tempfile.TemporaryDirectory(prefix="lumina-icon-check-") as temp_dir:
        temp_root = Path(temp_dir)
        generated_icns = temp_root / ICNS_PATH.name
        generated_ico = temp_root / ICO_PATH.name
        build_outputs(generated_icns, generated_ico)
        if icns_pixels(generated_icns) != icns_pixels(ICNS_PATH):
            raise ValueError("committed ICNS pixels do not match the PNG master")
        if ico_pixels(generated_ico) != ico_pixels(ICO_PATH):
            raise ValueError("committed ICO pixels do not match the PNG master")
    print("PNG master, ICNS, and ICO are valid and visually consistent")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    action = parser.add_mutually_exclusive_group()
    action.add_argument("--build", action="store_true", help="rebuild ICNS and ICO")
    action.add_argument("--check", action="store_true", help="validate committed assets")
    action.add_argument(
        "--lighten-background",
        action="store_true",
        help="apply the approved one-time charcoal calibration to the PNG master",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    try:
        if args.lighten_background:
            lighten_master_background()
        elif args.check:
            check()
        else:
            build()
    except (OSError, RuntimeError, ValueError) as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
