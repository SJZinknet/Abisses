"""Interface Tk légère pour les mises à jour d'Abisses."""

from __future__ import annotations

import queue
import threading
import tkinter as tk
from datetime import datetime, timedelta, timezone
from tkinter import messagebox, ttk
from typing import Callable, Optional

from abisses_update import (
    UpdateInfo,
    display_version,
    download_update,
    find_available_update,
    get_current_version,
    launch_installer,
    open_releases_page,
    parse_version,
    platform_description,
)


class AbissesUpdateController:
    """Contrôleur persistant ; son panneau peut être recréé avec Paramètres."""

    CHECK_INTERVAL = timedelta(hours=24)

    def __init__(
        self,
        root,
        read_settings: Callable[[], dict],
        write_settings: Callable[[dict], None],
        on_update_available: Optional[Callable[[UpdateInfo], None]] = None,
        log: Optional[Callable[[str], None]] = None,
    ):
        self.root = root
        self.read_settings = read_settings
        self.write_settings = write_settings
        self.on_update_available = on_update_available
        self.log = log
        self.current_version = get_current_version()
        self.latest_info = None
        self.busy = False

        preferences = self._preferences()
        self.auto_check_var = tk.BooleanVar(
            master=root,
            value=bool(preferences.get("check_automatically", True)),
        )
        self.status_var = tk.StringVar(master=root, value="Aucune vérification effectuée.")
        self.progress_var = tk.DoubleVar(master=root, value=0.0)

        self.panel = None
        self.check_button = None
        self.install_button = None
        self.progress = None
        self.notes_text = None
        self.version_label = None
        self._tk_queue = queue.Queue()
        self.root.after(100, self._drain_tk_queue)

    def _log(self, message: str) -> None:
        if self.log:
            try:
                self.log(message)
            except Exception:
                pass

    def _preferences(self) -> dict:
        settings = self.read_settings()
        if not isinstance(settings, dict):
            return {}
        preferences = settings.get("updates", {})
        return preferences if isinstance(preferences, dict) else {}

    def _write_preferences(self, **changes) -> None:
        settings = self.read_settings()
        if not isinstance(settings, dict):
            settings = {}
        preferences = settings.get("updates", {})
        if not isinstance(preferences, dict):
            preferences = {}
        preferences.update(changes)
        settings["updates"] = preferences
        self.write_settings(settings)

    def attach(self, parent) -> None:
        """Construit l'onglet Mises à jour dans un nouveau parent Tk."""
        self.panel = parent

        tk.Label(
            parent,
            text="Mises à jour d'Abisses",
            font=("Arial", 14, "bold"),
            anchor="w",
        ).pack(fill="x")

        channel = (
            "versions de test et stables"
            if parse_version(self.current_version).is_prerelease
            else "versions stables"
        )
        self.version_label = tk.Label(
            parent,
            text=(
                f"Version installée : {display_version(self.current_version)}\n"
                f"Système : {platform_description()}\n"
                f"Canal : {channel}"
            ),
            justify="left",
            anchor="w",
            fg="#444444",
        )
        self.version_label.pack(fill="x", pady=(8, 18))

        tk.Checkbutton(
            parent,
            text="Vérifier automatiquement les mises à jour au démarrage",
            variable=self.auto_check_var,
            command=self.save_auto_check_preference,
            anchor="w",
        ).pack(fill="x", pady=(0, 12))

        self.status_label = tk.Label(
            parent,
            textvariable=self.status_var,
            justify="left",
            anchor="w",
            wraplength=780,
        )
        self.status_label.pack(fill="x", pady=(4, 8))

        self.progress = ttk.Progressbar(
            parent,
            variable=self.progress_var,
            maximum=100,
            mode="determinate",
        )
        self.progress.pack(fill="x", pady=(0, 12))

        button_row = tk.Frame(parent)
        button_row.pack(fill="x", pady=(0, 12))

        self.check_button = tk.Button(
            button_row,
            text="🔎 Rechercher une mise à jour",
            command=lambda: self.check_for_updates(manual=True),
        )
        self.check_button.pack(side="left", padx=(0, 8))

        self.install_button = tk.Button(
            button_row,
            text="⬇ Télécharger et installer",
            command=self.start_installation,
            bg="#dceeff",
        )

        tk.Button(
            button_row,
            text="Ouvrir les Releases GitHub",
            command=self.open_release_page,
        ).pack(side="left", padx=8)

        tk.Label(
            parent,
            text="Notes de la version disponible",
            font=("Arial", 11, "bold"),
            anchor="w",
        ).pack(fill="x", pady=(8, 4))

        self.notes_text = tk.Text(parent, height=10, wrap="word", state="disabled")
        self.notes_text.pack(fill="both", expand=True)

        parent.bind("<Destroy>", self._on_panel_destroy, add="+")
        self._refresh_panel_from_state()
        self._set_busy(self.busy)

    def _on_panel_destroy(self, event=None) -> None:
        if event is not None and event.widget is not self.panel:
            return
        self.panel = None
        self.check_button = None
        self.install_button = None
        self.progress = None
        self.notes_text = None
        self.version_label = None

    @staticmethod
    def _widget_exists(widget) -> bool:
        if widget is None:
            return False
        try:
            return bool(widget.winfo_exists())
        except Exception:
            return False

    def _refresh_panel_from_state(self) -> None:
        if self.latest_info is None:
            return
        info = self.latest_info
        self.status_var.set(
            f"Mise à jour disponible : {display_version(info.new_version)}"
        )
        if self._widget_exists(self.install_button):
            self.install_button.pack(side="left", padx=8)
        if self._widget_exists(self.notes_text):
            self.notes_text.config(state="normal")
            self.notes_text.delete("1.0", tk.END)
            self.notes_text.insert(
                "1.0",
                info.notes or "Aucune note n'a été fournie pour cette version.",
            )
            self.notes_text.config(state="disabled")

    def _set_busy(self, busy: bool) -> None:
        self.busy = bool(busy)
        state = "disabled" if self.busy else "normal"
        for button in (self.check_button, self.install_button):
            if self._widget_exists(button):
                try:
                    button.config(state=state)
                except Exception:
                    pass

    def save_auto_check_preference(self) -> None:
        self._write_preferences(check_automatically=bool(self.auto_check_var.get()))

    def maybe_check_automatically(self) -> None:
        preferences = self._preferences()
        if not bool(preferences.get("check_automatically", True)):
            return

        last_value = str(preferences.get("last_checked_at") or "").strip()
        if last_value:
            try:
                last_check = datetime.fromisoformat(last_value.replace("Z", "+00:00"))
                if last_check.tzinfo is None:
                    last_check = last_check.replace(tzinfo=timezone.utc)
                if datetime.now(timezone.utc) - last_check < self.CHECK_INTERVAL:
                    return
            except Exception:
                pass
        self.check_for_updates(manual=False)

    def check_for_updates(self, manual: bool = True) -> None:
        if self.busy:
            return
        self._set_busy(True)
        self.progress_var.set(0.0)
        self.status_var.set("Recherche d'une mise à jour sur GitHub…")

        def worker():
            try:
                info = find_available_update(self.current_version)
                error = None
            except Exception as exc:
                info = None
                error = exc
            self._call_on_tk_thread(
                lambda: self._finish_check(info, error, manual)
            )

        threading.Thread(target=worker, daemon=True, name="abisses-update-check").start()

    def _finish_check(self, info, error, manual: bool) -> None:
        self._set_busy(False)
        if error is not None:
            message = str(error)
            self.status_var.set(f"Vérification impossible : {message}")
            self._log(f"⚠️ Mise à jour : {message}")
            if manual:
                messagebox.showwarning("Mise à jour Abisses", message)
            return

        checked_at = datetime.now(timezone.utc).isoformat(timespec="seconds")
        self._write_preferences(last_checked_at=checked_at)

        if info is None:
            self.status_var.set(
                f"Abisses {display_version(self.current_version)} est à jour."
            )
            self._log("✅ Aucune mise à jour disponible.")
            return

        self.latest_info = info
        self._refresh_panel_from_state()
        self._log(f"⬆ Mise à jour disponible : {display_version(info.new_version)}")
        if self.on_update_available:
            try:
                self.on_update_available(info)
            except Exception:
                pass

    def _set_download_progress(self, downloaded: int, total: int) -> None:
        if total > 0:
            percent = min(100.0, downloaded * 100.0 / total)
            self.progress_var.set(percent)
            self.status_var.set(f"Téléchargement : {percent:.0f} %")
        else:
            self.status_var.set(
                f"Téléchargement : {downloaded / (1024 * 1024):.1f} Mo"
            )

    def start_installation(self) -> None:
        info = self.latest_info
        if info is None or self.busy:
            return

        confirmed = messagebox.askyesno(
            "Installer la mise à jour",
            f"Installer Abisses {display_version(info.new_version)} ?\n\n"
            "Le fichier sera vérifié avant son ouverture. Abisses se fermera "
            "ensuite pour laisser l'installateur terminer la mise à jour.\n\n"
            "Sous Ubuntu, le mot de passe du système pourra être demandé.",
        )
        if not confirmed:
            return

        self._set_busy(True)
        self.progress_var.set(0.0)
        self.status_var.set("Préparation du téléchargement…")

        def progress(downloaded: int, total: int) -> None:
            self._call_on_tk_thread(
                lambda: self._set_download_progress(downloaded, total)
            )

        def worker():
            try:
                installer_path = download_update(info, progress_callback=progress)
                error = None
            except Exception as exc:
                installer_path = None
                error = exc
            self._call_on_tk_thread(
                lambda: self._finish_download(installer_path, error)
            )

        threading.Thread(target=worker, daemon=True, name="abisses-update-download").start()

    def _finish_download(self, installer_path, error) -> None:
        if error is not None:
            self._set_busy(False)
            self.progress_var.set(0.0)
            message = str(error)
            self.status_var.set(f"Mise à jour interrompue : {message}")
            self._log(f"❌ Mise à jour : {message}")
            messagebox.showerror("Mise à jour Abisses", message)
            return

        self.progress_var.set(100.0)
        self.status_var.set("Fichier vérifié. Ouverture de l'installateur…")
        try:
            mode = launch_installer(installer_path)
        except Exception as exc:
            self._set_busy(False)
            message = str(exc)
            self.status_var.set(f"Installateur non ouvert : {message}")
            messagebox.showerror("Mise à jour Abisses", message)
            return

        if mode.startswith("linux"):
            messagebox.showinfo(
                "Installation lancée",
                "Le gestionnaire de paquets Ubuntu va terminer l'installation.\n\n"
                "Abisses va maintenant se fermer. Relancez-le lorsque "
                "l'installation est terminée.",
            )
        self._log("✅ Installateur de mise à jour lancé.")
        try:
            self.root.after(250, self.root.destroy)
        except Exception:
            pass

    def open_release_page(self) -> None:
        url = self.latest_info.html_url if self.latest_info else None
        if not open_releases_page(url):
            messagebox.showwarning(
                "Releases GitHub",
                "La page des Releases n'a pas pu être ouverte dans le navigateur.",
            )

    def _call_on_tk_thread(self, callback) -> None:
        self._tk_queue.put(callback)

    def _drain_tk_queue(self) -> None:
        try:
            while True:
                callback = self._tk_queue.get_nowait()
                try:
                    callback()
                except Exception as exc:
                    self._log(f"⚠️ Interface de mise à jour : {exc}")
        except queue.Empty:
            pass
        try:
            self.root.after(100, self._drain_tk_queue)
        except Exception:
            pass
