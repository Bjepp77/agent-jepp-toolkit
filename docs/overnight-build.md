# Overnight build recipe (replaces forge)

Uses Team Kit's `/spec` and `/build-spec`, installed per repo from upstream. This kit does not ship them.

1. **Decide.** If the build is costly to get wrong, run the roundtable skill first. Its CEO rulings go into
   the spec's "Decisions already made", and its rejected options go into "Considered and rejected". Name
   the one invariant under "Constraints in this repo".
2. **Fill the repo's check commands.** `/build-spec` reads the typecheck, targeted-test and full-suite
   commands from the repo's CLAUDE.md. Empty placeholders stall an unattended run.
3. **Restore point.** Commit, then `git tag pre-<slug>`.
4. **Spec.** Run `/spec`. On a solo, single-user repo, answer "Access and release" with "N/A, single user".
5. **Approve.** Read the spec and punchlist. This is the only human gate, so read it properly.
6. **Build.** Run `/build-spec` and leave it. It commits each punchlist item locally and never pushes
   (git_guard blocks pushes anyway).
7. **Morning.** Read `.specs/<slug>/check.md` and any unchecked items. Run the full suite yourself.
8. **Roll back** if needed: run `git reset --hard pre-<slug>` yourself. Agents should not run it, and Team
   Kit's guard blocks it on a shared tree.
9. **Ship.** You push, or type `/push` for one run.

Never start a build with `--dangerously-skip-permissions` on a real repo.
