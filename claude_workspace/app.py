import os
import shutil
import subprocess

import gi
gi.require_version("Notify", "0.7")
from gi.repository import Gtk, Vte, GLib, Notify

from .config import load_state, save_state
from .pane import GENERIC_TITLES, Pane, shorten_path
from .session import last_assistant_text
from .terminal import create_terminal

BLINK_INTERVAL_MS = 500
NOTIFY_SOUND_ID = "message-new-instant"


class ClaudeWorkspace(Gtk.Window):
    def __init__(self, config, appearance):
        super().__init__(title="Claude Workspace")
        self.config = config
        self.appearance = appearance
        self.selected_pane = None
        self.cols = config["columns"]
        self.panes = self._create_panes()
        self.grid = Gtk.Grid(row_homogeneous=True, column_homogeneous=True)
        self._blink_source = None
        self._blink_state = False
        self._sound_cmd = shutil.which("canberra-gtk-play")
        self._notify_enabled = Notify.init("Claude Workspace")
        self._active_notifications = {}
        self.set_default_size(1920, 1080)
        self.maximize()
        self.add(self.grid)
        self._build_grid()
        GLib.idle_add(self._spawn_all)
        GLib.timeout_add_seconds(3, self._refresh_titles)
        GLib.timeout_add_seconds(config["save_interval"], self._save)
        self.connect("destroy", self._quit)
        self.connect("focus-in-event", self._on_window_focus_in)

    def _create_panes(self):
        state = load_state()
        slots = [(p["name"], p["directory"]) for p in self.config["panes"]]
        order = state.get("_order", [n for n, _ in slots])
        by_name = {n: d for n, d in slots}
        ordered = [(n, by_name[n]) for n in order if n in by_name]
        missing = [(n, d) for n, d in slots if n not in order]
        return [Pane(n, d, state.get(n)) for n, d in ordered + missing]

    def _build_grid(self):
        for i, pane in enumerate(self.panes):
            pane.box = self._make_pane_widget(pane)
            self.grid.attach(pane.box, i % self.cols, i // self.cols, 1, 1)

    def _make_pane_widget(self, pane):
        box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)
        pane.label = self._make_label(pane)
        pane.terminal = create_terminal(self.appearance)
        pane.terminal.connect("window-title-changed", self._on_title_changed, pane)
        pane.terminal.connect("bell", self._on_bell, pane)
        pane.terminal.connect("commit", self._on_terminal_commit, pane)
        event_box = self._make_label_event_box(pane)
        box.pack_start(event_box, False, False, 0)
        box.pack_start(pane.terminal, True, True, 0)
        return box

    def _make_label(self, pane):
        label = Gtk.Label(label=pane.title_text(), xalign=0)
        label.get_style_context().add_class("pane-label")
        return label

    def _make_label_event_box(self, pane):
        event_box = Gtk.EventBox()
        event_box.add(pane.label)
        event_box.connect("button-press-event", self._on_label_click, pane)
        return event_box

    def _on_label_click(self, widget, event, pane):
        self._clear_notify(pane)
        if self.selected_pane is None:
            self._select_pane(pane)
        elif self.selected_pane is pane:
            self._deselect()
        else:
            self._swap_panes(self.selected_pane, pane)

    def _on_title_changed(self, terminal, pane):
        pane.term_title = terminal.get_window_title() or ""
        pane.update_label()

    def _select_pane(self, pane):
        self.selected_pane = pane
        pane._set_label_class("pane-label-selected")

    def _deselect(self):
        if self.selected_pane:
            self.selected_pane.update_label()
        self.selected_pane = None

    def _swap_panes(self, a, b):
        idx_a, idx_b = self.panes.index(a), self.panes.index(b)
        self.panes[idx_a], self.panes[idx_b] = b, a
        self._reattach(a, idx_b)
        self._reattach(b, idx_a)
        self.selected_pane = None
        a.update_label()
        b.update_label()

    def _reattach(self, pane, idx):
        self.grid.remove(pane.box)
        self.grid.attach(pane.box, idx % self.cols, idx // self.cols, 1, 1)

    def _spawn_all(self):
        for pane in self.panes:
            self._spawn(pane)
        return False

    def _spawn(self, pane):
        cwd = pane.cwd if os.path.isdir(pane.cwd) else pane.default_dir
        pane.terminal.spawn_async(
            Vte.PtyFlags.DEFAULT, cwd, ["/bin/bash"],
            None, GLib.SpawnFlags.DEFAULT, None, None,
            -1, None, self._on_spawned, pane,
        )

    def _on_spawned(self, terminal, pid, error, pane):
        if error:
            return
        pane.shell_pid = pid
        GLib.timeout_add(800, self._launch_startup_cmd, pane)

    def _launch_startup_cmd(self, pane):
        for cmd in pane.startup_commands(self.config["claude_flags"]):
            pane.terminal.feed_child((cmd + "\n").encode())
        return False

    def _refresh_titles(self):
        for pane in self.panes:
            pane.refresh()
            if pane is not self.selected_pane:
                pane.update_label()
        return True

    def _save(self):
        state = {p.name: p.to_dict() for p in self.panes}
        state["_order"] = [p.name for p in self.panes]
        save_state(state)
        return True

    def _quit(self, *args):
        self._refresh_titles()
        self._save()
        Gtk.main_quit()

    def _on_bell(self, terminal, pane):
        if terminal.has_focus() and self.is_active():
            return
        self._start_notify(pane)

    def _on_terminal_commit(self, terminal, text, size, pane):
        self._clear_notify(pane)

    def _on_window_focus_in(self, window, event):
        self.set_urgency_hint(False)
        return False

    def _start_notify(self, pane):
        if pane.notifying:
            return
        pane.notifying = True
        pane.blink_on = True
        if pane is not self.selected_pane:
            pane.update_label()
        self.set_urgency_hint(True)
        self._send_notification(pane)
        self._play_sound()
        if self._blink_source is None:
            self._blink_state = True
            self._blink_source = GLib.timeout_add(BLINK_INTERVAL_MS, self._tick_blink)

    def _clear_notify(self, pane):
        if not pane.notifying:
            return
        pane.notifying = False
        pane.blink_on = False
        if pane is not self.selected_pane:
            pane.update_label()
        if not any(p.notifying for p in self.panes):
            self.set_urgency_hint(False)

    def _tick_blink(self):
        self._blink_state = not self._blink_state
        any_notifying = False
        for pane in self.panes:
            if pane.notifying:
                any_notifying = True
                pane.blink_on = self._blink_state
                if pane is not self.selected_pane:
                    pane.update_label()
        if not any_notifying:
            self._blink_source = None
            return False
        return True

    def _send_notification(self, pane):
        if not self._notify_enabled:
            return
        pane.refresh()
        cwd = shorten_path(pane.cwd)
        if pane.term_title and pane.term_title not in GENERIC_TITLES:
            title = f"Claude terminó: {pane.term_title}"
        else:
            title = f"Claude terminó en {cwd}"
        body = last_assistant_text(pane.session_id, pane.cwd) if pane.session_id else None
        if not body:
            body = cwd if title.startswith("Claude terminó:") else pane.name
        n = Notify.Notification.new(title, body)
        n.add_action("default", "Abrir", self._on_notification_action, pane)
        n.connect("closed", self._on_notification_closed, pane)
        self._active_notifications[pane.name] = n
        try:
            n.show()
        except GLib.Error:
            self._active_notifications.pop(pane.name, None)

    def _on_notification_action(self, notification, action, pane):
        self.present_with_time(Gtk.get_current_event_time())
        if pane.terminal:
            pane.terminal.grab_focus()
        self._clear_notify(pane)

    def _on_notification_closed(self, notification, pane):
        self._active_notifications.pop(pane.name, None)

    def _play_sound(self):
        if not self._sound_cmd:
            return
        try:
            subprocess.Popen(
                [self._sound_cmd, "-i", NOTIFY_SOUND_ID],
                stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
            )
        except OSError:
            pass
