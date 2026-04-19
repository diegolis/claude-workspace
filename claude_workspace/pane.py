import os

from .process import find_child_cmd, find_claude_pid, read_cwd, read_virtual_env
from .session import find_session_id, session_exists
from .style import LABEL_CLASSES

GENERIC_TITLES = {"", "Claude Code", "✳ Claude Code"}


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
        last_cmd = saved.get("last_command")
        self.last_command = None if (last_cmd and self._is_internal_cmd(last_cmd)) else last_cmd
        self.virtual_env = saved.get("virtual_env")
        self.shell_pid = None
        self.terminal = None
        self.label = None
        self.box = None
        self.claude_running = False
        self.term_title = ""
        self.notifying = False
        self.blink_on = False
        self.silenced = False

    def title_text(self):
        path = shorten_path(self.cwd)
        session = self.session_id[:8] if self.session_id else "new"
        suffix = f"  —  {self.term_title}" if self.term_title else ""
        return f"  {path}    [{session}]{suffix}"

    def startup_commands(self, claude_flags=""):
        cmds = []
        if self.virtual_env:
            cmds.append(f"source {self.virtual_env}/bin/activate")
        cmd = self._resolve_command(claude_flags)
        if cmd:
            cmds.append(cmd)
        return cmds

    def refresh(self):
        if not self.shell_pid:
            return
        claude_pid = find_claude_pid(self.shell_pid)
        self.claude_running = claude_pid is not None
        active_pid = claude_pid or self.shell_pid
        self.cwd = read_cwd(active_pid) or self.cwd
        self.virtual_env = read_virtual_env(self.shell_pid) or self.virtual_env
        self._refresh_command(claude_pid)

    def update_label(self):
        self.label.set_text(self.title_text())
        self._set_label_class(self._label_class())

    def _label_class(self):
        if self.notifying:
            return "pane-label-notify-on" if self.blink_on else "pane-label-notify-off"
        return "pane-label-active" if self.claude_running else "pane-label"

    def to_dict(self):
        return {
            "dir": self.cwd,
            "session_id": self.session_id,
            "last_command": self.last_command,
            "virtual_env": self.virtual_env,
        }

    def _resolve_command(self, flags=""):
        if self.last_command is None:
            return None
        if not self._is_claude_cmd(self.last_command):
            return self.last_command
        return self._claude_command(flags)

    def _claude_command(self, flags=""):
        parts = ["claude"] + (flags.split() if flags else [])
        if self.session_id and session_exists(self.session_id, self.cwd):
            parts += ["--resume", self.session_id]
        return " ".join(parts)

    def _refresh_command(self, claude_pid):
        if claude_pid:
            self.session_id = find_session_id(claude_pid) or self.session_id
            self.last_command = "claude"
            return
        child_cmd = find_child_cmd(self.shell_pid)
        if child_cmd is None:
            self.last_command = None
            return
        if not self._is_internal_cmd(child_cmd):
            self.last_command = child_cmd

    def _set_label_class(self, css_class):
        ctx = self.label.get_style_context()
        for c in LABEL_CLASSES:
            ctx.remove_class(c)
        ctx.add_class(css_class)

    @staticmethod
    def _is_claude_cmd(cmd):
        return "claude" in cmd

    @staticmethod
    def _is_internal_cmd(cmd):
        """Filter out shell-internal commands that shouldn't be restored."""
        internal_patterns = [
            "pyenv-rehash", "pyenv-init", "pyenv-versions", "pyenv-hooks",
            "nvm.sh", "virtualenvwrapper",
        ]
        return any(p in cmd for p in internal_patterns)
