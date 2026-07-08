#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Lance Gestion Bisses, tente une mise à jour Git sûre et conserve un journal
lisible si l'application ne démarre pas.

Compatible avec Python 3.8 et versions suivantes.
"""

from __future__ import annotations

import glob
import os
import shutil
import subprocess
import sys
import traceback
from datetime import datetime
from pathlib import Path
from typing import Optional


APP_DIR = Path(__file__).resolve().parent
APP_SCRIPT = APP_DIR / "gestion_bisses.py"
LOG_FILE = APP_DIR / "lancement_gestion_bisses.log"


def log(message: str) -> None:
    line = "[{}] {}".format(
        datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        message,
    )
    print(line)
    try:
        with LOG_FILE.open("a", encoding="utf-8") as handle:
            handle.write(line + "\n")
    except Exception:
        pass


def show_error(title: str, message: str) -> None:
    """Affiche une boîte Windows si possible, sinon laisse le message dans la console."""
    log("{} : {}".format(title, message))
    try:
        import tkinter as tk
        from tkinter import messagebox

        root = tk.Tk()
        root.withdraw()
        messagebox.showerror(title, message)
        root.destroy()
    except Exception:
        pass


def find_git() -> Optional[str]:
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


def run_git(git: str, *args: str) -> subprocess.CompletedProcess:
    return subprocess.run(
        [git, *args],
        cwd=str(APP_DIR),
        text=True,
        capture_output=True,
        check=False,
    )


def update_from_github() -> None:
    git = find_git()
    if not git:
        log("Git introuvable : lancement sans mise à jour automatique.")
        return

    if not (APP_DIR / ".git").exists():
        log("Ce dossier n'est pas un clone Git : lancement de la version locale.")
        return

    status = run_git(git, "status", "--porcelain", "--untracked-files=no")
    if status.returncode != 0:
        log(
            "Impossible de vérifier l'état Git : {}".format(
                (status.stderr or "").strip()
            )
        )
        return

    if (status.stdout or "").strip():
        log(
            "Mise à jour automatique ignorée : des fichiers suivis "
            "ont des modifications locales."
        )
        log((status.stdout or "").strip())
        return

    log("Recherche d'une mise à jour GitHub...")
    result = run_git(git, "pull", "--ff-only")

    if result.returncode == 0:
        log((result.stdout or "").strip() or "Dépôt déjà à jour.")
    else:
        log("Mise à jour impossible : lancement de la version locale.")
        if (result.stderr or "").strip():
            log((result.stderr or "").strip())


def launch_application() -> int:
    if not APP_SCRIPT.exists():
        show_error(
            "Gestion Bisses",
            "Fichier introuvable :\n{}\n\n"
            "Le lanceur doit se trouver dans le même dossier que gestion_bisses.py."
            .format(APP_SCRIPT),
        )
        return 1

    log("Python utilisé : {}".format(sys.executable))
    log("Lancement de : {}".format(APP_SCRIPT))

    result = subprocess.run(
        [sys.executable, str(APP_SCRIPT)],
        cwd=str(APP_DIR),
        check=False,
    )

    if result.returncode != 0:
        show_error(
            "Gestion Bisses ne s'est pas lancé",
            "L'application s'est arrêtée avec le code {}.\n\n"
            "Consultez le fichier :\n{}\n\n"
            "Vous pouvez aussi lancer lancer_gestion_bisses.bat afin que "
            "la fenêtre reste ouverte et affiche l'erreur."
            .format(result.returncode, LOG_FILE),
        )

    return int(result.returncode)


def main() -> int:
    try:
        log("=" * 60)
        update_from_github()
        return launch_application()
    except Exception:
        details = traceback.format_exc()
        log(details)
        show_error(
            "Erreur du lanceur Gestion Bisses",
            "Une erreur inattendue s'est produite.\n\n"
            "Le détail a été enregistré dans :\n{}".format(LOG_FILE),
        )
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
