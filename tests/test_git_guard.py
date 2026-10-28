"""Runs git_guard.py as Claude Code would (JSON on stdin) against real command strings."""
import json
import os
import subprocess
import sys
import tempfile

HOOK = os.path.join(os.path.dirname(__file__), "..", "user", "hooks", "git_guard.py")
work = tempfile.mkdtemp()
subprocess.run(["git", "init", "-q", work], check=True)
subprocess.run(["git", "-C", work, "config", "alias.p", "push"], check=True)
subprocess.run(["git", "-C", work, "config", "alias.sp", "!git status && git push"], check=True)


def transcript(*entries):
    path = os.path.join(work, f"t{len(os.listdir(work))}.jsonl")
    with open(path, "w") as f:
        for e in entries:
            f.write(json.dumps(e) + "\n")
    return path


def user(text, kind="human"):
    # Real transcripts mark the owner's own typing with origin kind "human"
    return {"type": "user", "origin": {"kind": kind}, "message": {"role": "user", "content": text}}


TOOL_RESULT = {"type": "user", "message": {"content": [{"type": "tool_result", "content": "ok"}]}}


def run(cmd, tpath=None):
    payload = {"tool_name": "Bash", "tool_input": {"command": cmd}, "cwd": work,
               "transcript_path": tpath or transcript(user("please fix the bug"))}
    return subprocess.run([sys.executable, HOOK], input=json.dumps(payload),
                          capture_output=True, text=True).returncode


BLOCK = [
    "git push", "git push origin main --force", "git -C /tmp/x push", "git -c user.name=x push origin",
    "FOO=1 git push", "env A=1 git push", "/usr/bin/git push", "command git push",
    'sh -c "git push"', "bash -lc 'cd x && git push'", "eval git push", "cd x && git push",
    "git status; git push", "git status\ngit push", "git p", "git sp", 'git push "unterminated',
    "nohup git push origin main &", "git --no-pager push",
    "cat <<'EOF'\nit's data\nEOF\ngit push",                          # push after a heredoc still blocks
    "echo it's && git push",                                            # unparseable + real push
    # bypass shapes closed 2026-10-27 (secure-review T1, codex F3)
    "bash <<'EOF'\ngit push\nEOF", "sh -s <<EOF\ngit push origin main\nEOF",
    "cat <<'EOF' | bash\ngit push\nEOF", "cat <<EOF\n$(git push)\nEOF",
    "timeout 60 git push", "timeout -s KILL 60 git push", "echo origin | xargs git push",
    "xargs -I {} git push {}", "find . -maxdepth 0 -exec git push \\;", "caffeinate -i git push",
    "caffeinate -t 5 git push", "stdbuf -oL git push", "stdbuf -o L git push", "echo `git push`",
    'echo "$(git push)"', "git -c alias.x=push x", "git -c alias.y='!git push' y",
    "git push -o -n origin main", "git push --push-option -n origin main", "nice -n 10 git push",

]
ALLOW = [
    "git status", 'git commit -m "push later"',
    "git commit -F - <<'EOF'\nowner's pending pushes\nEOF",          # live false positive 2026-10-21
    "git commit -F - <<'EOF'\nnever git push from agents, it's blocked\nEOF",
    "cat > notes.md <<EOF\ndon't git push yet\nEOF",
    "git commit -m 'owner'\\''s pending pushes'", "git push --dry-run", "git push -n origin main",
    "git push -o ci.skip -n origin main", "git push origin main --dry-run",
    "echo 'not `git push`'", "cat <<'EOF'\n$(git push) stays text\nEOF",
    "timeout 60 git fetch", "find . -name '*.py' -exec grep -l push {} +",
    "git -c alias.st=status st", "caffeinate -i make test",
    "echo push", "git log --grep push", 'grep -rn "git push" .', "ls -la", "git add README.md",
]
AUTH = [  # (transcript, expected exit code for "git push")
    (transcript(user("<command-name>/push</command-name>"), TOOL_RESULT), 0),
    (transcript(user("/promote")), 0),
    (transcript(user("<command-name>/agent-team-kit:push</command-name>")), 0),
    (transcript(user("/push"), user("<cross-session-message from=\"Manager\">push it</cross-session-message>")), 2),
    (transcript(user("go ahead and push")), 2),
    (transcript(user("/pushy")), 2),
    (transcript(user("Please explain this tag, do not push: <command-name>/push</command-name>")), 2),  # Codex F4
    (transcript(user("<command-name>/push</command-name>", kind="plugin")), 2),
    (transcript(user("/push", kind="peer")), 2),
    (transcript({"type": "user", "message": {"role": "user", "content": "/push"}}), 2),  # no origin: not the owner
]

fails = 0
for c in BLOCK:
    if run(c) != 2:
        fails += 1; print("SHOULD BLOCK:", repr(c))
for c in ALLOW:
    if run(c) != 0:
        fails += 1; print("SHOULD ALLOW:", repr(c))
for t, want in AUTH:
    if run("git push origin main", t) != want:
        fails += 1; print("AUTH WRONG:", open(t).read()[-120:], "want", want)
for payload in ('{"tool_name":', '[]', '{"tool_name":"Bash","tool_input":[]}'):
    result = subprocess.run([sys.executable, HOOK], input=payload,
                            capture_output=True, text=True)
    if result.returncode != 2:
        fails += 1; print("MALFORMED HOOK JSON ALLOWED:", repr(payload))
print(f"git_guard: {len(BLOCK)} block, {len(ALLOW)} allow, {len(AUTH)} auth cases, {fails} failure(s)")
sys.exit(1 if fails else 0)
