import json
import os

CONFIG_DIR = os.path.expanduser("~/.config/claude-workspace")
CONFIG_PATH = os.path.join(CONFIG_DIR, "config.json")
STATE_DIR = os.path.expanduser("~/.local/state/claude-workspace")
STATE_PATH = os.path.join(STATE_DIR, "state.json")

DEFAULT_CONFIG = {
    "columns": 2,
    "save_interval": 60,
    "claude_flags": "",
    "font": None,
    "background": None,
    "foreground": None,
    "palette": None,
    "panes": [
        {"name": "project-1", "directory": "~"},
        {"name": "project-2", "directory": "~"},
        {"name": "project-3", "directory": "~"},
        {"name": "project-4", "directory": "~"},
    ],
}


def load_config():
    ensure_config()
    with open(CONFIG_PATH) as f:
        user = json.load(f)
    return {**DEFAULT_CONFIG, **user}


def ensure_config():
    if os.path.exists(CONFIG_PATH):
        return
    os.makedirs(CONFIG_DIR, exist_ok=True)
    with open(CONFIG_PATH, "w") as f:
        json.dump(DEFAULT_CONFIG, f, indent=2)
    print(f"Config created at {CONFIG_PATH} — edit it to add your panes.")


def load_state():
    try:
        with open(STATE_PATH) as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        return {}


def save_state(state):
    os.makedirs(STATE_DIR, exist_ok=True)
    with open(STATE_PATH, "w") as f:
        json.dump(state, f, indent=2)
