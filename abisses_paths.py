"""Chemins locaux et migration des réglages d'Abisses.

Le code de l'application peut être installé dans un dossier protégé. Tous les
éléments écrits par Abisses (réglages, journaux et cache de mise à jour) vivent
donc dans le profil de l'utilisateur. ``Gestion_Bisses_Data`` reste un dossier
métier choisi par l'utilisateur ; seul son emplacement par défaut change.
"""

from __future__ import annotations

import json
import os
import re
import shutil
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Mapping, Optional, Union

APP_NAME = "Abisses"
PathLike = Union[str, os.PathLike]


def is_frozen_application() -> bool:
    """Indique si le programme s'exécute depuis un paquet PyInstaller."""
    return bool(getattr(sys, "frozen", False) and hasattr(sys, "_MEIPASS"))


def get_application_dir() -> Path:
    """Dossier du programme exécutable ou, en développement, du dépôt."""
    if is_frozen_application():
        return Path(sys.executable).resolve().parent
    return Path(__file__).resolve().parent


def get_resource_dir() -> Path:
    """Dossier des ressources incluses dans l'application."""
    if is_frozen_application():
        return Path(getattr(sys, "_MEIPASS")).resolve()
    return Path(__file__).resolve().parent


def resource_path(name: str) -> Path:
    return get_resource_dir() / name


def _platform_name(platform_name: Optional[str] = None) -> str:
    return str(platform_name or sys.platform).lower()


def _environment(environ: Optional[Mapping[str, str]] = None) -> Mapping[str, str]:
    return os.environ if environ is None else environ


def _home_path(home: Optional[PathLike] = None) -> Path:
    return Path(home).expanduser() if home is not None else Path.home()


def get_user_config_dir(
    platform_name: Optional[str] = None,
    environ: Optional[Mapping[str, str]] = None,
    home: Optional[PathLike] = None,
) -> Path:
    platform_value = _platform_name(platform_name)
    env = _environment(environ)

    if platform_value.startswith("win"):
        base = env.get("LOCALAPPDATA") or env.get("APPDATA")
        if base:
            return Path(base) / APP_NAME
        return _home_path(home) / "AppData" / "Local" / APP_NAME
    if platform_value == "darwin":
        return _home_path(home) / "Library" / "Application Support" / APP_NAME

    base = env.get("XDG_CONFIG_HOME")
    return (Path(base) if base else _home_path(home) / ".config") / APP_NAME


def get_user_data_dir(
    platform_name: Optional[str] = None,
    environ: Optional[Mapping[str, str]] = None,
    home: Optional[PathLike] = None,
) -> Path:
    platform_value = _platform_name(platform_name)
    env = _environment(environ)

    if platform_value.startswith("win"):
        base = env.get("LOCALAPPDATA") or env.get("APPDATA")
        if base:
            return Path(base) / APP_NAME
        return _home_path(home) / "AppData" / "Local" / APP_NAME
    if platform_value == "darwin":
        return _home_path(home) / "Library" / "Application Support" / APP_NAME

    base = env.get("XDG_DATA_HOME")
    return (Path(base) if base else _home_path(home) / ".local" / "share") / APP_NAME


def get_user_log_dir(
    platform_name: Optional[str] = None,
    environ: Optional[Mapping[str, str]] = None,
    home: Optional[PathLike] = None,
) -> Path:
    platform_value = _platform_name(platform_name)
    env = _environment(environ)

    if platform_value.startswith("win"):
        return get_user_data_dir(platform_value, env, home) / "logs"
    if platform_value == "darwin":
        return _home_path(home) / "Library" / "Logs" / APP_NAME

    base = env.get("XDG_STATE_HOME")
    return (Path(base) if base else _home_path(home) / ".local" / "state") / APP_NAME / "logs"


def get_user_cache_dir(
    platform_name: Optional[str] = None,
    environ: Optional[Mapping[str, str]] = None,
    home: Optional[PathLike] = None,
) -> Path:
    platform_value = _platform_name(platform_name)
    env = _environment(environ)

    if platform_value.startswith("win"):
        return get_user_data_dir(platform_value, env, home) / "cache"
    if platform_value == "darwin":
        return _home_path(home) / "Library" / "Caches" / APP_NAME

    base = env.get("XDG_CACHE_HOME")
    return (Path(base) if base else _home_path(home) / ".cache") / APP_NAME


def settings_file_path() -> Path:
    return get_user_config_dir() / "settings.local.json"


def default_app_data_dir() -> Path:
    return get_user_data_dir() / "Gestion_Bisses_Data"


def launcher_log_file_path() -> Path:
    return get_user_log_dir() / "lancement_abisses.log"


def update_cache_dir() -> Path:
    return get_user_cache_dir() / "updates"


def path_looks_foreign(path: PathLike, platform_name: Optional[str] = None) -> bool:
    """Repère un chemin Windows sur Unix, ou un chemin Unix sur Windows."""
    text = str(path or "").strip()
    if not text:
        return False

    platform_value = _platform_name(platform_name)
    looks_windows = bool(re.match(r"^[A-Za-z]:[\\/]", text)) or text.startswith("\\\\")

    if platform_value.startswith("win"):
        return text.startswith("/") and not text.startswith("//")
    return looks_windows


@dataclass(frozen=True)
class LocalEnvironment:
    application_dir: Path
    settings_file: Path
    default_data_dir: Path
    log_file: Path
    update_cache_dir: Path
    migrated_settings_from: Optional[Path] = None
    migration_error: str = ""


def prepare_user_environment(
    legacy_application_dir: Optional[PathLike] = None,
) -> LocalEnvironment:
    """Crée les dossiers locaux et copie une ancienne configuration une fois.

    L'ancien fichier reste en place comme sauvegarde. Une configuration déjà
    présente dans le profil utilisateur n'est jamais remplacée.
    """
    application_dir = (
        Path(legacy_application_dir).resolve()
        if legacy_application_dir is not None
        else get_application_dir()
    )
    settings_file = settings_file_path()
    default_data = default_app_data_dir()
    log_file = launcher_log_file_path()
    cache_dir = update_cache_dir()

    for directory in (
        settings_file.parent,
        default_data.parent,
        log_file.parent,
        cache_dir,
    ):
        directory.mkdir(parents=True, exist_ok=True)

    migrated_from = None
    migration_error = ""
    legacy_settings = application_dir / "settings.local.json"

    if not settings_file.exists() and legacy_settings.is_file():
        try:
            with legacy_settings.open("r", encoding="utf-8") as handle:
                payload = json.load(handle)
            if not isinstance(payload, dict):
                raise ValueError("le contenu n'est pas un objet JSON")
            shutil.copy2(legacy_settings, settings_file)
            migrated_from = legacy_settings
        except Exception as exc:
            migration_error = str(exc)

    return LocalEnvironment(
        application_dir=application_dir,
        settings_file=settings_file,
        default_data_dir=default_data,
        log_file=log_file,
        update_cache_dir=cache_dir,
        migrated_settings_from=migrated_from,
        migration_error=migration_error,
    )
