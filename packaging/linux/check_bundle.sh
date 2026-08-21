#!/usr/bin/env bash
set -euo pipefail

BUNDLE_DIR="${1:-dist/Abisses}"
if [[ ! -d "$BUNDLE_DIR" ]]; then
    echo "Dossier PyInstaller introuvable : $BUNDLE_DIR" >&2
    exit 1
fi

missing=0
bundle_library_path="$BUNDLE_DIR/_internal${LD_LIBRARY_PATH:+:$LD_LIBRARY_PATH}"
while IFS= read -r -d '' candidate; do
    if ! file "$candidate" | grep -q 'ELF'; then
        continue
    fi
    # Le bootloader PyInstaller ajoute _internal à LD_LIBRARY_PATH au
    # démarrage ; le contrôle doit reproduire exactement ce contexte.
    report="$(LD_LIBRARY_PATH="$bundle_library_path" ldd "$candidate" 2>/dev/null || true)"
    if grep -q 'not found' <<<"$report"; then
        echo "Bibliothèque manquante pour $candidate" >&2
        grep 'not found' <<<"$report" >&2
        missing=1
    fi
done < <(find "$BUNDLE_DIR" -type f -print0)

if [[ "$missing" -ne 0 ]]; then
    exit 1
fi

echo "Toutes les dépendances ELF du paquet sont résolues."
