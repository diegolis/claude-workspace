import os


def read_cwd(pid):
    try:
        return os.readlink(f"/proc/{pid}/cwd")
    except OSError:
        return None


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
