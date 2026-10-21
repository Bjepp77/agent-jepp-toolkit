# Agent-Jepp-Toolkit

Brandon Jeppson's personal layer for working with Claude Code agents. It is small on purpose. It holds only
what the 2026-10-21 round table kept, and anything else gets added after it fails in real use.

It sits between two things it does not replace:
- **Agent Team Kit** (https://github.com/ai-foundry-byu/agent-team-kit): per-repo guards, `/spec`, `/build-spec`,
  `/push`. It is installed in each repo from upstream.
- **Evan's agent harness** (Manager, leads and workers in `~/.claude/harness`). The installer merges into its
  `settings.json` and never replaces it.

## What's in it

| Path | Installs to | What it does |
|---|---|---|
| `user/CLAUDE.md` | `~/.claude/CLAUDE.md` (marked block) | Cross-repo working rules, 38 lines. Advice only: hooks and CI are the controls |
| `user/skills/roundtable/` | `~/.claude/skills/roundtable/` | Personas, diligence, CEO call, execute, loop log |
| `user/hooks/git_guard.py` | `~/.claude/hooks/` + `settings.json` | Stops an agent's `git push` unless the latest real prompt is `/push`, `/stage` or `/promote` |
| `repo/secret-scan.sh` | `<repo hooks dir>/` (only with `--repo`) | Refuses commits that stage `.env` files, private keys or key-shaped strings |
| `docs/overnight-build.md` | (read it) | Spec, approve, then build unattended. Replaces forge |
| `templates/postmortems.md` | (copy by hand) | Empty failure-to-fix ledger format |
| `docs/roundtable-2026-10-21.md` | | Why each component won, merged, or was cut |
| `docs/steal-reject.md` | | What was taken from Team Kit and what was rejected |

### What the guards do NOT do
`git_guard.py` is a speed bump for an agent that is trying to comply. It is not a boundary. It sees through
`git -C`, `-c`, env prefixes, `sh -c`, `eval`, absolute paths and git aliases. It does not catch a script file
that pushes, a python/node subprocess, `gh`, `curl` to a forge API, or a "push" built at run time.
`secret-scan.sh` is skipped by `git commit --no-verify`, and its patterns miss base64, split strings and short
passwords. The real gates are a remote credential without push rights, branch protection, and a CI secret
scan such as gitleaks. Add them when a repo gets a remote.

## Install

Requires bash, git and python3.

```bash
./install.sh --dry-run
```

```bash
./install.sh
```

Then, in each repo that already has Team Kit installed:

```bash
./install.sh --repo ~/Code/<project>
```

- **Backs up first.** Every file it is about to change is copied to `~/.claude/backups/agent-jepp-toolkit-<timestamp>/`.
  A `RESTORE.txt` there undoes the run: `bash <that dir>/RESTORE.txt`.
- **Safe to re-run.** Unchanged files are skipped. The CLAUDE.md block is replaced in place, between
  `agent-jepp-toolkit` markers. Your own text outside the block is never touched. The settings hook is added
  once, and every existing hook is kept.
- **Refuses** to write anything if `settings.json` is not valid JSON.
- Honors `CLAUDE_CONFIG_DIR`. Never pushes, never edits git config, never installs Team Kit.

## Test

```bash
bash tests/run.sh
```

It runs 22 checks in throwaway dirs only: guard cases, first install, re-run, kit update, restore, malformed
JSON, repo install with a fake key, and a read-only merge of the real `~/.claude/settings.json` into a temp file.

## Not in v1 (on purpose)
forge, the jobs/ SOPs, the voice skill, the reminders ledger and `agenda.py` (these live in `~/Work`), and
`safe_commit.sh`. Reasons are in `docs/steal-reject.md`. To add something new, write the failure in a
postmortem first.

## Provenance and license
- Brandon's own work: `user/CLAUDE.md` (from MegaMind `Claude_Cowork/CLAUDE.md`, `ground-rules.md` and
  `BRANDON-SYSTEM-CONTEXT.md`), the roundtable skill (from MegaMind `Skills/roundtable-skill`), and
  `secret-scan.sh` (from `~/Work/hooks/pre-commit`).
- **Agent Team Kit** (ai-foundry-byu, commit `c3ed7ad`) has **no license**, so default copyright applies. No
  Team Kit file, code or text is copied here. Ideas taken from it (the user-vs-repo split, the push guard,
  `/push` as authorization, the approve-then-build flow, guarded installs) were re-written from scratch and
  are credited in `docs/steal-reject.md`. `tests/run.sh` fails if Team Kit identifiers show up in shipped files.
- This repo has no license of its own yet (private).

Review date: 2027-01-19.
