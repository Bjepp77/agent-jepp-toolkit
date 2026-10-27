#!/bin/bash
# install.sh: install agent-jepp-toolkit into a Claude config dir, and optionally a repo.
#
#   ./install.sh [--dry-run] [--repo PATH]
#
# User level (always), into ${CLAUDE_CONFIG_DIR:-~/.claude}:
#   CLAUDE.md                  managed block between agent-jepp-toolkit markers (rest untouched)
#   skills/roundtable/SKILL.md
#   hooks/git_guard.py         + one PreToolUse(Bash) entry merged into settings.json
# Repo level (only with --repo):
#   <hooks dir>/secret-scan.sh + one line inserted near the top of <hooks dir>/pre-commit
#   (hooks dir = core.hooksPath if set, e.g. Team Kit's .githooks, else .git/hooks)
#
# Safe to re-run: unchanged files are skipped. Every file that changes is backed up first to
# <config>/backups/agent-jepp-toolkit-<timestamp>/, with a RESTORE.txt. Never pushes, never
# edits git config, never installs Team Kit.
set -euo pipefail

KIT="$(cd "$(dirname "$0")" && pwd)"
CONFIG="${CLAUDE_CONFIG_DIR:-$HOME/.claude}"
DRY=0
REPO=""
while [ $# -gt 0 ]; do
  case "$1" in
    --dry-run) DRY=1 ;;
    --repo) REPO="${2:?--repo needs a path}"; shift ;;
    -h|--help) sed -n '2,17p' "$0"; exit 0 ;;
    *) echo "unknown option: $1" >&2; exit 1 ;;
  esac
  shift
done

command -v python3 >/dev/null || { echo "python3 is required" >&2; exit 1; }
HOOK_CMD='python3 "${CLAUDE_CONFIG_DIR:-$HOME/.claude}/hooks/git_guard.py"'
TMP="$(mktemp -d)"; trap 'rm -rf "$TMP"' EXIT
BK=""; CHANGED=0
PLAN=()   # "tmpfile|dest|mode"

# ---------- compute phase: nothing is written outside $TMP ----------
stage() {  # stage <new-content-file> <dest> <mode>
  if [ -f "$2" ] && cmp -s "$1" "$2"; then echo "  same     $2"; return; fi
  if [ -f "$2" ]; then echo "  update   $2"; else echo "  create   $2"; fi
  PLAN+=("$1|$2|$3")
}

echo "agent-jepp-toolkit -> $CONFIG$([ $DRY = 1 ] && echo '  (dry run)')"
n=0; next() { n=$((n+1)); f="$TMP/f$n"; }   # sets $f (no subshell, so n advances)

next; python3 "$KIT/lib/merge.py" claude-md "$CONFIG/CLAUDE.md" "$KIT/user/CLAUDE.md" "$f"
stage "$f" "$CONFIG/CLAUDE.md" 644
next; cp "$KIT/user/skills/roundtable/SKILL.md" "$f"
stage "$f" "$CONFIG/skills/roundtable/SKILL.md" 644
next; cp "$KIT/user/hooks/git_guard.py" "$f"
stage "$f" "$CONFIG/hooks/git_guard.py" 755
next; python3 "$KIT/lib/merge.py" settings "$CONFIG/settings.json" "$HOOK_CMD" "$f"
stage "$f" "$CONFIG/settings.json" 644

if [ -n "$REPO" ]; then
  REPO="$(cd "$REPO" && pwd)"
  git -C "$REPO" rev-parse --git-dir >/dev/null 2>&1 || { echo "$REPO is not a git repo" >&2; exit 1; }
  HP="$(git -C "$REPO" config core.hooksPath || true)"
  if [ -n "$HP" ]; then
    case "$HP" in /*) HD="$HP" ;; "~"*) HD="$HOME${HP#\~}" ;; *) HD="$REPO/$HP" ;; esac
  else
    HD="$(cd "$REPO" && cd "$(git rev-parse --git-path hooks)" 2>/dev/null && pwd || echo "$REPO/.git/hooks")"
  fi
  echo "repo $REPO (hooks dir: $HD)"
  next; cp "$KIT/repo/secret-scan.sh" "$f"
  stage "$f" "$HD/secret-scan.sh" 755
  LINE='"$(dirname "$0")/secret-scan.sh" || exit 1  # agent-jepp-toolkit'
  next
  if [ ! -f "$HD/pre-commit" ]; then
    printf '#!/bin/bash\n%s\n' "$LINE" > "$f"
  elif grep -qF '# agent-jepp-toolkit' "$HD/pre-commit"; then
    cp "$HD/pre-commit" "$f"
  elif head -1 "$HD/pre-commit" | grep -q '^#!'; then
    if ! head -1 "$HD/pre-commit" | grep -qE '^#!.*[/ ](ba|z|da|k)?sh([[:space:]]|$)'; then
      echo "refusing: $HD/pre-commit is not a shell script ($(head -1 "$HD/pre-commit")). Chain $HD/secret-scan.sh from it by hand." >&2
      exit 1
    fi
    # insert right after the shebang so an "exit 0" at the end cannot skip it
    { head -1 "$HD/pre-commit"; echo "$LINE"; tail -n +2 "$HD/pre-commit"; } > "$f"
  else
    { echo "$LINE"; cat "$HD/pre-commit"; } > "$f"
  fi
  stage "$f" "$HD/pre-commit" 755
fi

# ---------- apply phase ----------
if [ ${#PLAN[@]} -eq 0 ]; then echo "Nothing to change. Already installed."; exit 0; fi
# never write through a symlink: it would overwrite the link's source or break the link
for item in "${PLAN[@]}"; do
  IFS='|' read -r src dest mode <<<"$item"
  case "$dest" in "$CONFIG"/*) root="$CONFIG" ;; *) root="$HD" ;; esac
  p="$dest"
  while [ "$p" != "$root" ] && [ "$p" != "/" ] && [ "$p" != "." ]; do
    if [ -L "$p" ]; then
      echo "refusing: $p is a symlink, so installing would write through it. Update its source by hand, or replace the link, then re-run. Nothing was written." >&2
      exit 1
    fi
    p="$(dirname "$p")"
  done
done
if [ "$DRY" = 1 ]; then echo "Dry run: ${#PLAN[@]} file(s) would change. Nothing written."; exit 0; fi

BK="$CONFIG/backups/agent-jepp-toolkit-$(date +%Y%m%d-%H%M%S)"
# mkdir without -p fails if the dir exists, so a second install in the same second gets
# its own dir instead of overwriting the first one's rollback copy
mkdir -p "$CONFIG/backups"; base="$BK"; n=1
until mkdir "$BK" 2>/dev/null; do
  n=$((n+1)); BK="$base-$n"
  [ "$n" -gt 99 ] && { echo "cannot create a backup dir under $CONFIG/backups" >&2; exit 1; }
done
: > "$BK/RESTORE.txt"
for item in "${PLAN[@]}"; do
  IFS='|' read -r src dest mode <<<"$item"
  if [ -f "$dest" ]; then
    b="$BK/files$(dirname "$dest")"; mkdir -p "$b"; cp -p "$dest" "$b/"
    printf 'cp -p %q %q\n' "$b/$(basename "$dest")" "$dest" >> "$BK/RESTORE.txt"
  else
    printf 'rm -f %q\n' "$dest" >> "$BK/RESTORE.txt"
  fi
  mkdir -p "$(dirname "$dest")"
  cp "$src" "$dest.agent-jepp-tmp" && chmod "$mode" "$dest.agent-jepp-tmp" && mv "$dest.agent-jepp-tmp" "$dest"
  CHANGED=$((CHANGED+1))
done
python3 -c 'import json,sys; json.load(open(sys.argv[1]))' "$CONFIG/settings.json"
echo "Done: $CHANGED file(s) changed."
echo "Backup and undo: $BK  (run: bash $BK/RESTORE.txt)"
[ -n "$REPO" ] || echo "Per-repo guards: install Team Kit from upstream (https://github.com/ai-foundry-byu/agent-team-kit), then re-run with --repo <path> for the secrets scan."
