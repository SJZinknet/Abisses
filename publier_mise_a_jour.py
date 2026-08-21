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

    python_files = [
        APP,
        ROOT / "abisses_paths.py",
        ROOT / "abisses_update.py",
        ROOT / "abisses_update_ui.py",
        ROOT / "lancer_gestion_bisses.py",
    ]
    try:
        for path in python_files:
            source = path.read_text(encoding="utf-8")
            ast.parse(source)
            compile(source, str(path), "exec")
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
        message = "Mise à jour Abisses"

    # Cet ancien journal a été suivi par erreur dans les premières versions.
    # Il reste sur l'ordinateur comme diagnostic local, mais n'est plus envoyé
    # sur GitHub (le lanceur v55 écrit désormais dans le profil utilisateur).
    legacy_log = "lancement_gestion_bisses.log"
    tracked_log = run(git, "ls-files", "--error-unmatch", legacy_log)
    if tracked_log.returncode == 0:
        untrack_log = run(git, "rm", "--cached", "--ignore-unmatch", legacy_log)
        if untrack_log.returncode != 0:
            return fail(f"Impossible de retirer {legacy_log} du suivi Git.")
        print(f"✅ {legacy_log} retiré du dépôt (conservé sur l'ordinateur).")

    files = [
        "gestion_bisses.py",
        "abisses_paths.py",
        "abisses_update.py",
        "abisses_update_ui.py",
        "lancer_gestion_bisses.py",
        "publier_mise_a_jour.py",
        "requirements.txt",
        "requirements-build.txt",
        "requirements-build-lock.txt",
        "README.md",
        "CHANGELOG.md",
        "VERSION",
        ".gitignore",
        ".gitattributes",
        ".github",
        "packaging",
        "tests",
        "docs",
        "installer_dependances.bat",
        "lancer_gestion_bisses.bat",
    ]

    add_result = run(git, "add", "--", *files)
    if add_result.returncode != 0:
        return fail("git add a échoué.")

    diff = run(git, "diff", "--cached", "--quiet")
    if diff.returncode == 0:
        print("Aucun nouveau changement à commiter ; poursuite vers la Release.")
    else:
        commit = run(git, "commit", "-m", message)
        if commit.returncode != 0:
            return fail("git commit a échoué.")

    push = run(git, "push")
    if push.returncode != 0:
        return fail("git push a échoué.")

    print("✅ Branche envoyée sur GitHub.")

    version = input(
        "Créer aussi une Release ? Entrez une version (ex. 0.55.0-beta.1), "
        "ou laissez vide : "
    ).strip()

    if not version:
        return 0

    tag = version if version.startswith("v") else f"v{version}"
    normalized_version = version.lstrip("v")
    current_version = VERSION_FILE.read_text(encoding="utf-8").strip()
    if current_version != normalized_version:
        VERSION_FILE.write_text(normalized_version + "\n", encoding="utf-8")
        run(git, "add", "VERSION")
        version_commit = run(git, "commit", "-m", f"Version {tag}")
        if version_commit.returncode != 0:
            return fail("Impossible de commiter le nouveau fichier VERSION.")
        version_push = run(git, "push")
        if version_push.returncode != 0:
            return fail("Impossible d'envoyer le nouveau fichier VERSION.")

    existing_tag = run(git, "rev-parse", "--verify", f"refs/tags/{tag}", capture=True)
    if existing_tag.returncode == 0:
        return fail(f"Le tag {tag} existe déjà.")

    tag_result = run(git, "tag", "-a", tag, "-m", f"Abisses {tag}")
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
