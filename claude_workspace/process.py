import os


def read_cwd(pid):
    try:
        return os.readlink(f"/proc/{pid}/cwd")
    except OSError:
        return None


def read_cmdline(pid):
    try:
        with open(f"/proc/{pid}/cmdline") as f:
            return f.read().replace("\0", " ").strip()
    except OSError:
        return None


def read_virtual_env(pid):
    env = _read_environ(pid)
    return env.get("VIRTUAL_ENV")


def _read_environ(pid):
    try:
        with open(f"/proc/{pid}/environ") as f:
            parts = f.read().split("\0")
        return dict(p.split("=", 1) for p in parts if "=" in p)
    except OSError:
        return {}


def find_child_cmd(shell_pid):
    children = _child_pids(shell_pid)
    if not children:
        return None
    return read_cmdline(children[0])


def find_claude_pid(shell_pid):
    for child in _child_pids(shell_pid):
        if _is_claude(child):
            return child
        deep = find_claude_pid(child)
        if deep:
            return deep
    return None


def _child_pids(parent_pid):
    try:
        with open(f"/proc/{parent_pid}/task/{parent_pid}/children") as f:
            return [int(p) for p in f.read().split() if p]
    except OSError:
        return []


def _is_claude(pid):
    try:
        with open(f"/proc/{pid}/cmdline") as f:
            return "claude" in f.read()
    except OSError:
        return False
