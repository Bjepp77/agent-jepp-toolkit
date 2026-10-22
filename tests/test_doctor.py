"""Runs lib/doctor.py against throwaway dirs. Never touches ~/.claude."""
import json
import os
import shutil
import subprocess
import sys
import tempfile

DOC = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "lib", "doctor.py")
HOOKS = ["role_card", "git_guard", "secret_guard", "voice_nudge", "handoff_header_guard"]
fails = []


def build(root, hooks_present=True):
    c, w = os.path.join(root, "claude"), os.path.join(root, "work")
    os.makedirs(os.path.join(c, "harness", "handoffs", "archive"))
    os.makedirs(os.path.join(c, "hooks"))
    os.makedirs(os.path.join(w, "tools"))
    for r in ("manager", "lead", "worker", "reviewer"):
        open(os.path.join(c, "harness", r + ".md"), "w").write("Reviewed by x\n" if r == "lead" else "x\n")
    open(os.path.join(c, "harness", "handoffs", "a.md"), "w").write("Goal: g\nState: s\nOpen: o\nNext: n\nFiles: f\n")
    ev = []
    for h in HOOKS:
        if hooks_present:
            open(os.path.join(c, "hooks", h + ".py"), "w").write("")
        ev.append({"hooks": [{"type": "command", "command": 'python3 "${CLAUDE_CONFIG_DIR:-$HOME/.claude}/hooks/%s.py"' % h}]})
    json.dump({"hooks": {"PreToolUse": ev}, "enabledPlugins": {"manager-console@x": True}}, open(os.path.join(c, "settings.json"), "w"))
    open(os.path.join(w, ".gitattributes"), "w").write("*.csv merge=ledger-rows\n")
    open(os.path.join(w, "tools", "expire_rows.py"), "w").write("")
    subprocess.run(["git", "init", "-q", w], check=True)
    subprocess.run(["git", "-C", w, "config", "merge.ledger-rows.driver", "true"], check=True)
    return c, w


def run(c, w):
    p = subprocess.run([sys.executable, DOC, "--claude-dir", c, "--work-dir", w], capture_output=True, text=True)
    return p.returncode, p.stdout


def check(name, cond):
    print(("PASS  " if cond else "FAIL  ") + name)
    if not cond:
        fails.append(name)


def case(fn):
    t = tempfile.mkdtemp()
    try:
        fn(t)
    finally:
        shutil.rmtree(t, ignore_errors=True)


def good(t):
    c, w = build(t)
    rc, out = run(c, w)
    check("good layout exits 0, no warn/bad lines", rc == 0 and "\nwarn" not in "\n" + out and "\nbad" not in "\n" + out)


def broken(t):
    c, w = build(t)
    open(os.path.join(c, "settings.json"), "w").write('{"hooks": ')
    rc, out = run(c, w)
    check("broken JSON exits 1 with bad line", rc == 1 and "bad  settings.json is not valid JSON" in out)


def nohook(t):
    c, w = build(t)
    os.remove(os.path.join(c, "hooks", "git_guard.py"))
    rc, out = run(c, w)
    check("missing hook file gives bad line, exit 1", rc == 1 and "bad  hook file missing" in out and "git_guard.py" in out)


def nohdr(t):
    c, w = build(t)
    open(os.path.join(c, "harness", "handoffs", "a.md"), "w").write("Goal: g\nState: s\n")
    rc, out = run(c, w)
    check("missing handoff header gives warn, exit 0", rc == 0 and "warn handoffs/a.md" in out)


for f in (good, broken, nohook, nohdr):
    case(f)
sys.exit(1 if fails else 0)
