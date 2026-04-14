from gi.repository import Gtk, Gdk

CSS = b"""
.pane-label {
    background-color: #303030;
    color: #aaaaaa;
    padding: 2px 8px;
    font-size: 10px;
}
.pane-label-active {
    background-color: #404040;
    color: #d0d0d0;
    padding: 2px 8px;
    font-size: 10px;
}
.pane-label-selected {
    background-color: #505050;
    color: #ffffff;
    padding: 2px 8px;
    font-size: 10px;
}
"""

LABEL_CLASSES = ["pane-label", "pane-label-active", "pane-label-selected"]


def apply_css():
    provider = Gtk.CssProvider()
    provider.load_from_data(CSS)
    screen = Gdk.Screen.get_default()
    Gtk.StyleContext.add_provider_for_screen(
        screen, provider, Gtk.STYLE_PROVIDER_PRIORITY_APPLICATION
    )


def rgba(hex_color):
    r = int(hex_color[1:3], 16) / 255
    g = int(hex_color[3:5], 16) / 255
    b = int(hex_color[5:7], 16) / 255
    return Gdk.RGBA(r, g, b, 1)
