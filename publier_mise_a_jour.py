#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Publie une mise à jour du logiciel sur GitHub.

Pré-requis :
- dépôt cloné et authentifié;
- Git disponible;
- branche de travail propre en dehors des fichiers à publier.

Le script :
1. vérifie la syntaxe de gestion_bisses.py;
2. montre les changements;
3. demande une validation humaine;
4. commit et push;
5. peut créer un tag de version, ce qui déclenche la Release GitHub.
"""

from __future__ import annotations

import ast
import shutil
import subprocess
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parent
APP = ROOT / "gestion_bisses.py"
VERSION_FILE = ROOT / "VERSION"


def run(*args: str, capture: bool = False) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        list(args),
        cwd=ROOT,
        text=True,
        capture_output=capture,
        check=False,
    )


def fail(message: str) -> int:
    print("❌", message)
    return 1


def main() -> int:
    git = shutil.which("git")
    if not git:
        return fail("Git n'est pas disponible dans le PATH.")

    if not (ROOT / ".git").exists():
        return fail("Ce dossier n'est pas un dépôt Git cloné.")

    if not APP.exists():
        return fail("gestion_bisses.py est introuvable.")

    try:
        source = APP.read_text(encoding="utf-8")
        ast.parse(source)
        compile(source, str(APP), "exec")
    except Exception as exc:
        return fail(f"Syntaxe Python invalide : {exc}")

    print("✅ Syntaxe Python vérifiée.\n")
    run(git, "status", "--short")

    answer = input(
        "\nPublier tous les changements suivis du logiciel ? "
        "Tapez PUBLIER pour confirmer : "
    ).strip()
    if answer != "PUBLIER":
        print("Annulé.")
        return 0

    message = input("Message de mise à jour : ").strip()
    if not message:
        message = "Mise à jour Gestion Bisses"

    files = [
        "gestion_bisses.py",
        "lancer_gestion_bisses.py",
        "publier_mise_a_jour.py",
        "requirements.txt",
        "README.md",
        "CHANGELOG.md",
        "VERSION",
        ".gitignore",
        ".github",
        "docs",
        "installer_dependances.bat",
        "lancer_gestion_bisses.bat",
    ]

    add_result = run(git, "add", "--", *files)
    if add_result.returncode != 0:
        return fail("git add a échoué.")

    diff = run(git, "diff", "--cached", "--quiet")
    if diff.returncode == 0:
        print("Aucun changement à publier.")
        return 0

    commit = run(git, "commit", "-m", message)
    if commit.returncode != 0:
        return fail("git commit a échoué.")

    push = run(git, "push")
    if push.returncode != 0:
        return fail("git push a échoué.")

    print("✅ Mise à jour envoyée sur GitHub.")

    version = input(
        "Créer aussi une Release ? Entrez une version (ex. 0.50.0), "
        "ou laissez vide : "
    ).strip()

    if not version:
        return 0

    tag = version if version.startswith("v") else f"v{version}"
    VERSION_FILE.write_text(version.lstrip("v") + "\n", encoding="utf-8")
    run(git, "add", "VERSION")
    run(git, "commit", "-m", f"Version {tag}")

    tag_result = run(git, "tag", "-a", tag, "-m", f"Gestion Bisses {tag}")
    if tag_result.returncode != 0:
        return fail(f"Impossible de créer le tag {tag}.")

    push_result = run(git, "push", "origin", "HEAD", tag)
    if push_result.returncode != 0:
        return fail("Impossible d'envoyer le tag sur GitHub.")

    print(
        "✅ Tag envoyé. GitHub Actions va préparer automatiquement "
        "la Release téléchargeable."
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
