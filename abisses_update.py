"""Moteur de mise à jour d'Abisses depuis les Releases GitHub."""

from __future__ import annotations

import hashlib
import json
import os
import platform
import re
import shutil
import ssl
import subprocess
import urllib.error
import urllib.request
import webbrowser
from dataclasses import dataclass
from pathlib import Path
from typing import Callable, Optional, Sequence, Tuple

from abisses_paths import resource_path, update_cache_dir

try:
    import certifi
except Exception:  # pragma: no cover - repli pour une exécution source minimale
    certifi = None


GITHUB_REPOSITORY = "SJZinknet/Abisses"
GITHUB_API_ROOT = f"https://api.github.com/repos/{GITHUB_REPOSITORY}"
GITHUB_RELEASES_URL = f"https://github.com/{GITHUB_REPOSITORY}/releases"
DEFAULT_VERSION = "0.55.0-beta.1"
DOWNLOAD_BLOCK_SIZE = 1024 * 1024


class UpdateError(RuntimeError):
    """Erreur compréhensible pouvant être affichée dans l'interface."""


@dataclass(frozen=True)
class ParsedVersion:
    original: str
    release: Tuple[int, int, int]
    prerelease: Tuple[Tuple[int, object], ...]

    @property
    def is_prerelease(self) -> bool:
        return bool(self.prerelease)

    @property
    def comparison_key(self):
        # Une version stable est plus récente que ses préversions.
        stable_rank = 0 if self.prerelease else 1
        return self.release + (stable_rank, self.prerelease)


@dataclass(frozen=True)
class ReleaseAsset:
    name: str
    download_url: str
    size: int = 0


@dataclass(frozen=True)
class UpdateInfo:
    current_version: str
    new_version: str
    tag_name: str
    release_name: str
    notes: str
    html_url: str
    published_at: str
    prerelease: bool
    installer: ReleaseAsset
    checksums: ReleaseAsset


def parse_version(value: str) -> ParsedVersion:
    text = str(value or "").strip()
    match = re.fullmatch(
        r"[vV]?(\d+)(?:\.(\d+))?(?:\.(\d+))?(?:-([0-9A-Za-z.-]+))?(?:\+[0-9A-Za-z.-]+)?",
        text,
    )
    if not match:
        raise ValueError(f"Version non reconnue : {value!r}")

    release = tuple(int(part or 0) for part in match.groups()[:3])
    prerelease_text = match.group(4) or ""
    prerelease = []
    for token in filter(None, prerelease_text.split(".")):
        if token.isdigit():
            prerelease.append((0, int(token)))
        else:
            prerelease.append((1, token.casefold()))

    return ParsedVersion(text, release, tuple(prerelease))


def is_newer_version(candidate: str, current: str) -> bool:
    return parse_version(candidate).comparison_key > parse_version(current).comparison_key


def get_current_version() -> str:
    version_file = resource_path("VERSION")
    try:
        value = version_file.read_text(encoding="utf-8").strip()
        parse_version(value)
        return value
    except Exception:
        return DEFAULT_VERSION


def display_version(value: Optional[str] = None) -> str:
    version = str(value or get_current_version()).strip()
    return version if version.lower().startswith("v") else f"v{version}"


def current_platform_key(
    system_name: Optional[str] = None,
    machine_name: Optional[str] = None,
) -> Tuple[str, str]:
    system_value = str(system_name or platform.system()).strip().lower()
    machine_value = str(machine_name or platform.machine()).strip().lower()

    if machine_value not in {"x86_64", "amd64", "x64"}:
        raise UpdateError(
            "Les mises à jour automatiques sont actuellement disponibles "
            "uniquement pour les ordinateurs 64 bits Intel/AMD."
        )

    if system_value.startswith("win"):
        return "windows", "x64"
    if system_value == "linux":
        return "linux", "amd64"
    raise UpdateError(
        f"Les mises à jour automatiques ne sont pas encore proposées pour {system_name or platform.system()}."
    )


def platform_description() -> str:
    try:
        system_key, _architecture = current_platform_key()
    except UpdateError:
        return f"{platform.system()} {platform.machine()}"
    return "Windows 64 bits" if system_key == "windows" else "Ubuntu/Linux 64 bits"


def _request(url: str, timeout: int = 20):
    request = urllib.request.Request(
        url,
        headers={
            "Accept": "application/vnd.github+json",
            "User-Agent": f"Abisses/{get_current_version()}",
        },
    )
    ssl_context = None
    if certifi is not None:
        try:
            ssl_context = ssl.create_default_context(cafile=certifi.where())
        except Exception:
            ssl_context = None
    try:
        return urllib.request.urlopen(request, timeout=timeout, context=ssl_context)
    except urllib.error.HTTPError as exc:
        if exc.code == 403:
            raise UpdateError(
                "GitHub refuse temporairement la vérification. Réessayez dans quelques minutes."
            ) from exc
        raise UpdateError(f"GitHub a répondu avec l'erreur HTTP {exc.code}.") from exc
    except urllib.error.URLError as exc:
        reason = getattr(exc, "reason", exc)
        raise UpdateError(f"Connexion à GitHub impossible : {reason}") from exc


def _request_json(url: str):
    try:
        with _request(url) as response:
            payload = json.loads(response.read().decode("utf-8"))
    except UpdateError:
        raise
    except Exception as exc:
        raise UpdateError(f"Réponse GitHub illisible : {exc}") from exc
    return payload


def _asset_from_json(raw: dict) -> Optional[ReleaseAsset]:
    name = str(raw.get("name") or "").strip()
    url = str(raw.get("browser_download_url") or "").strip()
    if not name or not url:
        return None
    try:
        size = int(raw.get("size") or 0)
    except Exception:
        size = 0
    return ReleaseAsset(name=name, download_url=url, size=max(0, size))


def select_release_assets(
    release: dict,
    system_name: Optional[str] = None,
    machine_name: Optional[str] = None,
) -> Tuple[ReleaseAsset, ReleaseAsset]:
    system_key, _architecture = current_platform_key(system_name, machine_name)
    if system_key == "windows":
        installer_pattern = re.compile(
            r"^Abisses-Setup-v?.+-Windows-x64\.exe$",
            re.IGNORECASE,
        )
    else:
        installer_pattern = re.compile(
            r"^abisses_.+_amd64\.deb$",
            re.IGNORECASE,
        )

    installer = None
    checksums = None
    for raw in release.get("assets", []) or []:
        if not isinstance(raw, dict):
            continue
        asset = _asset_from_json(raw)
        if asset is None:
            continue
        if installer_pattern.match(asset.name):
            installer = asset
        elif asset.name.casefold() == "sha256sums":
            checksums = asset

    if installer is None:
        raise UpdateError(
            "Cette version est publiée, mais son installateur pour ce système "
            "n'est pas encore disponible. Réessayez un peu plus tard."
        )
    if checksums is None:
        raise UpdateError(
            "Cette version ne contient pas le fichier de contrôle SHA256SUMS ; "
            "le téléchargement est refusé par sécurité."
        )
    return installer, checksums


def _candidate_releases(current_version: str) -> Sequence[dict]:
    # La liste fonctionne aussi lorsqu'aucune Release n'existe encore, alors
    # que l'endpoint /latest répondrait par une erreur 404.
    parse_version(current_version)
    payload = _request_json(f"{GITHUB_API_ROOT}/releases?per_page=20")
    if not isinstance(payload, list):
        raise UpdateError("La liste des Releases GitHub est illisible.")
    return [item for item in payload if isinstance(item, dict)]


def find_available_update(current_version: Optional[str] = None) -> Optional[UpdateInfo]:
    current = str(current_version or get_current_version()).strip()
    parse_version(current)
    delayed_asset_error = None

    for release in _candidate_releases(current):
        if release.get("draft"):
            continue
        if release.get("prerelease") and not parse_version(current).is_prerelease:
            continue

        tag_name = str(release.get("tag_name") or "").strip()
        try:
            if not tag_name or not is_newer_version(tag_name, current):
                continue
        except ValueError:
            continue

        try:
            installer, checksums = select_release_assets(release)
        except UpdateError as exc:
            delayed_asset_error = exc
            continue

        return UpdateInfo(
            current_version=current,
            new_version=parse_version(tag_name).original.lstrip("vV"),
            tag_name=tag_name,
            release_name=str(release.get("name") or tag_name),
            notes=str(release.get("body") or "").strip(),
            html_url=str(release.get("html_url") or GITHUB_RELEASES_URL),
            published_at=str(release.get("published_at") or ""),
            prerelease=bool(release.get("prerelease")),
            installer=installer,
            checksums=checksums,
        )

    if delayed_asset_error is not None:
        raise delayed_asset_error
    return None


def _download_to_path(
    url: str,
    destination: Path,
    expected_size: int = 0,
    progress_callback: Optional[Callable[[int, int], None]] = None,
) -> Path:
    destination.parent.mkdir(parents=True, exist_ok=True)
    temporary = destination.with_name(destination.name + ".part")
    try:
        temporary.unlink(missing_ok=True)
    except TypeError:
        if temporary.exists():
            temporary.unlink()

    try:
        with _request(url, timeout=60) as response, temporary.open("wb") as handle:
            try:
                total = int(response.headers.get("Content-Length") or expected_size or 0)
            except Exception:
                total = max(0, expected_size)
            downloaded = 0
            while True:
                block = response.read(DOWNLOAD_BLOCK_SIZE)
                if not block:
                    break
                handle.write(block)
                downloaded += len(block)
                if progress_callback:
                    progress_callback(downloaded, total)
        os.replace(temporary, destination)
        return destination
    except UpdateError:
        raise
    except Exception as exc:
        raise UpdateError(f"Téléchargement interrompu : {exc}") from exc
    finally:
        if temporary.exists():
            try:
                temporary.unlink()
            except Exception:
                pass


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        while True:
            block = handle.read(DOWNLOAD_BLOCK_SIZE)
            if not block:
                break
            digest.update(block)
    return digest.hexdigest()


def expected_checksum(checksum_text: str, filename: str) -> str:
    for raw_line in checksum_text.splitlines():
        parts = raw_line.strip().split(maxsplit=1)
        if len(parts) != 2:
            continue
        digest, listed_name = parts
        listed_name = listed_name.lstrip("*").strip()
        if listed_name == filename and re.fullmatch(r"[0-9a-fA-F]{64}", digest):
            return digest.lower()
    raise UpdateError(f"Aucune empreinte SHA256 trouvée pour {filename}.")


def download_update(
    update: UpdateInfo,
    progress_callback: Optional[Callable[[int, int], None]] = None,
) -> Path:
    cache_dir = update_cache_dir()
    cache_dir.mkdir(parents=True, exist_ok=True)
    installer_path = cache_dir / update.installer.name
    checksum_path = cache_dir / "SHA256SUMS"

    _download_to_path(
        update.installer.download_url,
        installer_path,
        expected_size=update.installer.size,
        progress_callback=progress_callback,
    )
    _download_to_path(update.checksums.download_url, checksum_path)

    checksum_text = checksum_path.read_text(encoding="utf-8")
    expected = expected_checksum(checksum_text, installer_path.name)
    actual = sha256_file(installer_path)
    if actual != expected:
        try:
            installer_path.unlink()
        except Exception:
            pass
        raise UpdateError(
            "Le fichier téléchargé ne correspond pas à l'empreinte publiée. "
            "Il a été supprimé et ne sera pas exécuté."
        )
    return installer_path


def launch_installer(installer_path: Path) -> str:
    path = Path(installer_path).resolve()
    if not path.is_file():
        raise UpdateError(f"Installateur introuvable : {path}")

    system_key, _architecture = current_platform_key()
    try:
        if system_key == "windows":
            os.startfile(str(path))  # type: ignore[attr-defined]
            return "windows"

        pkexec = shutil.which("pkexec")
        apt_get = shutil.which("apt-get")
        if pkexec and apt_get:
            subprocess.Popen(
                [pkexec, apt_get, "install", "-y", str(path)],
                start_new_session=True,
            )
            return "linux-package-manager"

        opener = shutil.which("gio") or shutil.which("xdg-open")
        if opener:
            command = [opener, "open", str(path)] if Path(opener).name == "gio" else [opener, str(path)]
            subprocess.Popen(command, start_new_session=True)
            return "linux-open"
    except Exception as exc:
        raise UpdateError(f"Impossible d'ouvrir l'installateur : {exc}") from exc

    raise UpdateError(
        "Aucun installateur graphique compatible n'a été trouvé sur cet ordinateur."
    )


def open_releases_page(url: Optional[str] = None) -> bool:
    return bool(webbrowser.open(str(url or GITHUB_RELEASES_URL)))
