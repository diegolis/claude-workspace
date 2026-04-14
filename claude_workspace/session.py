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
    project_key = cwd.replace("/", "-")
    jsonl = os.path.join(PROJECTS_DIR, project_key, f"{session_id}.jsonl")
    return os.path.exists(jsonl)


def _match_pid(path, pid):
    try:
        with open(path) as f:
            data = json.load(f)
        return data["sessionId"] if data.get("pid") == pid else None
    except (json.JSONDecodeError, OSError, KeyError):
        return None
