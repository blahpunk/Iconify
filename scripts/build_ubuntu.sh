#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT"

python3 -m venv .venv
. .venv/bin/activate
python -m pip install --upgrade pip
python -m pip install -e . -r requirements-dev.txt
pyinstaller installer/pyinstaller/iconify.spec --noconfirm

VERSION="$(python - <<'PY'
from iconify import __version__
print(__version__)
PY
)"
PKGROOT="dist/deb/iconify_${VERSION}_amd64"
rm -rf "$PKGROOT"
mkdir -p "$PKGROOT/DEBIAN" "$PKGROOT/opt/iconify" "$PKGROOT/usr/share/applications" "$PKGROOT/usr/share/doc/iconify"

cp -R "dist/Iconify/"* "$PKGROOT/opt/iconify/"
cp icon.ico "$PKGROOT/opt/iconify/icon.ico"
chmod 755 "$PKGROOT/opt/iconify/iconify"
cp installer/linux/iconify.desktop "$PKGROOT/usr/share/applications/iconify.desktop"
cp README.md LICENSE "$PKGROOT/usr/share/doc/iconify/"

cat > "$PKGROOT/DEBIAN/control" <<CONTROL
Package: iconify
Version: ${VERSION}
Section: graphics
Priority: optional
Architecture: amd64
Maintainer: Iconify contributors
Description: Pro-level image-to-icon converter with GUI and CLI
CONTROL

dpkg-deb --build "$PKGROOT" "dist/iconify_${VERSION}_amd64.deb"
echo "Ubuntu package written to dist/iconify_${VERSION}_amd64.deb"
