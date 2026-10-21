# Round Table: Agent-Jepp-Toolkit v1 (2026-10-21)

Run by Lead · Toolkit, following `~/MegaMind/Claude_Cowork/Skills/roundtable-skill/SKILL.md`.
Mode: **full** (the output is saved to a file and decides what ships).
Object: what each component of Brandon's agent setup becomes in a portable kit.
Inputs: Brandon's setup (MegaMind, `~/Downloads/BRANDON-SYSTEM-CONTEXT.md`, `~/Work`, `~/.claude/harness`), and
ai-foundry-byu/agent-team-kit at commit `c3ed7ad` (2026-10-20), "Team Kit" below.

## 1. Draft plan (abridged)

| # | Component | Draft proposal |
|---|---|---|
| 1 | Instructions file | User-level `~/.claude/CLAUDE.md`, under 60 lines, Brandon content, with the user-vs-repo split taken from Team Kit |
| 2 | Skills | Ship `roundtable` and `voice` |
| 3 | Build pipeline | Cut forge; use Team Kit `/spec` + `/build-spec` |
| 4 | Memory | Templates for reminders, postmortems, `agenda.py` |
| 5 | Git guards | User-level `git_guard.py` that blocks push, force-push, reset --hard, clean -f, add -A, and scans secrets on commit; plus repo pre-commit gate and `safe_commit.sh` |
| 6 | SOP jobs | Cut the `jobs/` concept |
| 7 | Voice | `voice-and-style.md` as an on-demand skill |

## 2. Panel (Sonnet subagents, run in parallel, each self-red-teamed)

- **Simplicity skeptic** (time cost for a student whose top goal is a PM job). Verdict: the plan is still design, not failure-driven. Ship 3 files: the CLAUDE.md template, `git_guard.py`, and roundtable. Cut voice (no logged runs), cut the reminder/agenda templates (copies drift from the live `~/Work` files), cut duplicated guards, and set a kill date. Red-team killed: cutting the CLAUDE.md template.
- **Harness security engineer** (a promise is not a control, blast radius, installer safety, licensing). Verdict: a regex on Bash text is a speed bump, not a boundary. Listed bypasses: `git -C x push`, `sh -c`, `eval`, aliases, env prefixes, scripts. Asked for shlex parsing, failing closed, and claims demoted. The real gates are remote credentials, branch protection, and CI secret scanning. One secrets scanner, not two. The installer must dedupe, write through a temp file, validate JSON, and back up first. Never vendor Team Kit; add a check for copied strings. Red-team killed: sandbox/container isolation (scope creep).
- **Solo-builder staff engineer** (daily build speed, overnight runs, coexistence). Verdict: cutting forge is right. Approve once with `/spec`, then let `/build-spec` run unattended. Add an overnight recipe with a restore-point tag. Map round-table output into the spec. Hold voice. `git_guard` double-fires with Team Kit's `bash-guard` and breaks worktrees, and a blanket push block breaks Team Kit `/push`. Red-team killed: writing an own spec skill, and defaulting to worktrees.

## 3. Round table

**Convergence (non-negotiable):**
- Cut forge, and reuse Team Kit `/spec` + `/build-spec` (all 3).
- Ship roundtable. Hold voice until it has logged runs (all 3).
- Cut `jobs/` (all 3).
- `git_guard.py` is the one hook worth shipping, because it still fires in bypassPermissions mode (all 3).
- Do not vendor Team Kit; it has no license (security, staff).

**Conflicts:**
- A. Installer weight. The skeptic wants about 20 lines with no flags. Security wants dedupe, temp-file writes, `--dry-run`, and `--uninstall`.
- B. Guard scope. The plan blocked local destructive git too. The skeptic and the staff engineer say that duplicates Team Kit's `bash-guard` and clashes in worktrees.
- C. Secrets scan. Security wants it as a git pre-commit hook. The staff engineer says a repo gate collides with Team Kit's `core.hooksPath .githooks`.
- D. Memory. The skeptic says document the pattern only. The staff engineer says ship the postmortems template only.
- E. A `kickoff.sh` script (staff engineer) vs nothing that has not failed yet (skeptic).
- F. A separate repo (owner requirement) vs a folder in `~/Work` (skeptic).

**Collapse check:** the skeptic and the staff engineer overlapped on cutting voice and the repo extras. They came at it from different incentives (time vs build speed), so the overlap is real agreement, not a duplicated lens. Weighted normally.

## 4. Diligence (checked against primary sources)

- Team Kit license: no LICENSE file, and no license text in the README or file headers (`git ls-files`, grep). Verified. Result: no Team Kit file or text is copied. Ideas only, credited.
- Roundtable has earned its place: `roundtable-loop-log.md` has 21 dated entries. Voice: no loop log and no session-log hits for ghost-drafting. Verified, so voice is held.
- Forge evidence: `forge-loop-log.md` says stages 4-5 "don't apply" to a doc deliverable, and the previous RUN-SHEET status is "unknown". Verified.
- Team Kit `bash-guard.mjs` already blocks `git add -A`, `commit -a`, `reset --hard`, `clean -f`, `stash`, `checkout .` and force-push. It relaxes the first six in linked worktrees (`:40-69`, `:205-212`). It does NOT block a plain `git push`. Verified. So the only gap is a plain push.
- Team Kit `skills/push/SKILL.md:3`: invoking `/push` "is the user's explicit push authorization for this one run". Verified. A blanket block would break it.
- Harness: no harness role card tells agents to push. Verified with a grep of `~/.claude/harness`.
- `~/.claude/settings.json` holds Evan's 15 hook entries and no permission rules. Verified. The merge must preserve them.
- Claim cut: "works in every repo regardless of core.hooksPath". True only for the PreToolUse layer. Removed.
- Not verified: whether `permissions.deny` applies in bypassPermissions mode. The kit does not rely on it.

## 5. CEO call

1. **Instructions file: MERGE.** Brandon's content, with Team Kit's user-vs-repo split. The template is under 50 lines, and a test fails it past 60. It covers output format, sparring partner, trust rules, verify-before-handover, and a 5-line placement tree. It says outright that CLAUDE.md is advice and hooks are the controls. No health, faith, persona, or palette.
2. **Skills: BRANDON's roundtable only.** It is de-vaulted: the loop log goes to the project's `docs/` or to `~/Work`. Voice is held. Other skills stay in MegaMind and move on touch.
3. **Build pipeline: TEAM KIT.** Forge is retired. Its useful parts move elsewhere: roundtable before `/spec` when stakes are high, one named invariant, and a restore-point tag before `/build-spec`. They live in the roundtable skill and in `docs/overnight-build.md`. Ruling on E: a doc, not a `kickoff.sh`. A script is code to maintain before it has failed once.
4. **Memory: CUT from the kit, except one empty template.** Ruling on D: ship `templates/postmortems.md`, an empty format with no real rows. The README documents the reminders pattern in a few lines. `_reminders.md` and `agenda.py` stay live in `~/Work` only, so no copy can drift.
5. **Git guards: MERGE, narrowed.** Ruling on B: `git_guard.py` blocks only the tier where damage leaves the laptop, which is `git push` (force or not). Local destructive git stays with Team Kit per repo, so nothing double-fires and worktrees are untouched. It parses with shlex, sees through `git -C/-c`, env prefixes, `command`, absolute paths, `sh -c` / `bash -c` / `eval`, and git aliases. It allows `--dry-run`, and it allows a push when the latest real user prompt is `/push`, `/stage`, or `/promote` (Team Kit's authorization model). It fails closed only when it cannot parse a command that mentions push. The README calls it a speed bump and names its holes. Ruling on C: one scanner, Brandon's `~/Work/hooks/pre-commit` generalized to `repo/secret-scan.sh`. `install.sh --repo` chains it into whatever hooks directory the repo already uses, inserted after the shebang so an `exit 0` at the end of Team Kit's hook cannot skip it. `safe_commit.sh`: cut, because Team Kit's explicit-path commits cover it.
6. **SOP jobs: CUT.** A repeated job becomes a skill when touched.
7. **Voice: CUT for v1, held.** It stays in MegaMind until ghost-drafting has 2-3 logged runs.
- Ruling on A: re-run safety is a stated requirement, so keep the marker block, the dedupe-by-command JSON merge, the temp-file write, the backup first, and `--dry-run`. Cut `--uninstall`: the backup directory plus a printed restore command covers it.
- Ruling on F: a separate repo, because the owner asked for it. Skeptic overruled.
- Unanimity challenged: everyone wanted the push block. The challenge was whether it breaks real flows. It did break Team Kit `/push`, which is why the slash-command allowance exists.
- Added: a kill/review date of 2027-01-19 (the same day-90 date as the MegaMind freeze review), and a test that greps the kit for Team Kit identifiers.

## 6. Closeout

| Panel item | Status |
|---|---|
| Skeptic: 3-file core | Addressed. Core is CLAUDE.md block, git_guard, roundtable; the rest is docs, the empty template, and the opt-in scanner |
| Skeptic: cut voice, reminder templates, duplicate guards | Addressed |
| Skeptic: 20-line installer, no flags | Rejected. Re-run safety and backups are owner requirements |
| Skeptic: kill date | Addressed (2027-01-19) |
| Skeptic: folder in ~/Work | Rejected. Owner asked for its own repo |
| Security: shlex parsing, bypass list, fail closed | Addressed, with the remaining holes documented |
| Security: demote "blocks" claims | Addressed in the README |
| Security: one scanner | Addressed |
| Security: dedupe, temp-file write, validate, backup | Addressed |
| Security: `--uninstall` | Rejected. Backup plus restore command |
| Security: deny rule as second layer | Rejected for now. It would also block Team Kit `/push`, and its bypass-mode behavior is unverified |
| Security: Team Kit string check | Addressed in `tests/run.sh` |
| Security: CI gitleaks as the real gate | Documented as a recommendation, not built (no remote yet) |
| Staff: overnight recipe, restore tag | Addressed (`docs/overnight-build.md`) |
| Staff: roundtable-to-spec mapping | Addressed (in the roundtable skill) |
| Staff: double-fire and worktree clash | Addressed by narrowing to push |
| Staff: `/push` breakage | Addressed by the slash-command allowance |
| Staff: `kickoff.sh` | Rejected. It became a doc |

**Lift:** 14 of about 20 panel items changed the deliverable. The biggest was narrowing git_guard to push only, plus the `/push` allowance. Without it the kit would have double-fired with Team Kit and broken its release skill.

**Human gap:** a real person in these seats would bring things a model can't: the Team Kit author's intent on licensing, and how Evan (author of the harness) expects pushes to flow. People to pressure-test with: the Team Kit maintainer at the BYU AI Foundry (ask for a license, or permission to vendor), and Evan (whether harness workers ever need to push). Only Brandon can judge whether 3 components are too few to be worth installing.

**Loop log:** the skill says to append to `MegaMind/Claude_Cowork/memory/loop-logs/roundtable-loop-log.md`. MegaMind is frozen for this job, so the entry lives here instead:
`2026-10-21 | Agent-Jepp-Toolkit v1 component calls | full | skeptic, security engineer, solo-builder staff engineer | lift 14/~20, biggest: git_guard narrowed to push plus /push allowance`.
