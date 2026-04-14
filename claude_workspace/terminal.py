from gi.repository import Vte, Pango

from .style import rgba


def create_terminal(appearance):
    term = Vte.Terminal()
    term.set_scroll_on_output(False)
    term.set_font(Pango.FontDescription(appearance["font"]))
    _apply_colors(term, appearance)
    return term


def _apply_colors(term, appearance):
    fg = rgba(appearance["foreground"])
    bg = rgba(appearance["background"])
    palette = [rgba(c) for c in appearance["palette"]]
    term.set_colors(fg, bg, palette)
