#!/usr/bin/env python3
"""Pure merge helpers for install.sh. Each reads the current file, writes the merged
result to OUT, and never touches the destination itself (install.sh backs up and moves).
Exit 3 = destination is malformed; nothing should be written."""
import json
import sys

START = "<!-- agent-jepp-toolkit:start (managed by install.sh; edit the kit, not this block) -->"
END = "<!-- agent-jepp-toolkit:end -->"


def read(path):
    try:
        with open(path, encoding="utf-8") as f:
            return f.read()
    except FileNotFoundError:
        return None


def claude_md(dest, block_src, out):
    block = START + "\n" + read(block_src).rstrip("\n") + "\n" + END + "\n"
    cur = read(dest)
    if cur is None:
        new = block
    elif START.split(" (")[0] in cur:
        a = cur.index(START.split(" (")[0])
        b = cur.find(END, a)
        if b < 0:
            sys.stderr.write(f"{dest}: start marker without end marker; fix by hand\n")
            sys.exit(3)
        new = cur[:a] + block + cur[b + len(END):].lstrip("\n")
    else:
        new = cur.rstrip("\n") + "\n\n" + block
    open(out, "w", encoding="utf-8").write(new)


def settings(dest, command, out):
    cur = read(dest)
    try:
        data = json.loads(cur) if cur and cur.strip() else {}
    except ValueError as e:
        sys.stderr.write(f"{dest}: not valid JSON ({e}); nothing written\n")
        sys.exit(3)
    if not isinstance(data, dict):
        sys.stderr.write(f"{dest}: top level is not an object; nothing written\n")
        sys.exit(3)
    pre = data.setdefault("hooks", {}).setdefault("PreToolUse", [])
    present = any("hooks/git_guard.py" in (h.get("command") or "")
                  for entry in pre for h in entry.get("hooks", []))
    if not present:
        pre.append({"matcher": "Bash", "hooks": [{"type": "command", "command": command, "timeout": 5}]})
    text = json.dumps(data, indent=2) + "\n"
    json.loads(text)  # validate what we are about to write
    if cur is not None and present:
        text = cur  # unchanged: keep the user's exact formatting
    open(out, "w", encoding="utf-8").write(text)


if __name__ == "__main__":
    mode, args = sys.argv[1], sys.argv[2:]
    {"claude-md": claude_md, "settings": settings}[mode](*args)
