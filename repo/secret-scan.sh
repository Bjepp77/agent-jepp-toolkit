#!/bin/bash
# secret-scan.sh (agent-jepp-toolkit): refuses a commit that stages a secret.
# Source: Brandon Jeppson's ~/Work/hooks/pre-commit (2026-10-21), generalized to run from any
# hooks directory. install.sh --repo chains it into the repo's existing pre-commit.
#
# Called from pre-commit as: "$(dirname "$0")/secret-scan.sh" || exit 1
# Blocks: .env files (but .env.example / .env.sample are fine), private keys,
# and common API key shapes. Looks only at lines being ADDED by this commit.
#
# Escape hatch: `git commit --no-verify` skips this. Use it only for a false
# positive you have read, and say so in the commit message.
#
# The patterns are in this file, so this file contains the pattern text but no
# real key. Never paste a real key into a test.

set -u
ROOT=$(git rev-parse --show-toplevel) || exit 1
cd "$ROOT" || exit 1

FAIL=0
bad() { echo "  BLOCKED: $1"; FAIL=1; }

# 1. File names. Added, copied, modified or renamed files only.
while IFS= read -r f; do
  base=$(basename "$f")
  case "$base" in
    .env.example|.env.sample|.env.template) ;;
    .env|.env.*|*.env) bad "$f is an env file. Put it in .gitignore." ;;
    id_rsa|id_ed25519|id_ecdsa|id_dsa|*.pem|*.p12|*.pfx|*.key) bad "$f looks like a private key file." ;;
  esac
done < <(git diff --cached --name-only --diff-filter=ACMR)

# 2. Content. Only added lines, skipping this scanner's own file.
PATTERNS=(
  'sk-ant-[A-Za-z0-9_-]{20,}'                        # Anthropic
  'sk-(proj-|live-|svcacct-)?[A-Za-z0-9_-]{32,}'     # OpenAI and similar
  'gh[pousr]_[A-Za-z0-9]{30,}'                       # GitHub tokens
  'github_pat_[A-Za-z0-9_]{40,}'                     # GitHub fine-grained
  'AKIA[0-9A-Z]{16}'                                 # AWS access key id
  'xox[abprs]-[A-Za-z0-9-]{10,}'                     # Slack
  'AIza[0-9A-Za-z_-]{35}'                            # Google API key
  'sk_live_[A-Za-z0-9]{20,}'                         # Stripe live
  'eyJ[A-Za-z0-9_-]{15,}\.eyJ[A-Za-z0-9_-]{15,}\.[A-Za-z0-9_-]{10,}'  # JWT, incl. Supabase service-role
  '-----BEGIN ([A-Z]+ )?PRIVATE KEY-----'            # PEM private key
  '(SERVICE_ROLE|SECRET|PASSWORD|API_KEY|TOKEN)[A-Z_]*[[:space:]]*[=:][[:space:]]*["'\'']?[A-Za-z0-9/+_.-]{24,}'  # NAME=longvalue
)

# No path is excluded: none of the PATTERNS matches its own text, so this file can be committed.
ADDED=$(git diff --cached -U0 --no-color --diff-filter=ACMR | grep -E '^\+' | grep -vE '^\+\+\+ ')
for p in "${PATTERNS[@]}"; do
  if hit=$(printf '%s\n' "$ADDED" | grep -E -m1 -- "$p"); then
    # Never echo the matched text. Say which rule fired.
    bad "a staged line matches secret pattern: $p"
  fi
done

if [ "$FAIL" -ne 0 ]; then
  echo ""
  echo "COMMIT REFUSED: remove the secret from the staged files (git restore --staged <file>)."
  echo "Real keys belong in an untracked .env. If a key was ever committed, rotate it."
  exit 1
fi
exit 0
