import subprocess

DEFAULT_FONT = "Monospace 12"
DEFAULT_BG = "#000000"
DEFAULT_FG = "#ffffff"
DEFAULT_PALETTE = [
    "#171421", "#c01c28", "#26a269", "#a2734c",
    "#12488b", "#a347ba", "#2aa1b3", "#d0cfcc",
    "#5e5c64", "#f66151", "#33da7a", "#e9ad0c",
    "#2a7bde", "#c061cb", "#33c7de", "#ffffff",
]

GNOME_PROFILE = (
    "org.gnome.Terminal.Legacy.Profile:"
    "/org/gnome/terminal/legacy/profiles:/:"
    ":b1dcc9dd-5262-4d8d-a863-c897e6d979b9/"
)


def detect_font():
    return _gsettings("org.gnome.desktop.interface", "monospace-font-name")


def detect_background():
    return _gsettings(GNOME_PROFILE, "background-color")


def detect_foreground():
    return _gsettings(GNOME_PROFILE, "foreground-color")


def detect_palette():
    raw = _gsettings(GNOME_PROFILE, "palette")
    if not raw:
        return None
    return [c.strip().strip("'\"") for c in raw.strip("[]").split(",")]


def resolve_appearance(config):
    return {
        "font": config["font"] or detect_font() or DEFAULT_FONT,
        "background": config["background"] or DEFAULT_BG,
        "foreground": config["foreground"] or DEFAULT_FG,
        "palette": config["palette"] or detect_palette() or DEFAULT_PALETTE,
    }


def _gsettings(schema, key):
    try:
        out = subprocess.run(
            ["gsettings", "get", schema, key],
            capture_output=True, text=True, timeout=2,
        )
        return out.stdout.strip().strip("'") if out.returncode == 0 else None
    except (FileNotFoundError, subprocess.TimeoutExpired):
        return None
