#!/usr/bin/env python3
"""doctor.py: read-only health check for a Claude config dir and a Work dir.

  python3 lib/doctor.py [--claude-dir DIR] [--work-dir DIR]

One line per check: "ok  msg", "warn msg -- fix: ...", "bad  msg -- fix: ...".
Exit 1 if any bad, else 0. Writes nothing. Never prints file contents or env values.
Idea from agent-brain-harness harness.py (doctor_*) at f6c121a.
"""
import argparse
import json
import os
import re
import subprocess
import sys

counts = {"ok": 0, "warn": 0, "bad": 0}


def ok(msg):
    counts["ok"] += 1
    print("ok  " + msg)


def warn(msg, fix):
    counts["warn"] += 1
    print("warn %s -- fix: %s" % (msg, fix))


def bad(msg, fix):
    counts["bad"] += 1
    print("bad  %s -- fix: %s" % (msg, fix))


def read(p):
    with open(p, encoding="utf-8", errors="replace") as f:
        return f.read()


def expand(s, claude):
    s = re.sub(r"\$\{CLAUDE_CONFIG_DIR(:-[^}]*)?\}", lambda m: claude, s)
    s = re.sub(r"\$CLAUDE_CONFIG_DIR", lambda m: claude, s)
    home = os.path.expanduser("~")
    s = s.replace("${HOME}", home).replace("$HOME", home)
    return re.sub(r"(^|(?<=[\s\"']))~(?=/)", lambda m: home, s)


PATH_RE = re.compile(r"""[^\s"'`;|&<>()=]+\.(?:py|sh|mjs|cjs|js|ts)\b""")


def hook_commands(settings):
    hooks = settings.get("hooks")
    if not isinstance(hooks, dict):
        return []
    out = []
    for entries in hooks.values():
        if not isinstance(entries, list):
            continue
        for e in entries:
            for h in (e.get("hooks", []) if isinstance(e, dict) else []):
                if isinstance(h, dict) and isinstance(h.get("command"), str):
                    out.append(h["command"])
    return out


def check_roles(claude):
    hd = os.path.join(claude, "harness")
    for r in ("manager", "lead", "worker", "reviewer"):
        if os.path.isfile(os.path.join(hd, r + ".md")):
            ok("harness/%s.md exists" % r)
        else:
            bad("harness/%s.md is missing" % r, "restore it under %s" % hd)
    lead = os.path.join(hd, "lead.md")
    if os.path.isfile(lead):
        if "Reviewed by" in read(lead):
            ok("harness/lead.md has the verify step")
        else:
            warn('harness/lead.md has no "Reviewed by" line', "add the reviewer verify section to lead.md")


def check_settings(claude):
    sp = os.path.join(claude, "settings.json")
    if not os.path.isfile(sp):
        bad("settings.json is missing", "create %s" % sp)
        return None
    try:
        s = json.loads(read(sp))
        if not isinstance(s, dict):
            raise ValueError("not an object")
    except ValueError:
        bad("settings.json is not valid JSON", "fix it by hand or restore from backups/")
        return None
    ok("settings.json parses")
    cmds = hook_commands(s)
    missing = 0
    for c in cmds:
        for tok in PATH_RE.findall(c):
            p = expand(tok, claude)
            if not os.path.isabs(p):
                continue
            if not os.path.isfile(p):
                missing += 1
                bad("hook file missing: %s" % p, "restore it or remove the hook from settings.json")
    if not missing:
        ok("every hook file path exists (%d hook commands)" % len(cmds))
    return s


def check_wired(s):
    blob = "\n".join(hook_commands(s))
    for name in ("role_card", "git_guard", "secret_guard", "voice_nudge", "handoff_header_guard"):
        if name in blob:
            ok("hook wired: %s" % name)
        else:
            warn("hook not wired: %s" % name, "add %s.py to settings.json hooks" % name)


def check_handoffs(claude):
    d = os.path.join(claude, "harness", "handoffs")
    if not os.path.isdir(d):
        warn("no harness/handoffs dir", "mkdir %s" % d)
        return
    files = sorted(f for f in os.listdir(d) if f.endswith(".md") and os.path.isfile(os.path.join(d, f)))
    for f in files:
        head = read(os.path.join(d, f)).splitlines()[:5]
        miss = [k for k in ("Goal:", "State:", "Open:", "Next:", "Files:") if not any(l.startswith(k) for l in head)]
        if miss:
            warn("handoffs/%s lacks %s in its first 5 lines" % (f, ", ".join(miss)), "add the missing header lines at the top")
        else:
            ok("handoffs/%s header complete" % f)


def check_work(work):
    r = subprocess.run(["git", "-C", work, "config", "merge.ledger-rows.driver"], capture_output=True, text=True)
    if r.returncode == 0 and r.stdout.strip():
        ok("git merge driver ledger-rows set")
    else:
        warn("git merge driver ledger-rows not set", "git -C %s config merge.ledger-rows.driver 'python3 tools/ledger_merge.py %%O %%A %%B'" % work)
    ga = os.path.join(work, ".gitattributes")
    if os.path.isfile(ga) and "ledger-rows" in read(ga):
        ok(".gitattributes names ledger-rows")
    else:
        warn(".gitattributes has no ledger-rows line", "add a '<file> merge=ledger-rows' line to %s" % ga)
    if os.path.isfile(os.path.join(work, "tools", "expire_rows.py")):
        ok("tools/expire_rows.py exists")
    else:
        warn("tools/expire_rows.py is missing", "copy it from the vendored set (docs/VENDORED.md)")


def check_plugin(s):
    ep = s.get("enabledPlugins") if isinstance(s, dict) else None
    if isinstance(ep, dict) and any("manager-console" in k and v is True for k, v in ep.items()):
        ok("manager-console plugin enabled")
    else:
        warn("manager-console plugin not enabled", 'set an enabledPlugins "manager-console@..." key to true in settings.json')


def main(argv=None):
    ap = argparse.ArgumentParser(description="read-only Claude config health check")
    ap.add_argument("--claude-dir", default=os.path.expanduser("~/.claude"))
    ap.add_argument("--work-dir", default=os.path.expanduser("~/Work"))
    a = ap.parse_args(argv)
    claude, work = os.path.abspath(a.claude_dir), os.path.abspath(a.work_dir)
    check_roles(claude)
    s = check_settings(claude)
    if s is not None:
        check_wired(s)
    check_handoffs(claude)
    check_work(work)
    if s is not None:
        check_plugin(s)
    print("summary: %d ok, %d warn, %d bad" % (counts["ok"], counts["warn"], counts["bad"]))
    return 1 if counts["bad"] else 0


if __name__ == "__main__":
    sys.exit(main())
