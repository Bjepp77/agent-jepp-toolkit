# Agent Team Kit: what was stolen, what was rejected

Source: https://github.com/ai-foundry-byu/agent-team-kit at commit `c3ed7ad` (2026-10-20), read-only.
**License: none found** (no LICENSE file, no license text in README or headers). So "stolen" here means
the *idea* was adopted and re-written from scratch in this kit's own words and code, with credit. No Team
Kit file, regex, or paragraph is copied. `tests/run.sh` greps for Team Kit identifiers to keep it that way.
Team Kit itself is still installed per repo from upstream, as Brandon already decided.

## Stolen (idea adopted, fresh implementation)

| Idea | Team Kit source | Where it lives here | Why |
|---|---|---|---|
| User-level vs repo-level split of instructions | `snippets/CLAUDE-md-*.md`, `install.sh` | `user/CLAUDE.md` holds only cross-repo rules; repo rules stay with Team Kit | Matches Brandon's placement tree; keeps personal content out of client repos |
| "Commit freely, never push" enforced at the tool layer | `hooks/scripts/bash-guard.mjs` (force-push block), `memory-pack/commit-freely-never-push.md` | `user/hooks/git_guard.py` | A promise is not a control; the hook still fires in bypassPermissions mode |
| A slash command as a one-run push authorization | `skills/push/SKILL.md` | `git_guard.py` allows push when the latest real prompt is `/push`, `/stage`, or `/promote` | Keeps Team Kit's release flow working under the push block |
| Approve the spec, then build unattended | `skills/spec`, `skills/build-spec` | `docs/overnight-build.md` (uses Team Kit's skills, does not copy them) | Replaces forge's full-auto launch with a human gate before autonomy |
| Guarded, additive installer that is safe to re-run | `install.sh` (grep-guarded appends, skip-if-exists) | `install.sh` (marker block, JSON merge with dedupe) | Improved: Team Kit's installer has no backups and overwrites; this one backs up first |
| Memory file format: frontmatter + Why / How to apply + one-line index | `memory-pack/README.md` | Referenced in `user/CLAUDE.md` placement tree | Already the format of `~/Work/.claude/team-memory`; no new files needed |

## Rejected (and why)

| Team Kit piece | Why rejected |
|---|---|
| Local destructive git blocks (`add -A`, `reset --hard`, `clean -f`, `stash`, `checkout .`) as a user-level copy | Team Kit already ships them per repo, with a worktree relaxation. A second copy double-fires and breaks worktrees |
| `dev-port.mjs`, schema lock, `agent-coord.mjs`, `session-release.mjs`, anti-sweep ledger | Concurrency machinery for many agents on one tree. Solo default is stay-on-main |
| Supabase/pnpm hardcoding (`SCHEMA_RE`, psql DDL block, `post-merge` migrations notice, `pre-push` pnpm checks) | App-stack specific; lives with Team Kit in each repo where it applies |
| Release pipeline (`/push`, `/stage`, `/promote`, `/remove-flag`, release-flags and access-model snippets, staging twin) | Multi-environment ops; used from Team Kit directly when a repo needs it |
| App QA skills (`/fix-bug`, `/userflow-map`, `/ux-critique`, crawlers, impersonation) | Need an app-integrated bug DB and flows; not personal-kit material |
| `memory-pack/` content (30 memories) | No license, and Brandon's own team memory already holds his rules |
| `team-memory.mjs` + `/share-memory` | Evan's harness already installs an equivalent team-memory hook; a duplicate would race it |
| `worktree-commands.sh` (`wt`, `cockpit`) | Bakes in `--dangerously-skip-permissions --remote-control`; worktrees only when needed |
| `hub/` hub-and-spokes | Parked idea in Brandon's context ("A ~/hub knowledge hub" is on the do-not-build list) |
| `file-size-nudge.mjs`, `arch-check.mjs`, import boundaries | Useful per repo, comes with Team Kit; not a user-level concern |
| `/mockup` + `.mockups/` | Good idea, but Brandon has not repeated it 2-3 times yet; revisit when he does |

## Brandon's own pieces rejected for v1

| Piece | Why |
|---|---|
| forge | Retired by the round table: full-auto on the real repo, stages 4-5 not applying, RUN-SHEET results "unknown" |
| voice skill | No logged runs yet; held until 2-3 |
| jobs/ SOPs | Skills are the native mechanism; convert on touch |
| `_reminders.md`, `agenda.py` | Live in `~/Work`; a kit copy would drift (postmortem #2) |
| `safe_commit.sh` | Team Kit's explicit-path commits cover it in repos; stays in `~/Work` |
| health, faith, TARS persona, palette | Must not reach client and Foundry repos via `~/.claude/CLAUDE.md` |
