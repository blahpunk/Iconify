from __future__ import annotations

import argparse
import sys
from pathlib import Path

from .converter import DEFAULT_SIZES, IconifyOptions, convert_image, normalize_sizes


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="iconify",
        description="Convert images to high-quality multi-size icons, or launch the GUI.",
    )
    parser.add_argument("image", nargs="?", help="Input image. Omit to launch the GUI.")
    parser.add_argument("-o", "--output", type=Path, help="Output .ico path.")
    parser.add_argument(
        "--shape",
        choices=["square", "rounded", "circle", "squircle"],
        default="square",
        help="Mask shape to apply to the icon.",
    )
    parser.add_argument(
        "--radius",
        type=int,
        default=18,
        help="Rounded-corner radius as a percent of icon size.",
    )
    parser.add_argument(
        "--sizes",
        default=",".join(str(size) for size in DEFAULT_SIZES),
        help="Comma-separated icon sizes.",
    )
    parser.add_argument(
        "--background",
        default="transparent",
        help="Background color such as #ffffff, rgb(255,255,255), or transparent.",
    )
    parser.add_argument(
        "--padding",
        type=int,
        default=0,
        help="Inset image content by this percentage before masking.",
    )
    parser.add_argument("--preview-png", type=Path, help="Also write a 256px PNG preview.")
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    if not args.image:
        from .gui import run

        run()
        return 0

    try:
        sizes = normalize_sizes(args.sizes)
        output = convert_image(
            args.image,
            IconifyOptions(
                output=args.output,
                shape=args.shape,
                radius=args.radius,
                sizes=sizes,
                background=args.background,
                padding=args.padding,
                preview_png=args.preview_png,
            ),
        )
    except Exception as exc:
        print(f"iconify: {exc}", file=sys.stderr)
        return 2

    print(output)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

