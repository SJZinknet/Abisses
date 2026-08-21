#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"
cd "$PROJECT_ROOT"

VERSION="$(tr -d '[:space:]' < VERSION)"
if [[ -z "$VERSION" ]]; then
    echo "VERSION est vide." >&2
    exit 1
fi

# Le caractère ~ place correctement une bêta avant la version stable dans
# l'ordre des versions Debian.
DEB_VERSION="${VERSION/-beta./~beta}"
DEB_VERSION="${DEB_VERSION/-rc./~rc}"

PKGROOT="$PROJECT_ROOT/build/deb/abisses"
RELEASE_DIR="$PROJECT_ROOT/release"

rm -rf "$PKGROOT"
mkdir -p \
    "$PKGROOT/DEBIAN" \
    "$PKGROOT/usr/lib/abisses" \
    "$PKGROOT/usr/bin" \
    "$PKGROOT/usr/share/applications" \
    "$PKGROOT/usr/share/icons/hicolor/512x512/apps" \
    "$RELEASE_DIR"

cp -a "$PROJECT_ROOT/dist/Abisses/." "$PKGROOT/usr/lib/abisses/"
install -m 0755 "$SCRIPT_DIR/abisses" "$PKGROOT/usr/bin/abisses"
install -m 0644 "$SCRIPT_DIR/abisses.desktop" "$PKGROOT/usr/share/applications/abisses.desktop"
install -m 0644 "$PROJECT_ROOT/packaging/icons/abisses.png" \
    "$PKGROOT/usr/share/icons/hicolor/512x512/apps/abisses.png"

sed "s/@VERSION@/$DEB_VERSION/g" "$SCRIPT_DIR/control.template" > "$PKGROOT/DEBIAN/control"
install -m 0755 "$SCRIPT_DIR/postinst" "$PKGROOT/DEBIAN/postinst"
install -m 0755 "$SCRIPT_DIR/postrm" "$PKGROOT/DEBIAN/postrm"

dpkg-deb --root-owner-group --build \
    "$PKGROOT" \
    "$RELEASE_DIR/abisses_${VERSION}_amd64.deb"

echo "Paquet Ubuntu créé : release/abisses_${VERSION}_amd64.deb"
