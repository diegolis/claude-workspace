import subprocess

from gi.repository import Gdk, Vte, Pango

from .style import rgba

URL_PATTERN = (
    r"https?://[a-zA-Z0-9\-._~:/?#\[\]@!$&'()*+,;=%]+"
)


def create_terminal(appearance):
    term = Vte.Terminal()
    term.set_scroll_on_output(False)
    term.set_font(Pango.FontDescription(appearance["font"]))
    term.set_allow_hyperlink(True)
    _apply_colors(term, appearance)
    _setup_url_matching(term)
    return term


def _setup_url_matching(term):
    regex = Vte.Regex.new_for_match(URL_PATTERN, len(URL_PATTERN.encode()), 0)
    tag = term.match_add_regex(regex, 0)
    term.match_set_cursor_name(tag, "pointer")
    term.connect("button-press-event", _on_button_press)


def _on_button_press(term, event):
    if event.button != 1 or not (event.state & Gdk.ModifierType.CONTROL_MASK):
        return False
    match = term.match_check_event(event)
    if match and match[0]:
        subprocess.Popen(["xdg-open", match[0]],
                         stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        return True
    return False


def _apply_colors(term, appearance):
    fg = rgba(appearance["foreground"])
    bg = rgba(appearance["background"])
    palette = [rgba(c) for c in appearance["palette"]]
    term.set_colors(fg, bg, palette)
