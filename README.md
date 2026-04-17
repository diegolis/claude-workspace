# claude-workspace

A multi-pane terminal grid for [Claude Code](https://claude.ai/claude-code) with automatic session persistence. Run multiple Claude Code instances side by side and pick up exactly where you left off after a restart.

## Features

- **Grid layout** — configurable N×M grid of terminal panes
- **Session persistence** — saves working directory, Claude session ID, virtualenv, and last running program every 60s
- **Auto-resume** — restarts each pane in the right directory, re-activates its virtualenv, and relaunches whatever was running (Claude with `--resume`, or any other program like `htop`, `vim`, etc.)
- **Live titles** — each pane shows its current path, session ID, and Claude's activity
- **Rearrangeable** — click a title to select it, click another to swap them
- **Bell notifications** — when Claude finishes (or any program rings the terminal bell) in a pane you're not looking at, the label blinks orange, the window asks for attention, a desktop notification pops up, and a short sound plays. Click the notification to raise the window and focus that pane's terminal
- **Clickable URLs** — Ctrl+Click a URL in any pane to open it in your default browser
- **System colors** — auto-detects your GNOME terminal font and color palette

## Prerequisites

**Linux only** (GTK 3 + VTE). macOS/Windows support is not available yet — see [#1](https://github.com/diegolis/claude-workspace/issues/1).

On Debian/Ubuntu:

```bash
sudo apt install python3-gi gir1.2-gtk-3.0 gir1.2-vte-2.91 gir1.2-notify-0.7 xdg-utils gnome-session-canberra sound-theme-freedesktop
```

- `python3-gi`, `gir1.2-gtk-3.0`, `gir1.2-vte-2.91` — GTK 3 + VTE bindings (required)
- `gir1.2-notify-0.7` — libnotify GIR bindings used for desktop bell notifications with a clickable "focus pane" action (optional; without it the label still blinks but no popup appears). `libnotify-bin` is not required
- `xdg-utils` — provides `xdg-open` for Ctrl+Click URL opening (optional; usually preinstalled)
- `gnome-session-canberra`, `sound-theme-freedesktop` — provide `canberra-gtk-play` and the `message-new-instant` sound used for the bell (optional; without them, notifications are silent)

[Claude Code](https://docs.anthropic.com/en/docs/claude-code) must be installed and available in your PATH.

## Install

```bash
git clone https://github.com/diegolis/claude-workspace.git
cd claude-workspace
make install
```

This installs to `~/.local/bin/` and `~/.local/lib/`. Make sure `~/.local/bin` is in your `PATH`.

To uninstall:

```bash
make uninstall
```

For development, run directly from the repo:

```bash
PYTHONPATH=. python3 -m claude_workspace
```

## Usage

```bash
claude-workspace
```

On first run, a default config is created at `~/.config/claude-workspace/config.json`. Edit it to define your panes.

The number of panes is determined by the `panes` array — add as many as you need. The `columns` value controls the grid layout. For example, 8 panes with 4 columns gives a 4×2 grid:

```json
{
  "columns": 4,
  "panes": [
    {"name": "api-1", "directory": "~/projects/my-api"},
    {"name": "api-2", "directory": "~/projects/my-api"},
    {"name": "api-3", "directory": "~/projects/my-api"},
    {"name": "api-4", "directory": "~/projects/my-api"},
    {"name": "web", "directory": "~/projects/my-web"},
    {"name": "infra", "directory": "~/projects/infra"},
    {"name": "docs", "directory": "~/projects/docs"},
    {"name": "scripts", "directory": "~/projects/scripts"}
  ]
}
```

Multiple panes can point to the same directory — each one maintains its own independent Claude session.

### Skip permissions prompt

By default, Claude asks for permission before running commands. To bypass this, add the `--dangerously-skip-permissions` flag:

```json
{
  "claude_flags": "--dangerously-skip-permissions"
}
```

### Enabling bell notifications

claude-workspace reacts to the VTE `bell` signal (any `\a` / BEL `0x07` written to the terminal). Claude Code's built-in `"preferredNotifChannel": "terminal_bell"` setting only fires on a narrow set of events (permission prompts, long-running idle timeouts) and in practice rarely emits a BEL during a normal interactive session.

A `Stop` hook (fires on every turn end) ends up being noisy: you get a notification for every individual response, even while you're actively chatting with Claude. A better option is the `Notification` hook, which only fires when Claude actually needs your attention — specifically on `idle_notification` (Claude finished a turn and you haven't replied for ~60s) and `permission_request` (Claude is waiting for tool-use approval). Add to `~/.claude/settings.json`:

```json
{
  "hooks": {
    "Notification": [
      {
        "hooks": [
          {"type": "command", "command": "printf '\\a' > /dev/tty"}
        ]
      }
    ]
  }
}
```

The idle threshold is hardcoded to 60 seconds inside Claude Code (the `messageIdleNotifThresholdMs` key in the default config is not user-settable at the time of writing). claude-workspace's `_on_bell` handler suppresses the notification when the pane is focused and the window is active — so you only get notified for panes you're not looking at. Restart your Claude sessions (or the whole app) for the hook to take effect.

### Configuration reference

| Key | Default | Description |
|-----|---------|-------------|
| `columns` | `2` | Number of columns in the grid |
| `save_interval` | `60` | Seconds between state saves |
| `claude_flags` | `""` | Extra flags passed to `claude` |
| `font` | `null` | Terminal font (null = auto-detect system monospace font) |
| `background` | `null` | Terminal background color hex (null = `#000000`) |
| `foreground` | `null` | Terminal foreground color hex (null = `#ffffff`) |
| `palette` | `null` | 16-color terminal palette (null = auto-detect from GNOME, fallback to Ubuntu default) |
| `panes` | | Array of `{name, directory}` objects — add as many as you want |

### Keyboard / Mouse

- **Click title** — select pane (highlighted); also clears any pending bell notification on that pane
- **Click another title** — swap the two panes
- **Click same title** — deselect
- **Ctrl+Click on URL** — open in default browser

### State files

- Config: `~/.config/claude-workspace/config.json`
- State: `~/.local/state/claude-workspace/state.json`

## How it works

Each pane spawns a bash shell and runs `claude --resume <session_id>` (or plain `claude` for new sessions). A background timer polls `/proc` every 3 seconds to read each pane's working directory, active virtualenv (`VIRTUAL_ENV`), and currently running child process, and to match it to a Claude session file. State is saved to disk every 60 seconds.

On restart, each pane restores its last directory, re-activates its virtualenv if one was active, and relaunches the program that was running (Claude resumes the conversation; other programs like `htop` or `vim` are re-executed as-is).

Bell notifications use the VTE `bell` signal (triggered by BEL `\a`). When it fires in a pane that isn't focused, the window sets its urgency hint, the pane label starts blinking, libnotify pops a desktop notification (via the Python `Notify` GI binding, with a "default" action wired up), and `canberra-gtk-play` plays the `message-new-instant` sound from the freedesktop theme. Clicking the notification raises the window and grabs focus for that pane's terminal. Focusing the terminal or clicking the label also clears the state.

## License

MIT
