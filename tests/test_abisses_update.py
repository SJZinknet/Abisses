from __future__ import annotations

import hashlib
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

import abisses_update


def release_assets(*names):
    return {
        "assets": [
            {
                "name": name,
                "browser_download_url": f"https://example.invalid/{name}",
                "size": 123,
            }
            for name in names
        ]
    }


def release(tag, prerelease=False):
    payload = release_assets(
        f"Abisses-Setup-v{tag.lstrip('v')}-Windows-x64.exe",
        f"abisses_{tag.lstrip('v')}_amd64.deb",
        "SHA256SUMS",
    )
    payload.update(
        {
            "tag_name": tag,
            "name": f"Abisses {tag}",
            "body": "Notes de test",
            "html_url": f"https://example.invalid/releases/{tag}",
            "published_at": "2026-08-21T10:00:00Z",
            "prerelease": prerelease,
            "draft": False,
        }
    )
    return payload


class AbissesUpdateTests(unittest.TestCase):
    def test_versions_follow_stable_and_beta_order(self):
        self.assertTrue(abisses_update.is_newer_version("v0.55.0-beta.2", "0.55.0-beta.1"))
        self.assertTrue(abisses_update.is_newer_version("0.55.0", "0.55.0-beta.9"))
        self.assertTrue(abisses_update.is_newer_version("0.56.0", "0.55.9"))
        self.assertFalse(abisses_update.is_newer_version("0.55.0-beta.1", "0.55.0"))
        self.assertFalse(abisses_update.is_newer_version("0.55.0", "v0.55.0"))

    def test_windows_asset_is_selected(self):
        release = release_assets(
            "Abisses-Setup-v0.55.0-Windows-x64.exe",
            "abisses_0.55.0_amd64.deb",
            "SHA256SUMS",
        )
        installer, checksums = abisses_update.select_release_assets(
            release,
            "Windows",
            "AMD64",
        )
        self.assertEqual(installer.name, "Abisses-Setup-v0.55.0-Windows-x64.exe")
        self.assertEqual(checksums.name, "SHA256SUMS")

    def test_linux_asset_is_selected(self):
        release = release_assets(
            "Abisses-Setup-v0.55.0-Windows-x64.exe",
            "abisses_0.55.0_amd64.deb",
            "SHA256SUMS",
        )
        installer, _checksums = abisses_update.select_release_assets(
            release,
            "Linux",
            "x86_64",
        )
        self.assertEqual(installer.name, "abisses_0.55.0_amd64.deb")

    def test_missing_checksum_is_rejected(self):
        release = release_assets("abisses_0.55.0_amd64.deb")
        with self.assertRaises(abisses_update.UpdateError):
            abisses_update.select_release_assets(release, "Linux", "x86_64")

    def test_checksum_file_is_parsed_and_verified(self):
        with tempfile.TemporaryDirectory() as temp:
            path = Path(temp) / "abisses.deb"
            path.write_bytes(b"abisses-test")
            digest = hashlib.sha256(b"abisses-test").hexdigest()
            text = f"{digest}  abisses.deb\n"
            self.assertEqual(
                abisses_update.expected_checksum(text, path.name),
                digest,
            )
            self.assertEqual(abisses_update.sha256_file(path), digest)

    def test_unsupported_architecture_is_explicit(self):
        with self.assertRaises(abisses_update.UpdateError):
            abisses_update.current_platform_key("Linux", "aarch64")

    def test_beta_receives_the_next_beta(self):
        releases = [release("v0.55.0-beta.2", prerelease=True)]
        with patch("abisses_update._candidate_releases", return_value=releases), patch(
            "abisses_update.platform.system", return_value="Linux"
        ), patch("abisses_update.platform.machine", return_value="x86_64"):
            info = abisses_update.find_available_update("0.55.0-beta.1")
        self.assertIsNotNone(info)
        self.assertEqual(info.new_version, "0.55.0-beta.2")

    def test_stable_version_ignores_prereleases(self):
        releases = [release("v0.56.0-beta.1", prerelease=True)]
        with patch("abisses_update._candidate_releases", return_value=releases), patch(
            "abisses_update.platform.system", return_value="Windows"
        ), patch("abisses_update.platform.machine", return_value="AMD64"):
            info = abisses_update.find_available_update("0.55.0")
        self.assertIsNone(info)

    def test_download_is_accepted_only_after_checksum_verification(self):
        with tempfile.TemporaryDirectory() as temp:
            cache = Path(temp)
            installer_name = "abisses_0.55.0_amd64.deb"
            installer_bytes = b"paquet-abisses"
            digest = hashlib.sha256(installer_bytes).hexdigest()
            info = abisses_update.UpdateInfo(
                current_version="0.54.0",
                new_version="0.55.0",
                tag_name="v0.55.0",
                release_name="Abisses v0.55.0",
                notes="",
                html_url="https://example.invalid/release",
                published_at="",
                prerelease=False,
                installer=abisses_update.ReleaseAsset(
                    installer_name,
                    "https://example.invalid/installer",
                    len(installer_bytes),
                ),
                checksums=abisses_update.ReleaseAsset(
                    "SHA256SUMS",
                    "https://example.invalid/checksums",
                    0,
                ),
            )

            def fake_download(url, destination, **_kwargs):
                if url.endswith("installer"):
                    destination.write_bytes(installer_bytes)
                else:
                    destination.write_text(
                        f"{digest}  {installer_name}\n",
                        encoding="utf-8",
                    )
                return destination

            with patch("abisses_update.update_cache_dir", return_value=cache), patch(
                "abisses_update._download_to_path", side_effect=fake_download
            ):
                result = abisses_update.download_update(info)

            self.assertEqual(result, cache / installer_name)
            self.assertEqual(result.read_bytes(), installer_bytes)


if __name__ == "__main__":
    unittest.main()
