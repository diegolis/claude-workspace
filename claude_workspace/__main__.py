import signal

from . import gi_setup  # noqa: F401
from gi.repository import Gtk

from .app import ClaudeWorkspace
from .config import load_config
from .style import apply_css
from .system import resolve_appearance


def main():
    signal.signal(signal.SIGINT, signal.SIG_DFL)
    config = load_config()
    appearance = resolve_appearance(config)
    apply_css()
    ClaudeWorkspace(config, appearance).show_all()
    Gtk.main()


if __name__ == "__main__":
    main()
