from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

import abisses_paths


class AbissesPathsTests(unittest.TestCase):
    def test_windows_paths_are_local_to_the_user(self):
        env = {"LOCALAPPDATA": r"C:\Users\xy\AppData\Local"}
        config = abisses_paths.get_user_config_dir("win32", env, r"C:\Users\xy")
        data = abisses_paths.get_user_data_dir("win32", env, r"C:\Users\xy")
        self.assertEqual(
            str(config).replace("\\", "/"),
            "C:/Users/xy/AppData/Local/Abisses",
        )
        self.assertEqual(config, data)

    def test_linux_follows_xdg_directories(self):
        env = {
            "XDG_CONFIG_HOME": "/tmp/config",
            "XDG_DATA_HOME": "/tmp/data",
            "XDG_STATE_HOME": "/tmp/state",
            "XDG_CACHE_HOME": "/tmp/cache",
        }
        self.assertEqual(
            abisses_paths.get_user_config_dir("linux", env, "/home/xy"),
            Path("/tmp/config/Abisses"),
        )
        self.assertEqual(
            abisses_paths.get_user_data_dir("linux", env, "/home/xy"),
            Path("/tmp/data/Abisses"),
        )
        self.assertEqual(
            abisses_paths.get_user_log_dir("linux", env, "/home/xy"),
            Path("/tmp/state/Abisses/logs"),
        )
        self.assertEqual(
            abisses_paths.get_user_cache_dir("linux", env, "/home/xy"),
            Path("/tmp/cache/Abisses"),
        )

    def test_explicit_platform_directories_do_not_require_home(self):
        """Windows CI peut volontairement exécuter sans USERPROFILE/HOME."""
        with patch.object(
            abisses_paths.Path,
            "home",
            side_effect=RuntimeError("dossier personnel indisponible"),
        ):
            windows_path = abisses_paths.get_user_config_dir(
                "win32",
                {"LOCALAPPDATA": r"C:\Users\xy\AppData\Local"},
            )
            linux_path = abisses_paths.get_user_config_dir(
                "linux",
                {"XDG_CONFIG_HOME": "/tmp/config"},
            )

        self.assertEqual(
            str(windows_path).replace("\\", "/"),
            "C:/Users/xy/AppData/Local/Abisses",
        )
        self.assertEqual(linux_path, Path("/tmp/config/Abisses"))

    def test_foreign_paths_are_detected(self):
        self.assertTrue(abisses_paths.path_looks_foreign(r"C:\Bisses\Data", "linux"))
        self.assertTrue(abisses_paths.path_looks_foreign("/home/xy/Bisses", "win32"))
        self.assertFalse(abisses_paths.path_looks_foreign("/home/xy/Bisses", "linux"))
        self.assertFalse(abisses_paths.path_looks_foreign(r"D:\Bisses", "win32"))

    def test_legacy_settings_are_copied_without_deleting_the_source(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            legacy_dir = root / "ancienne_installation"
            legacy_dir.mkdir()
            legacy_settings = legacy_dir / "settings.local.json"
            legacy_settings.write_text(
                json.dumps({"app_data_folder": "/nas/Bisses"}),
                encoding="utf-8",
            )

            env = {
                "XDG_CONFIG_HOME": str(root / "config"),
                "XDG_DATA_HOME": str(root / "data"),
                "XDG_STATE_HOME": str(root / "state"),
                "XDG_CACHE_HOME": str(root / "cache"),
            }
            with patch.dict("os.environ", env, clear=True), patch(
                "abisses_paths.sys.platform", "linux"
            ):
                result = abisses_paths.prepare_user_environment(legacy_dir)

            self.assertEqual(result.migrated_settings_from, legacy_settings)
            self.assertTrue(legacy_settings.exists())
            self.assertEqual(
                json.loads(result.settings_file.read_text(encoding="utf-8")),
                {"app_data_folder": "/nas/Bisses"},
            )


if __name__ == "__main__":
    unittest.main()
