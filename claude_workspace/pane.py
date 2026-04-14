import os
from .process import find_claude_pid, read_cwd
from .session import find_session_id, session_exists
from .style import LABEL_CLASSES


def shorten_path(path):
    home = os.path.expanduser("~")
    return path.replace(home, "~") if path else "?"


class Pane:
    def __init__(self, name, default_dir, saved=None):
        saved = saved or {}
        self.name = name
        self.default_dir = os.path.expanduser(default_dir)
        self.cwd = saved.get("dir", self.default_dir)
        self.session_id = saved.get("session_id")
        self.shell_pid = None
        self.terminal = None
        self.label = None
        self.box = None
        self.claude_running = False
        self.term_title = ""

    def title_text(self):
        path = shorten_path(self.cwd)
        session = self.session_id[:8] if self.session_id else "new"
        suffix = f"  —  {self.term_title}" if self.term_title else ""
        return f"  {path}    [{session}]{suffix}"

    def claude_command(self, flags=""):
        parts = ["claude"] + (flags.split() if flags else [])
        if self.session_id and session_exists(self.session_id, self.cwd):
            parts += ["--resume", self.session_id]
        return " ".join(parts)

    def refresh(self):
        if not self.shell_pid:
            return
        claude_pid = find_claude_pid(self.shell_pid)
        self.claude_running = claude_pid is not None
        active_pid = claude_pid or self.shell_pid
        self.cwd = read_cwd(active_pid) or self.cwd
        if claude_pid:
            self.session_id = find_session_id(claude_pid) or self.session_id

    def update_label(self):
        self.label.set_text(self.title_text())
        cls = "pane-label-active" if self.claude_running else "pane-label"
        self._set_label_class(cls)

    def to_dict(self):
        return {"dir": self.cwd, "session_id": self.session_id}

    def _set_label_class(self, css_class):
        ctx = self.label.get_style_context()
        for c in LABEL_CLASSES:
            ctx.remove_class(c)
        ctx.add_class(css_class)
