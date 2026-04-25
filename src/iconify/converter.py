from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Iterable

from PIL import Image, ImageChops, ImageColor, ImageDraw, ImageOps

DEFAULT_SIZES = (16, 24, 32, 48, 64, 128, 256)
VALID_SHAPES = {"square", "rounded", "circle", "squircle"}


@dataclass(frozen=True)
class IconifyOptions:
    output: Path | None = None
    shape: str = "square"
    radius: int = 18
    sizes: tuple[int, ...] = field(default_factory=lambda: DEFAULT_SIZES)
    background: str = "transparent"
    padding: int = 0
    preview_png: Path | None = None


def convert_image(input_path: str | Path, options: IconifyOptions | None = None) -> Path:
    opts = options or IconifyOptions()
    source = Path(input_path).expanduser().resolve()
    if not source.exists():
        raise FileNotFoundError(f"Input image does not exist: {source}")

    sizes = normalize_sizes(opts.sizes)
    shape = opts.shape.lower()
    if shape not in VALID_SHAPES:
        raise ValueError(f"Unsupported shape '{opts.shape}'. Choose one of: {', '.join(sorted(VALID_SHAPES))}")

    output = (opts.output or source.with_suffix(".ico")).expanduser().resolve()
    output.parent.mkdir(parents=True, exist_ok=True)

    with Image.open(source) as opened:
        base = ImageOps.exif_transpose(opened).convert("RGBA")

    largest = max(sizes)
    primary = _render_icon(base, largest, shape, opts.radius, opts.background, opts.padding)
    primary.save(output, format="ICO", sizes=[(size, size) for size in sizes])

    if opts.preview_png:
        preview = opts.preview_png.expanduser().resolve()
        preview.parent.mkdir(parents=True, exist_ok=True)
        primary.save(preview, format="PNG")

    return output


def normalize_sizes(sizes: Iterable[int] | str) -> tuple[int, ...]:
    if isinstance(sizes, str):
        raw_values = [part.strip() for part in sizes.split(",") if part.strip()]
        parsed = [int(value) for value in raw_values]
    else:
        parsed = [int(value) for value in sizes]

    unique = sorted(set(parsed))
    if not unique:
        raise ValueError("At least one icon size is required.")
    invalid = [size for size in unique if size < 8 or size > 1024]
    if invalid:
        raise ValueError(f"Icon sizes must be between 8 and 1024 px: {invalid}")
    return tuple(unique)


def _render_icon(
    image: Image.Image,
    size: int,
    shape: str,
    radius_percent: int,
    background: str,
    padding_percent: int,
) -> Image.Image:
    canvas = _make_background(size, background)
    inset = max(0, min(45, padding_percent)) * size // 100
    content_size = max(1, size - (inset * 2))
    fitted = ImageOps.contain(image, (content_size, content_size), method=Image.Resampling.LANCZOS)
    x = inset + (content_size - fitted.width) // 2
    y = inset + (content_size - fitted.height) // 2
    canvas.alpha_composite(fitted, (x, y))

    mask = _shape_mask(size, shape, radius_percent)
    alpha = Image.new("L", (size, size), 0)
    alpha.paste(canvas.getchannel("A"))
    alpha = ImageChops.multiply(alpha, mask)
    canvas.putalpha(alpha)
    return canvas


def _make_background(size: int, background: str) -> Image.Image:
    if background.lower() in {"", "none", "transparent"}:
        return Image.new("RGBA", (size, size), (0, 0, 0, 0))
    color = ImageColor.getcolor(background, "RGBA")
    return Image.new("RGBA", (size, size), color)


def _shape_mask(size: int, shape: str, radius_percent: int) -> Image.Image:
    mask = Image.new("L", (size, size), 0)
    draw = ImageDraw.Draw(mask)
    bounds = (0, 0, size - 1, size - 1)

    if shape == "square":
        draw.rectangle(bounds, fill=255)
    elif shape == "circle":
        draw.ellipse(bounds, fill=255)
    elif shape == "rounded":
        radius = max(0, min(50, radius_percent)) * size // 100
        draw.rounded_rectangle(bounds, radius=radius, fill=255)
    elif shape == "squircle":
        radius = size * 32 // 100
        draw.rounded_rectangle(bounds, radius=radius, fill=255)
    else:
        raise ValueError(f"Unsupported shape: {shape}")

    return mask

