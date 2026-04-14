# claude-workspace

A multi-pane terminal grid for [Claude Code](https://claude.ai/claude-code) with automatic session persistence. Run multiple Claude Code instances side by side and pick up exactly where you left off after a restart.

## Features

- **Grid layout** — configurable N×M grid of terminal panes
- **Session persistence** — saves working directory and Claude session ID every 60s
- **Auto-resume** — restarts each pane in the right directory with `claude --resume`
- **Live titles** — each pane shows its current path, session ID, and Claude's activity
- **Rearrangeable** — click a title to select it, click another to swap them
- **System colors** — auto-detects your GNOME terminal font and color palette

## Prerequisites

**Linux only** (GTK 3 + VTE). macOS/Windows support is not available yet — see [#1](https://github.com/diegolis/claude-workspace/issues/1).

On Debian/Ubuntu:

```bash
sudo apt install python3-gi gir1.2-gtk-3.0 gir1.2-vte-2.91
```

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

- **Click title** — select pane (highlighted)
- **Click another title** — swap the two panes
- **Click same title** — deselect

### State files

- Config: `~/.config/claude-workspace/config.json`
- State: `~/.local/state/claude-workspace/state.json`

## How it works

Each pane spawns a bash shell and runs `claude --resume <session_id>` (or plain `claude` for new sessions). A background timer polls `/proc` every 3 seconds to read each pane's working directory and match it to a Claude session file. State is saved to disk every 60 seconds.

On restart, each pane restores its last directory and resumes its Claude conversation.

## License

MIT
