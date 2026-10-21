# Changelog

## 0.1.0 (2026-10-21)
First version, scoped by the round table in `docs/roundtable-2026-10-21.md`.
- `user/CLAUDE.md`: user-level working rules, 38 lines. Covers output, sparring, trust rules, verify before handover, and where things go.
- `user/skills/roundtable`: Brandon's Round Table skill, ported out of MegaMind. The loop log no longer depends on the vault. Adds a "Feeding a build" section.
- `user/hooks/git_guard.py`: PreToolUse(Bash) speed bump against agent `git push`. Allows `/push`, `/stage` and `/promote` for one run.
- `repo/secret-scan.sh`: Brandon's `~/Work` secrets gate, generalized to chain into any repo's pre-commit.
- `install.sh`: backs up first, safe to re-run, has `--dry-run` and `--repo`, and supports `CLAUDE_CONFIG_DIR`.
- `tests/run.sh`: 22 checks, run only in throwaway dirs.
- Retired: forge, the jobs/ SOPs, and the voice skill (held). See `docs/steal-reject.md`.
- Review date: 2027-01-19. Archive the repo if nothing in it has been used by then.
