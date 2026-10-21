#!/usr/bin/env python3
"""git_guard.py: PreToolUse(Bash) hook from agent-jepp-toolkit.

WHAT. Blocks `git push` (force or not) run by Claude. Brandon's rule: commit freely,
never push. Local destructive git (reset --hard, clean -f, add -A) is left to Team Kit's
per-repo guard so the two never double-fire.

ALLOWED.
- `git push --dry-run` / `-n`.
- Any push when the latest real user prompt in this session starts with /push, /stage
  or /promote (Team Kit's one-run push authorization). Cross-session messages do not count.

SEES THROUGH. `git -C dir push`, `git -c k=v push`, `--git-dir=`, env prefixes
(`FOO=1 git push`, `env ... git push`), `command`/`exec`/`nohup`/`sudo`/`time`,
absolute paths (`/usr/bin/git`), `sh -c` / `bash -c` / `zsh -c` / `eval` strings,
and git aliases that expand to push.

HOLES (this is a speed bump for an agent trying to comply, not a boundary):
a script file that pushes (`./deploy.sh`), python/node subprocess calls, `gh`, `curl`
to the forge API, `$(...)` that builds the word "push" at run time. The real gates are a
remote credential without push rights, branch protection, and CI.

EXIT CODES. 0 allow; 2 block (reason on stderr goes back to Claude). If the command
cannot be parsed and mentions "push", it blocks (fails closed). Any other internal error
allows (exit 0) so a bug cannot freeze every Bash call.
"""
from __future__ import annotations

import json
import os
import re
import shlex
import subprocess
import sys

AUTH_COMMANDS = ("/push", "/stage", "/promote")
WRAPPERS = {"command", "exec", "nohup", "sudo", "time", "builtin", "nice"}
SHELLS = {"sh", "bash", "zsh", "dash", "ksh"}
GIT_OPTS_WITH_ARG = {"-C", "-c", "--git-dir", "--work-tree", "--namespace", "--exec-path", "--config-env"}
SEPARATORS = {";", "&&", "||", "|", "&", "\n", "(", ")", "|&"}
ASSIGN = re.compile(r"^[A-Za-z_][A-Za-z0-9_]*=")


class Unparseable(Exception):
    pass


def tokenize(cmd: str) -> list[str]:
    lex = shlex.shlex(cmd.replace("\n", " ; "), posix=True, punctuation_chars=";&|()")
    lex.whitespace_split = True
    lex.commenters = ""
    try:
        return list(lex)
    except ValueError as e:  # unbalanced quotes
        raise Unparseable(str(e))


def segments(tokens: list[str]):
    seg: list[str] = []
    for t in tokens:
        if t in SEPARATORS:
            if seg:
                yield seg
            seg = []
        else:
            seg.append(t)
    if seg:
        yield seg


def git_aliases(cwd: str | None) -> dict[str, str]:
    try:
        out = subprocess.run(["git", "config", "--get-regexp", r"^alias\."], cwd=cwd or None,
                             capture_output=True, text=True, timeout=2).stdout
    except Exception:
        return {}
    aliases = {}
    for line in out.splitlines():
        name, _, value = line.partition(" ")
        aliases[name[len("alias."):]] = value
    return aliases


def push_in(cmd: str, cwd: str | None, depth: int = 0) -> str | None:
    """Return a description of the push found in cmd, or None."""
    if depth > 4:
        raise Unparseable("nesting too deep")
    for seg in segments(tokenize(cmd)):
        i = 0
        # strip env assignments and wrappers
        while i < len(seg):
            t = seg[i]
            if ASSIGN.match(t):
                i += 1
            elif os.path.basename(t) == "env":
                i += 1
                while i < len(seg) and (seg[i].startswith("-") or ASSIGN.match(seg[i])):
                    i += 1
            elif os.path.basename(t) in WRAPPERS:
                i += 1
                while i < len(seg) and seg[i].startswith("-"):
                    i += 1
            else:
                break
        if i >= len(seg):
            continue
        prog = os.path.basename(seg[i])
        rest = seg[i + 1:]
        if prog in SHELLS:
            for j, a in enumerate(rest):
                if a == "-c" or (a.startswith("-") and not a.startswith("--") and "c" in a[1:]):
                    if j + 1 < len(rest):
                        found = push_in(rest[j + 1], cwd, depth + 1)
                        if found:
                            return found
                    break
            continue
        if prog == "eval":
            found = push_in(" ".join(rest), cwd, depth + 1)
            if found:
                return found
            continue
        if prog != "git":
            continue
        # walk git global options to the subcommand
        k = 0
        while k < len(rest):
            a = rest[k]
            if a in GIT_OPTS_WITH_ARG:
                k += 2
            elif a.startswith("-"):
                k += 1
            else:
                break
        if k >= len(rest):
            continue
        sub, args = rest[k], rest[k + 1:]
        if sub not in ("push",):
            alias = git_aliases(cwd).get(sub)
            if alias:
                if alias.startswith("!"):
                    found = push_in(alias[1:], cwd, depth + 1)
                else:
                    found = push_in("git " + alias + " " + " ".join(shlex.quote(a) for a in args), cwd, depth + 1)
                if found:
                    return found
            continue
        if "--dry-run" in args or "-n" in args:
            continue
        return "git push"
    return None


def latest_user_prompt(transcript_path: str | None) -> str:
    if not transcript_path or not os.path.exists(transcript_path):
        return ""
    last = ""
    try:
        with open(transcript_path, encoding="utf-8", errors="replace") as f:
            for line in f:
                try:
                    e = json.loads(line)
                except ValueError:
                    continue
                if e.get("type") != "user" or e.get("isMeta"):
                    continue
                c = (e.get("message") or {}).get("content")
                if isinstance(c, str):
                    text = c
                elif isinstance(c, list):
                    if any(isinstance(b, dict) and b.get("type") == "tool_result" for b in c):
                        continue
                    text = " ".join(b.get("text", "") for b in c if isinstance(b, dict) and b.get("type") == "text")
                else:
                    continue
                if text.strip():
                    last = text
    except OSError:
        return ""
    return last


def authorized(prompt: str) -> bool:
    p = prompt.lstrip()
    if p.startswith("<cross-session-message"):
        return False
    # Claude Code records a slash command as <command-name>/push</command-name>
    m = re.search(r"<command-name>\s*(/[\w:-]+)\s*</command-name>", p)
    first = m.group(1) if m else (p.split() or [""])[0]
    if not first.startswith("/"):
        return False
    return "/" + first[1:].split(":")[-1] in AUTH_COMMANDS  # plugin form /kit:push counts


def block(reason: str) -> None:
    sys.stderr.write(
        "git_guard: " + reason + ". Commit freely; Brandon pushes. Ask him to run the push "
        "himself, or to type /push in this session for one run. (agent-jepp-toolkit)\n")
    sys.exit(2)


def main() -> None:
    try:
        data = json.load(sys.stdin)
    except Exception:
        sys.exit(0)
    if data.get("tool_name") != "Bash":
        sys.exit(0)
    cmd = (data.get("tool_input") or {}).get("command") or ""
    if "push" not in cmd and "git" not in cmd:
        sys.exit(0)
    try:
        found = push_in(cmd, data.get("cwd"))
    except Unparseable:
        if "push" in cmd:
            block("could not parse a command that mentions push, so it is blocked")
        sys.exit(0)
    except Exception:
        sys.exit(0)
    if not found:
        sys.exit(0)
    if authorized(latest_user_prompt(data.get("transcript_path"))):
        sys.exit(0)
    block("`git push` is blocked for agents")


if __name__ == "__main__":
    main()
