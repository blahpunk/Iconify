# Iconify

Iconify is a pro-level image-to-icon tool with both a native GUI and command-line usage. Drop in a source image and it produces a high-quality multi-size icon, ready for Windows apps, launchers, shortcuts, and packaging workflows.

## Highlights

- Converts common image formats to `.ico`
- Generates all standard icon sizes by default: `16, 24, 32, 48, 64, 128, 256`
- Preserves transparency and uses high-quality Lanczos resampling
- Optional square, rounded, circle, and squircle masks
- Native GUI with live scaling preview, transparent default background, hex entry, and color picker
- CLI-first workflow for scripts and build systems
- Installer recipes for Windows and Ubuntu that put `iconify` on the system path

## Quick Start

```bash
iconify monalisa.png
```

That creates `monalisa.ico` next to the source file.

```bash
iconify monalisa.png -o assets/app.ico --shape rounded --radius 24
iconify logo.png --shape circle
iconify source.png --sizes 16,32,48,256
```

Launch the GUI:

```bash
iconify
```

## CLI

```text
usage: iconify [image] [-o OUTPUT] [--shape square|rounded|circle|squircle]
               [--radius PERCENT] [--sizes LIST] [--background COLOR]
               [--padding PERCENT] [--preview-png PATH]
```

Options:

- `image`: input image. If omitted, Iconify opens the GUI.
- `-o, --output`: output path. Defaults to the input filename with `.ico`.
- `--shape`: icon mask style. Defaults to `square`.
- `--radius`: rounded-corner radius as a percentage of icon size. Defaults to `18`.
- `--sizes`: comma-separated icon sizes. Defaults to `16,24,32,48,64,128,256`.
- `--background`: optional background color for transparent or translucent images, such as `#ffffff` or `transparent`.
- `--padding`: inset the image before masking, as a percentage of size.
- `--preview-png`: additionally write a 256px PNG preview of the final masked icon.

## Development

Create a virtual environment and install the project:

```bash
python -m venv .venv
.venv\Scripts\activate
python -m pip install -e ".[dev]"
```

On Linux/macOS:

```bash
python -m venv .venv
source .venv/bin/activate
python -m pip install -e ".[dev]"
```

Run the app:

```bash
python -m iconify
python -m iconify examples/source.png --shape squircle
```

## Building Installers

Windows:

```powershell
.\scripts\build_windows.ps1
```

The Windows build script creates a PyInstaller executable and, when Inno Setup is installed, builds an installer that adds Iconify to the system `PATH` and creates Start Menu/File Explorer launch points.

Ubuntu:

```bash
./scripts/build_ubuntu.sh
```

The Ubuntu build script creates a `.deb` package that installs `/usr/bin/iconify` and a desktop entry so the GUI appears in app launchers and file explorer workflows.

## License

MIT
