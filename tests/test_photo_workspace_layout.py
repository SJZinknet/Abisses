from __future__ import annotations

import importlib
import sys
import types
import unittest


def install_optional_dependency_stub(name, **attributes):
    """Isole ces tests de disposition des bibliothèques métier lourdes."""
    try:
        importlib.import_module(name)
        return
    except ModuleNotFoundError:
        module = types.ModuleType(name)
        for key, value in attributes.items():
            setattr(module, key, value)
        sys.modules[name] = module


install_optional_dependency_stub(
    "pillow_heif",
    register_heif_opener=lambda: None,
)
install_optional_dependency_stub("gpxpy")
install_optional_dependency_stub("tkintermapview")
install_optional_dependency_stub("piexif")

from gestion_bisses import BisseManagerApp


class FakeVariable:
    def __init__(self, value=False):
        self.value = bool(value)

    def get(self):
        return self.value

    def set(self, value):
        self.value = bool(value)


class FakeButton:
    def __init__(self):
        self.options = {}

    def config(self, **kwargs):
        self.options.update(kwargs)


class FakePanedWindow:
    def __init__(self, width=1600):
        self.width = width
        self.attached = []
        self.add_options = {}
        self.sashes = []

    def panes(self):
        return list(self.attached)

    def forget(self, panel):
        self.attached.remove(panel)

    def add(self, panel, **options):
        self.attached.append(panel)
        self.add_options[panel] = options

    def update_idletasks(self):
        return None

    def winfo_width(self):
        return self.width

    def sash_place(self, index, x, y):
        self.sashes.append((index, x, y))


def make_app(*, map_visible=True, viewer_visible=True, metadata_visible=True):
    app = BisseManagerApp.__new__(BisseManagerApp)
    app.photo_panel_visibility_vars = {
        "map": FakeVariable(map_visible),
        "viewer": FakeVariable(viewer_visible),
        "metadata": FakeVariable(metadata_visible),
    }
    app.photo_workspace_panels = {
        "map": object(),
        "viewer": object(),
        "metadata": object(),
    }
    app.photo_workspace_paned = FakePanedWindow()
    app.photo_panels_button = FakeButton()
    app.photo_map_expand_button = FakeButton()
    app.schedule_photo_workspace_layout = lambda *args, **kwargs: None
    return app


class PhotoWorkspaceLayoutTests(unittest.TestCase):
    def test_default_order_is_map_viewer_metadata(self):
        app = make_app()
        self.assertEqual(
            app.photo_workspace_visible_keys(),
            ["map", "viewer", "metadata"],
        )

    def test_an_empty_workspace_restores_the_map(self):
        app = make_app(
            map_visible=False,
            viewer_visible=False,
            metadata_visible=False,
        )

        app.refresh_photo_workspace_panes()

        self.assertTrue(app.photo_panel_visibility_vars["map"].get())
        self.assertEqual(
            app.photo_workspace_paned.attached,
            [app.photo_workspace_panels["map"]],
        )
        self.assertEqual(app.photo_panels_button.options["text"], "Panneaux (1) ▾")

    def test_map_only_toggle_returns_to_all_panels(self):
        app = make_app(viewer_visible=False, metadata_visible=False)

        app.toggle_photo_map_expanded()

        self.assertEqual(
            app.photo_workspace_visible_keys(),
            ["map", "viewer", "metadata"],
        )

    def test_default_layout_gives_44_percent_to_the_map(self):
        app = make_app()

        app.apply_photo_workspace_layout()

        self.assertEqual(
            app.photo_workspace_paned.sashes,
            [(0, 704, 0), (1, 1280, 0)],
        )


if __name__ == "__main__":
    unittest.main()
