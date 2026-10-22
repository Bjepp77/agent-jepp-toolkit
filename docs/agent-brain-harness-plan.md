# agent-brain-harness: study and plan

Study date 2026-10-21. Source: https://github.com/NaluKicks-808/agent-brain-harness at `f6c121a`
(2026-10-21 16:35, author `agent-harness <evannalu@byu.edu>`). Read-only clone in scratch. Nothing installed.
**License: MIT.** Code may be copied if the MIT notice travels with it (unlike Team Kit, which has none).

## What it is (5 lines)
1. Evan's public, portable package of the same harness we run: Manager, leads, workers, reviewer, role cards.
2. Plus his second-brain-kit: a git `wiki/`, one agenda `_reminders.md`, postmortems, and gate scripts.
3. Agents talk through a file bus in `<project>/.harness/` (inbox, jobs, handoffs, reports) via a `harness` CLI.
4. Gates: brain pre-commit (lint + connect), repo pre-push (tests + leak scan), eval gate for prompt files.
5. Stdlib Python 3.8, any LLM app (Claude Code, Codex, Gemini, chat paste). 238 tests pass locally.

**Key finding.** Our `~/.claude/harness` is already a fork of this. 8 of 13 hooks are byte-identical to
`~/.claude/hooks`. The rest have drifted both ways. So this is not a new system to bolt on. It is the
upstream we forked from. The job is: pick an upstream, port the drift, and add the parts we lack.

## Parts vs ours

| Their part | Ours today | Call | Why |
|---|---|---|---|
| Hooks: archive_guard, caveman_manager_subagents, codex_model_floor, context_nudge, manager_msg_cap, paused_lead_guard, rule_change_notice, send_guard_test | `~/.claude/hooks`, identical | Already have | Same bytes |
| `reply_check.py` voice check + `voice_nudge.py` | Ours lacks voice check (theirs newer) | **Adopt** | Saves voice corrections for the next prompt instead of a double answer |
| `role_card.py` | Ours newer: late-title retry (today 17:08) | **Conflict, keep ours** | Ours fixes a real bug. Offer it upstream to Evan |
| `send_guard.py`, `secret_guard.py` | Same logic; theirs has wording scrubs, ours has a 10-16 false-hold fix | Keep ours | Theirs is anonymized text, not new logic. Ours has one more fix |
| `git_guard`, `direct_request_intake`, `lead_clear_guard`, `team-memory.mjs`, `send_log.py` | Ours only | Already have | Brandon-local controls. Keep |
| manager-console plugin (v0.2.0, +150 lines register.tsx, +120 lib.ts, tests) | Ours 0.1.10 (board v2) | **Adopt after diff** | Theirs is newer. Needs a line diff and their tests run before swap |
| Role cards manager/lead/worker | `~/.claude/harness/*.md`, longer, Brandon rules | Keep ours | Ours carry owner rules (budget, no Fable, models). Theirs are the generic base |
| `reviewer.md` + lead "verify before done" (PASS/FAIL/UNVERIFIED by a fresh session) | Not a role. CLAUDE.md "Done needs evidence" is prose only | **Adopt** | Turns a prose rule into a step. Highest value item |
| `eval-gate.md` + `core/eval/eval_gate.py` | None. Role cards were edited 3 times today with `.bak` as the only safety | **Adopt (later)** | Golden cases for role cards and hooks prompts. Gate goes red on an unevaluated edit |
| `.harness/` file bus + `harness.py` launch/spawn/send/inbox | Native SendMessage + desktop sessions + board v2 + `~/.claude/harness/inbox` | **Conflict, skip** | Two message buses would split the truth. Desktop app sessions are our runtime |
| `harness doctor` | None | **Adopt idea** | Port as a toolkit `doctor` for our layout (hooks wired, cards present, Work gates on) |
| Pre-push gate + `scripts/leak_scan.py` | Team Kit pre-push per repo; toolkit `repo/secret-scan.sh` pre-commit | Adopt for non-Team-Kit repos only | Team Kit repos already have one. Two pre-push hooks would fight |
| Brain `_reminders.md`, `agenda.py`, `safe_commit.sh`, `_postmortems.md` | `~/Work` has trimmed copies (second-brain-kit merge today) | Already have | Diff `agenda.py`/`safe_commit.sh` and take bug fixes only |
| `expire_rows.py`, `ledger_merge.py` (+ `.gitattributes` merge driver) | None. `sweep.py` exists | **Adopt** | Ledger is multi-writer. Merge driver ends row-insert conflicts. Expiry kills stale rows |
| `lint.py`, `connect.py`, `find.py`, `deepfind.py`, `quote_check.py`, `critic.py` | `~/Work` has no wiki by choice; MegaMind is the knowledge vault | Skip now | Gates for a wiki we do not keep in `~/Work`. Revisit if MegaMind adopts them |
| `wtfhappened` postmortem skill | Postmortem format only, no skill | **Adopt** | Repeat-check plus "install a mechanical fix" is the loop we want |
| `brain_quiz.py`, `guess_words.py`, `event_twin.py` | None | Skip | Calls a model (spend) or niche |
| Installer, launchers, PATH/zshrc edits, `~/agent-brain` | toolkit `install.sh` | **Skip, never run** | Would create a second brain folder and a second `harness` command |
| Codex/Gemini/VS Code/chat adapters | Codex via `codex_model_floor` | Skip | Desktop sessions cover us |

## Unified target

- **Upstream:** agent-brain-harness, pinned by commit, cloned read-only at `~/Code/agent-brain-harness`.
- **Overlay:** agent-jepp-toolkit holds only Brandon-local deltas (role_card fix, git_guard, intake,
  clear guard, owner rules in cards) plus a `VENDORED.md` listing each upstream file taken, its commit and
  the MIT notice.
- **Runtime:** `~/.claude/harness` + `~/.claude/hooks` + manager-console. Native messaging and board v2 stay
  the bus. No `.harness/` folder.
- **Records:** `~/Work` stays the ledger and tray. Gains ledger merge driver and expiry. MegaMind stays
  the knowledge vault.
- **Quality loop:** worker does, reviewer checks (fresh session), lead reports with `Reviewed by:`,
  failure goes to `wtfhappened` and a mechanical fix, prompt edits pass the eval gate.

## Migration (in order; each step rolls back alone)

| # | Step | Rollback | Size |
|---|---|---|---|
| 0 | Clone upstream to `~/Code/agent-brain-harness`, pin `f6c121a`. Add `docs/VENDORED.md` with the MIT text | Trash the clone, revert the doc commit | 0.25 h |
| 1 | Reviewer role: copy `reviewer.md`, add the verify step to our `lead.md`. Leads end reports with `Reviewed by: <model>, <verdict>` | Restore `lead.md.bak-<stamp>`, delete `reviewer.md` | 1 h |
| 2 | `reply_check.py` voice check + `voice_nudge.py`; wire `voice_nudge` on UserPromptSubmit | Restore `.bak`, remove the one settings entry | 1 h |
| 3 | `expire_rows.py`, `ledger_merge.py`, `.gitattributes` + `git config merge.ledger-rows.driver` in `~/Work`. Run their tests first | `git revert` in `~/Work`, `git config --unset` the driver | 1 h |
| 4 | `wtfhappened` skill into `~/.claude/skills/`, pointed at `~/Work/wiki/_postmortems.md` | Delete the skill folder | 0.5 h |
| 5 | manager-console 0.2.0: line diff vs our 0.1.10, run their test suite, install as new version | Plugin cache keeps 0.1.10; pin back | 2 h |
| 6 | Toolkit `doctor` for our layout | Delete the script | 1.5 h |
| 7 | Eval gate for role cards and hook prompts, cases from real failures in `_postmortems.md` | Delete `evals/`; gate is advisory until green twice | 3 h |
| 8 | Offer our `role_card.py` late-title fix to Evan as a PR | Close the PR | 0.5 h (needs Brandon's OK: outward-facing) |

Every step that edits `~/.claude` makes a `.bak-<stamp>` first and needs Brandon's go, per the trust rules.

## Risks
- **Drift returns.** Without step 0 and `VENDORED.md`, the fork keeps diverging silently. Diff on each upstream pull.
- **Two buses.** Running `harness launch` or the installer would create `.harness/` and `~/agent-brain` beside ours. Never run them.
- **Hook regressions.** Hooks fire in bypass mode on every session. One bad edit blocks all agents. Test each on a throwaway session first.
- **Spend.** Reviewer adds one fresh session per job (roughly +20-30% per job). Eval gate spends on each run; set `daily_call_cap`.
- **Evan's repo is public and contains copies of our hooks.** No Brandon names or data found (grep clean). Brandon should know it is public.

## Size
- Steps 0-4 (core value): about 3.75 h, about 1.5% of the daily Claude allowance.
- Steps 5-8: about 7 h, about 3-4%. Can go to Codex for the plugin diff and doctor script.
- Total: about 11 h, about 5% Claude, spread over 2-3 days.

## Not decided here
- Whether `~/Work` becomes a full wiki brain (lint/connect/find) or MegaMind takes those tools. Recommend
  neither for now: no failure has shown we need it.
