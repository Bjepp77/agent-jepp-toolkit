#!/usr/bin/env python3
"""git_guard.py: PreToolUse(Bash) hook from agent-jepp-toolkit.

WHAT. Blocks `git push` (force or not) run by Claude. Brandon's rule: commit freely,
never push. Local destructive git (reset --hard, clean -f, add -A) is left to Team Kit's
per-repo guard so the two never double-fire.

ALLOWED.
- `git push --dry-run` / `-n`.
- Any push when the owner's latest typed prompt in this session starts with /push, /stage
  or /promote (Team Kit's one-run push authorization). Cross-session messages do not count.

SEES THROUGH. `git -C dir push`, `git -c k=v push`, `--git-dir=`, env prefixes
(`FOO=1 git push`, `env ... git push`), `command`/`exec`/`nohup`/`sudo`/`time`/`nice`,
`timeout`/`caffeinate`/`stdbuf`/`xargs`, `find -exec`, absolute paths (`/usr/bin/git`),
`sh -c` / `bash -c` / `zsh -c` / `eval` strings, heredocs fed to a shell
(`bash <<EOF`, `sh -s <<EOF`, `cat <<EOF | bash`), `$(...)` and backticks (also inside
unquoted heredoc bodies), and git aliases that expand to push, including
`git -c alias.x=push x`.

HOLES (this is a speed bump for an agent trying to comply, not a boundary):
a script file that pushes (`./deploy.sh`), python/node subprocess calls, `gh`, `curl`
to the forge API, `$(...)` that builds the word "push" at run time. The real gates are a
remote credential without push rights, branch protection, and CI.

EXIT CODES. 0 allow; 2 block, including malformed hook JSON on stdin (reason on stderr
goes back to Claude). Heredoc bodies are
dropped first (they are data) unless a shell reads them or they expand `$(...)`. If the rest cannot be parsed and still contains
`git ... push`, it blocks (fails closed). Any other internal error also fails closed
when the command contains the word "push"; otherwise it allows (exit 0) so a bug
cannot freeze every Bash call.
"""
from __future__ import annotations

import json
import os
import re
import shlex
import subprocess
import sys

AUTH_COMMANDS = ("/push", "/stage", "/promote")
WRAPPERS = {"command", "exec", "nohup", "sudo", "time", "builtin", "nice",
            "timeout", "caffeinate", "stdbuf", "xargs"}
# wrapper options that take a separate value (`nice -n 10`, `xargs -I {}`, `caffeinate -t 5`)
WRAPPER_OPTS_WITH_ARG = {
    "nice": {"-n"}, "timeout": {"-s", "-k", "--signal", "--kill-after"},
    "caffeinate": {"-t", "-w"}, "stdbuf": {"-i", "-o", "-e"},
    "xargs": {"-I", "-n", "-P", "-L", "-s", "-d", "-E", "-a", "--delimiter", "--arg-file"},
    "sudo": {"-u", "-g", "-C", "-D", "-h", "-p", "-U"},
}
FIND_EXEC = {"-exec", "-execdir", "-ok", "-okdir"}
PUSH_OPTS_WITH_ARG = {"-o", "--push-option", "--repo", "--receive-pack", "--exec"}
SHELLS = {"sh", "bash", "zsh", "dash", "ksh"}
GIT_OPTS_WITH_ARG = {"-C", "-c", "--git-dir", "--work-tree", "--namespace", "--exec-path", "--config-env"}
SEPARATORS = {";", "&&", "||", "|", "&", "\n", "(", ")", "|&"}
ASSIGN = re.compile(r"^[A-Za-z_][A-Za-z0-9_]*=")


class Unparseable(Exception):
    pass


HEREDOC = re.compile(r"<<-?\s*(\\?)(['\"]?)([A-Za-z_][A-Za-z0-9_]*)\2")
GIT_PUSH_TEXT = re.compile(r"\bgit\s+(?:-\S+\s+(?:[^\s;&|]+\s+)?)*push\b")
# a shell (or eval/source/xargs) named on the heredoc line runs the body as commands
SHELL_ON_LINE = re.compile(r"(?:^|[\s;&|(])(?:[^\s;&|()]*/)?(?:sh|bash|zsh|dash|ksh|eval|source|xargs)(?=$|[\s;&|)])")


def substitutions(text: str, honor_single_quotes: bool = True) -> list[str]:
    """Bodies of `$(...)` and backtick substitutions. Single quotes stop them in a command
    line, but not in a heredoc body, so the caller says which applies."""
    out, i, n, in_dq = [], 0, len(text), False
    while i < n:
        c = text[i]
        if c == "\\":
            i += 2
            continue
        if c == "'" and honor_single_quotes and not in_dq:
            j = text.find("'", i + 1)
            i = n if j < 0 else j + 1
            continue
        if c == '"':
            in_dq = not in_dq
        elif c == "`":
            j = text.find("`", i + 1)
            out.append(text[i + 1:] if j < 0 else text[i + 1:j])
            i = n if j < 0 else j + 1
            continue
        elif c == "$" and text[i + 1:i + 2] == "(":
            depth, j = 1, i + 2
            while j < n and depth:
                depth += {"(": 1, ")": -1}.get(text[j], 0)
                j += 1
            out.append(text[i + 2:j - 1] if not depth else text[i + 2:])
            i = j
            continue
        i += 1
    return out


def strip_heredocs(cmd: str) -> tuple[str, list[str]]:
    """Drop heredoc bodies (commit messages, file contents): they are data. Return the
    remaining text plus the code hidden in bodies: the whole body when a shell reads it,
    and the `$(...)`/backtick parts of an unquoted body, which the shell expands."""
    out, extra, lines, i = [], [], cmd.split("\n"), 0
    while i < len(lines):
        line = lines[i]
        out.append(line)
        docs = [(m.group(3), bool(m.group(1) or m.group(2))) for m in HEREDOC.finditer(line)]
        to_shell = bool(docs) and bool(SHELL_ON_LINE.search(HEREDOC.sub(" ", line)))
        i += 1
        for d, quoted in docs:
            body = []
            while i < len(lines) and lines[i].strip() != d:
                body.append(lines[i])
                i += 1
            i += 1  # skip the delimiter line
            text = "\n".join(body)
            if to_shell:
                extra.append(text)
            if not quoted:
                extra.extend(substitutions(text, honor_single_quotes=False))
    return "\n".join(out), extra


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
    for sub_cmd in substitutions(cmd):
        found = push_in(sub_cmd, cwd, depth + 1)
        if found:
            return found
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
                w = os.path.basename(t)
                i += 1
                while i < len(seg) and seg[i].startswith("-"):
                    i += 2 if seg[i] in WRAPPER_OPTS_WITH_ARG.get(w, ()) else 1
                if w == "timeout" and i < len(seg):
                    i += 1  # the duration
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
        if prog == "find":
            for j, a in enumerate(rest):
                if a in FIND_EXEC:
                    found = push_in(" ".join(shlex.quote(x) for x in rest[j + 1:]), cwd, depth + 1)
                    if found:
                        return found
            continue
        if prog == "eval":
            found = push_in(" ".join(rest), cwd, depth + 1)
            if found:
                return found
            continue
        if prog != "git":
            continue
        # walk git global options to the subcommand
        k, inline_aliases = 0, {}
        while k < len(rest):
            a = rest[k]
            if a in GIT_OPTS_WITH_ARG:
                if a == "-c" and k + 1 < len(rest):
                    key, _, value = rest[k + 1].partition("=")
                    if key.lower().startswith("alias."):
                        inline_aliases[key[len("alias."):]] = value
                k += 2
            elif a.startswith("-"):
                k += 1
            else:
                break
        if k >= len(rest):
            continue
        sub, args = rest[k], rest[k + 1:]
        if sub not in ("push",):
            alias = inline_aliases.get(sub) or git_aliases(cwd).get(sub)
            if alias:
                if alias.startswith("!"):
                    found = push_in(alias[1:], cwd, depth + 1)
                else:
                    found = push_in("git " + alias + " " + " ".join(shlex.quote(a) for a in args), cwd, depth + 1)
                if found:
                    return found
            continue
        if is_dry_run(args):
            continue
        return "git push"
    return None


def is_dry_run(args: list[str]) -> bool:
    """True for a standalone `--dry-run` or `-n` push flag, not the value of `-o -n`."""
    k = 0
    while k < len(args):
        a = args[k]
        if a == "--":
            return False
        if a in ("--dry-run", "-n"):
            return True
        k += 2 if a in PUSH_OPTS_WITH_ARG else 1
    return False


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
                    # Only the owner's own typing can authorize: a plugin, peer or tool row cannot
                    human = (e.get("origin") or {}).get("kind") == "human"
                    last = text if human else ""
    except OSError:
        return ""
    return last


def authorized(prompt: str) -> bool:
    p = prompt.lstrip()
    if p.startswith("<cross-session-message"):
        return False
    # Claude Code records a slash command as <command-name>/push</command-name> at the start of the
    # prompt; the tag anywhere else is quoted text, not a command
    m = re.match(r"<command-name>\s*(/[\w:-]+)\s*</command-name>", p)
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
    except (ValueError, UnicodeError):
        block("malformed hook JSON on stdin")
    if not isinstance(data, dict):
        block("malformed hook JSON on stdin")
    if data.get("tool_name") != "Bash":
        sys.exit(0)
    tool_input = data.get("tool_input")
    if not isinstance(tool_input, dict):
        block("malformed hook JSON on stdin")
    cmd = tool_input.get("command") or ""
    if not isinstance(cmd, str):
        block("malformed hook JSON on stdin")
    if "push" not in cmd and "git" not in cmd:
        sys.exit(0)
    raw, hidden = cmd, []
    try:
        cmd, hidden = strip_heredocs(cmd)
        found = None
        for part in [cmd] + hidden:
            found = push_in(part, data.get("cwd"))
            if found:
                break
    except Unparseable:
        if GIT_PUSH_TEXT.search("\n".join([cmd] + hidden)):
            block("could not parse a command that contains `git ... push`, so it is blocked")
        sys.exit(0)
    except Exception:
        if re.search(r"\bpush\b", raw):
            block("the guard hit an internal error on a command that mentions push, so it is blocked")
        sys.exit(0)
    if not found:
        sys.exit(0)
    if authorized(latest_user_prompt(data.get("transcript_path"))):
        sys.exit(0)
    block("`git push` is blocked for agents")


if __name__ == "__main__":
    main()
