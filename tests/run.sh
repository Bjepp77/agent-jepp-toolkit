#!/bin/bash
# tests/run.sh: every check for agent-jepp-toolkit. Uses only throwaway dirs; never touches ~/.claude.
#   bash tests/run.sh
set -uo pipefail
KIT="$(cd "$(dirname "$0")/.." && pwd)"
T="$(mktemp -d)"; trap 'rm -rf "$T"' EXIT
FAIL=0
ok()   { echo "PASS  $1"; }
bad()  { echo "FAIL  $1"; FAIL=1; }
check(){ if eval "$2"; then ok "$1"; else bad "$1"; fi; }

echo "== static"
check "user/CLAUDE.md is <= 60 lines ($(wc -l < "$KIT/user/CLAUDE.md"))" '[ $(wc -l < "$KIT/user/CLAUDE.md") -le 60 ]'
check "no Team Kit identifiers in shipped files" \
  '! grep -rlE "bash-guard|GIT_BLOCKS|sharedTreeOnly|agent-coord|memory-pack|SCHEMA_RE" "$KIT/user" "$KIT/repo" "$KIT/lib" "$KIT/install.sh"'
check "shell syntax" 'bash -n "$KIT/install.sh" && bash -n "$KIT/repo/secret-scan.sh"'

echo "== git_guard"
check "git_guard command cases" 'python3 "$KIT/tests/test_git_guard.py"'

echo "== doctor"
check "doctor cases" 'python3 "$KIT/tests/test_doctor.py"'

echo "== installer, throwaway CLAUDE_CONFIG_DIR"
CFG="$T/cfg"; mkdir -p "$CFG/hooks"
printf '# My own notes\nkeep this line\n' > "$CFG/CLAUDE.md"
cat > "$CFG/settings.json" <<'JSON'
{"model": "opus", "hooks": {"PreToolUse": [
  {"matcher": "Bash|Read|Grep", "hooks": [{"type": "command", "command": "python3 \"${CLAUDE_CONFIG_DIR:-$HOME/.claude}/hooks/secret_guard.py\"", "timeout": 5}]},
  {"matcher": "mcp__.*__(send_message|reply)", "hooks": [{"type": "command", "command": "python3 \"${CLAUDE_CONFIG_DIR:-$HOME/.claude}/hooks/send_guard.py\""}]}],
 "SessionStart": [{"hooks": [{"type": "command", "command": "node \"${CLAUDE_CONFIG_DIR:-$HOME/.claude}/hooks/team-memory.mjs\""}]}]}}
JSON
cp "$CFG/settings.json" "$T/settings.orig"
export CLAUDE_CONFIG_DIR="$CFG"
check "dry run writes nothing" 'out=$("$KIT/install.sh" --dry-run) && cmp -s "$CFG/settings.json" "$T/settings.orig" && [ ! -e "$CFG/skills" ] && [ ! -d "$CFG/backups" ]'
check "first install succeeds" '"$KIT/install.sh" > "$T/run1.log"'
cat "$T/run1.log" | sed 's/^/      /'
check "user CLAUDE.md content kept" 'grep -q "keep this line" "$CFG/CLAUDE.md"'
check "managed block present once" '[ $(grep -c "agent-jepp-toolkit:start" "$CFG/CLAUDE.md") -eq 1 ]'
check "existing hooks preserved" 'python3 - "$T/settings.orig" "$CFG/settings.json" <<PY
import json,sys
a=json.load(open(sys.argv[1])); b=json.load(open(sys.argv[2]))
cmds=lambda d:[h["command"] for ev in d["hooks"].values() for e in ev for h in e["hooks"]]
assert set(cmds(a)) <= set(cmds(b)), "lost a hook"
assert b["model"]=="opus"
assert sum("git_guard.py" in c for c in cmds(b))==1
PY'
check "backup holds the pre-install files" 'BK=$(ls -d "$CFG"/backups/agent-jepp-toolkit-*) && cmp -s "$BK/files$CFG/settings.json" "$T/settings.orig" && grep -q "rm -f" "$BK/RESTORE.txt"'
check "installed hook runs and blocks a push" 'echo "{\"tool_name\":\"Bash\",\"tool_input\":{\"command\":\"git push\"}}" | python3 "$CFG/hooks/git_guard.py" 2>/dev/null; [ $? -eq 2 ]'
check "re-run changes nothing" '"$KIT/install.sh" | grep -q "Nothing to change" && [ $(ls -d "$CFG"/backups/agent-jepp-toolkit-* | wc -l) -eq 1 ]'
check "kit edit updates the block in place on re-run" 'cp -R "$KIT" "$T/kit2" && echo "- extra rule" >> "$T/kit2/user/CLAUDE.md" && sleep 1 && "$T/kit2/install.sh" >/dev/null && grep -q "extra rule" "$CFG/CLAUDE.md" && [ $(grep -c "agent-jepp-toolkit:start" "$CFG/CLAUDE.md") -eq 1 ] && grep -q "keep this line" "$CFG/CLAUDE.md"'
check "restore script undoes an install" 'BK=$(ls -d "$CFG"/backups/agent-jepp-toolkit-* | tail -1) && bash "$BK/RESTORE.txt" && ! grep -q "extra rule" "$CFG/CLAUDE.md" && grep -q "agent-jepp-toolkit:start" "$CFG/CLAUDE.md"'

echo "== installer refuses malformed settings.json"
CFG2="$T/cfg2"; mkdir -p "$CFG2"; echo '{"hooks": ' > "$CFG2/settings.json"; cp "$CFG2/settings.json" "$T/bad.orig"
check "malformed JSON: non-zero exit, nothing written" '! CLAUDE_CONFIG_DIR="$CFG2" "$KIT/install.sh" >/dev/null 2>&1 && cmp -s "$CFG2/settings.json" "$T/bad.orig" && [ ! -e "$CFG2/CLAUDE.md" ]'

echo "== installer --repo, Team Kit-style hooks dir"
R="$T/repo"; git init -q -b main "$R"; git -C "$R" config user.email t@example.com; git -C "$R" config user.name t
mkdir -p "$R/.githooks"; printf '#!/bin/bash\necho existing-check\nexit 0\n' > "$R/.githooks/pre-commit"; chmod +x "$R/.githooks/pre-commit"
git -C "$R" config core.hooksPath .githooks
check "repo install succeeds" '"$KIT/install.sh" --repo "$R" > "$T/run3.log"'
sed 's/^/      /' "$T/run3.log"
check "scan line inserted after shebang, existing hook kept" '[ "$(sed -n 2p "$R/.githooks/pre-commit")" = "\"\$(dirname \"\$0\")/secret-scan.sh\" || exit 1  # agent-jepp-toolkit" ] && grep -q existing-check "$R/.githooks/pre-commit"'
echo "hello" > "$R/a.txt"; git -C "$R" add a.txt
check "clean commit passes" 'git -C "$R" commit -qm clean >/dev/null 2>&1'
FAKE="sk-ant-$(printf 'x%.0s' $(seq 1 30))"   # built at run time; not a real key
echo "KEY=$FAKE" > "$R/b.txt"; git -C "$R" add b.txt
check "commit with a key-shaped string is refused" '! git -C "$R" commit -qm leak >/dev/null 2>&1'
git -C "$R" restore --staged b.txt; rm "$R/b.txt"
echo "X=1" > "$R/.env"; git -C "$R" add -f .env
check "commit staging .env is refused" '! git -C "$R" commit -qm env >/dev/null 2>&1'
git -C "$R" restore --staged .env
check "repo re-run changes nothing" '"$KIT/install.sh" --repo "$R" | grep -q "Nothing to change" && [ $(grep -c "# agent-jepp-toolkit" "$R/.githooks/pre-commit") -eq 1 ]'

mkdir -p "$R/sub"; echo "KEY=$FAKE" > "$R/sub/secret-scan.sh"; git -C "$R" add sub/secret-scan.sh
check "key in a file named secret-scan.sh is refused" '! git -C "$R" commit -qm leak2 >/dev/null 2>&1'
git -C "$R" restore --staged sub/secret-scan.sh; rm -r "$R/sub"
git -C "$R" add .githooks
check "the scanner itself commits cleanly" 'git -C "$R" commit -qm hooks >/dev/null 2>&1'

echo "== installer safety (2026-10-27 fixes)"
R2="$T/pyrepo"; git init -q -b main "$R2"
printf '#!/usr/bin/env python3\nimport sys\nsys.exit(0)\n' > "$R2/.git/hooks/pre-commit"; cp "$R2/.git/hooks/pre-commit" "$T/py.orig"
check "--repo refuses a Python pre-commit and leaves it unchanged" '! "$KIT/install.sh" --repo "$R2" >/dev/null 2>&1 && cmp -s "$R2/.git/hooks/pre-commit" "$T/py.orig"'
CFG3="$T/cfg3"; mkdir -p "$CFG3/skills" "$T/src/roundtable"; echo '{}' > "$CFG3/settings.json"
echo "SOURCE OF TRUTH" > "$T/src/roundtable/SKILL.md"; ln -s "$T/src/roundtable" "$CFG3/skills/roundtable"
check "refuses to write through a symlinked skill dir" '! CLAUDE_CONFIG_DIR="$CFG3" "$KIT/install.sh" >/dev/null 2>&1 && grep -q "SOURCE OF TRUTH" "$T/src/roundtable/SKILL.md" && [ ! -e "$CFG3/CLAUDE.md" ]'
rm "$CFG3/skills/roundtable"; echo "# mine" > "$T/src/CLAUDE.md"; ln -s "$T/src/CLAUDE.md" "$CFG3/CLAUDE.md"
check "refuses to replace a symlinked CLAUDE.md" '! CLAUDE_CONFIG_DIR="$CFG3" "$KIT/install.sh" >/dev/null 2>&1 && [ -L "$CFG3/CLAUDE.md" ] && [ "$(cat "$T/src/CLAUDE.md")" = "# mine" ]'
CFG4="$T/cfg4"; mkdir -p "$CFG4" "$T/fakebin"; echo ORIGINAL > "$CFG4/CLAUDE.md"; echo '{}' > "$CFG4/settings.json"
printf '#!/bin/sh\nprintf 20261027-120000\n' > "$T/fakebin/date"; chmod +x "$T/fakebin/date"
cp -R "$KIT" "$T/kit3"; PATH="$T/fakebin:$PATH" CLAUDE_CONFIG_DIR="$CFG4" "$T/kit3/install.sh" >/dev/null
echo "- second" >> "$T/kit3/user/CLAUDE.md"; PATH="$T/fakebin:$PATH" CLAUDE_CONFIG_DIR="$CFG4" "$T/kit3/install.sh" >/dev/null
check "two installs in the same second keep both backups" 'grep -qx ORIGINAL "$CFG4/backups/agent-jepp-toolkit-20261027-120000/files$CFG4/CLAUDE.md" && [ -d "$CFG4/backups/agent-jepp-toolkit-20261027-120000-2" ]'

echo "== coexistence with the real ~/.claude/settings.json (read-only, merged into a temp file)"
REAL="$HOME/.claude/settings.json"
if [ -f "$REAL" ]; then
  check "real settings merge keeps every hook and adds one" 'python3 "$KIT/lib/merge.py" settings "$REAL" x "$T/real.out" && python3 - "$REAL" "$T/real.out" <<PY
import json,sys
a=json.load(open(sys.argv[1])); b=json.load(open(sys.argv[2]))
cmds=lambda d:[h.get("command") for ev in d.get("hooks",{}).values() for e in ev for h in e.get("hooks",[])]
assert set(cmds(a)) <= set(cmds(b)); assert len(cmds(b)) in (len(cmds(a)), len(cmds(a))+1)
print("      real hooks:", len(cmds(a)), "after merge:", len(cmds(b)))
PY'
else echo "SKIP  no real settings.json"; fi

echo; [ $FAIL -eq 0 ] && echo "ALL PASS" || echo "SOME FAILED"
exit $FAIL
