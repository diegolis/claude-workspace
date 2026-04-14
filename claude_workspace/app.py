import os

from gi.repository import Gtk, Vte, GLib

from .config import load_state, save_state
from .pane import Pane
from .terminal import create_terminal


class ClaudeWorkspace(Gtk.Window):
    def __init__(self, config, appearance):
        super().__init__(title="Claude Workspace")
        self.config = config
        self.appearance = appearance
        self.selected_pane = None
        self.cols = config["columns"]
        self.panes = self._create_panes()
        self.grid = Gtk.Grid(row_homogeneous=True, column_homogeneous=True)
        self.set_default_size(1920, 1080)
        self.maximize()
        self.add(self.grid)
        self._build_grid()
        GLib.idle_add(self._spawn_all)
        GLib.timeout_add_seconds(3, self._refresh_titles)
        GLib.timeout_add_seconds(config["save_interval"], self._save)
        self.connect("destroy", self._quit)

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
            Vte.PtyFlags.DEFAULT, cwd, ["/bin/bash", "-l"],
            None, GLib.SpawnFlags.DEFAULT, None, None,
            -1, None, self._on_spawned, pane,
        )

    def _on_spawned(self, terminal, pid, error, pane):
        if error:
            return
        pane.shell_pid = pid
        GLib.timeout_add(800, self._launch_claude, pane)

    def _launch_claude(self, pane):
        cmd = pane.claude_command(self.config["claude_flags"])
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
