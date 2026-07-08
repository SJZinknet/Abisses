#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Lance Gestion Bisses après une mise à jour Git sûre.

- tente `git pull --ff-only`;
- ne tire rien si des fichiers suivis ont été modifiés localement;
- continue avec la version installée si GitHub ou Git n'est pas disponible;
- ne touche jamais à Gestion_Bisses_Data (ignoré par Git).
"""

from __future__ import annotations

import glob
import os
import shutil
import subprocess
import sys
from pathlib import Path


APP_DIR = Path(__file__).resolve().parent
APP_SCRIPT = APP_DIR / "gestion_bisses.py"


def find_git() -> str | None:
    found = shutil.which("git")
    if found:
        return found

    local_app_data = os.environ.get("LOCALAPPDATA", "")
    if local_app_data:
        patterns = [
            os.path.join(
                local_app_data,
                "GitHubDesktop",
                "app-*",
                "resources",
                "app",
                "git",
                "cmd",
                "git.exe",
            ),
            os.path.join(
                local_app_data,
                "Programs",
                "Git",
                "cmd",
                "git.exe",
            ),
        ]
        candidates = []
        for pattern in patterns:
            candidates.extend(glob.glob(pattern))
        if candidates:
            candidates.sort(reverse=True)
            return candidates[0]

    return None


def run_git(git: str, *args: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [git, *args],
        cwd=APP_DIR,
        text=True,
        capture_output=True,
        check=False,
    )


def update_from_github() -> None:
    git = find_git()
    if not git:
        print("ℹ️ Git introuvable : lancement sans mise à jour automatique.")
        return

    if not (APP_DIR / ".git").exists():
        print("ℹ️ Ce dossier n'est pas encore un clone Git : lancement direct.")
        return

    status = run_git(git, "status", "--porcelain", "--untracked-files=no")
    if status.returncode != 0:
        print("⚠️ Impossible de vérifier l'état Git :", status.stderr.strip())
        return

    if status.stdout.strip():
        print(
            "⚠️ Mise à jour automatique ignorée : des fichiers suivis ont "
            "des modifications locales."
        )
        print(status.stdout.strip())
        return

    print("🔄 Recherche d'une mise à jour GitHub…")
    result = run_git(git, "pull", "--ff-only")
    if result.returncode == 0:
        message = result.stdout.strip() or "Dépôt déjà à jour."
        print("✅", message)
    else:
        print("⚠️ Mise à jour impossible, lancement de la version locale.")
        if result.stderr.strip():
            print(result.stderr.strip())


def main() -> int:
    update_from_github()

    if not APP_SCRIPT.exists():
        print(f"❌ Fichier introuvable : {APP_SCRIPT}")
        return 1

    os.chdir(APP_DIR)
    os.execv(sys.executable, [sys.executable, str(APP_SCRIPT)])
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
