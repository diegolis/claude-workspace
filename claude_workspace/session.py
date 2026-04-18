import glob
import json
import os

SESSIONS_DIR = os.path.expanduser("~/.claude/sessions")
PROJECTS_DIR = os.path.expanduser("~/.claude/projects")


def find_session_id(pid):
    for path in glob.glob(f"{SESSIONS_DIR}/*.json"):
        sid = _match_pid(path, pid)
        if sid:
            return sid
    return None


def session_exists(session_id, cwd):
    return _session_path(session_id, cwd) is not None


def last_assistant_text(session_id, cwd, max_chars=120):
    path = _session_path(session_id, cwd)
    if not path:
        return None
    try:
        with open(path, "rb") as f:
            lines = f.readlines()
    except OSError:
        return None
    for raw in reversed(lines):
        try:
            entry = json.loads(raw)
        except (json.JSONDecodeError, ValueError):
            continue
        if entry.get("type") != "assistant":
            continue
        content = entry.get("message", {}).get("content", [])
        for item in content:
            if item.get("type") == "text":
                text = (item.get("text") or "").strip()
                if text:
                    return _truncate(text, max_chars)
    return None


def _session_path(session_id, cwd):
    project_key = cwd.replace("/", "-")
    jsonl = os.path.join(PROJECTS_DIR, project_key, f"{session_id}.jsonl")
    return jsonl if os.path.exists(jsonl) else None


def _truncate(text, limit):
    if len(text) <= limit:
        return text
    return text[:limit].rstrip() + "…"


def _match_pid(path, pid):
    try:
        with open(path) as f:
            data = json.load(f)
        return data["sessionId"] if data.get("pid") == pid else None
    except (json.JSONDecodeError, OSError, KeyError):
        return None
