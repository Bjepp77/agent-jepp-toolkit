# Vendored from agent-brain-harness

Upstream: https://github.com/NaluKicks-808/agent-brain-harness
Pinned commit: `f6c121a` (2026-10-21 16:35 -0600). Read-only clone: `~/Code/agent-brain-harness`.
Plan: `docs/agent-brain-harness-plan.md`.
Frozen (owner, 2026-10-22: no live links to Evan's work; keep copied pieces, credited). These copies are ours now:
no upstream pulls, no pull requests to upstream. The license notice below stays.

| Upstream file | Copied to | Commit | Local changes |
|---|---|---|---|
| `core/roles/reviewer.md` | `~/.claude/harness/reviewer.md` | f6c121a | none |
| `core/roles/lead.md` (verify section) | `~/.claude/harness/lead.md` "Verify before you report done" | f6c121a | rewritten for Agent subagents instead of `spawn`; `.harness` file bus dropped |
| `adapters/claude-code/extras/hooks/reply_check.py` | `~/.claude/hooks/reply_check.py` | f6c121a | `VOICE_TIERS` cap 1300 -> 500 chars (~80 words, our caveman cap). Replaces our blocking 80-word lead/worker check with a next-prompt nudge |
| `adapters/claude-code/extras/hooks/voice_nudge.py` | `~/.claude/hooks/voice_nudge.py`, wired on UserPromptSubmit | f6c121a | none |
| `brain/template/tools/expire_rows.py`, `ledger_merge.py`, their tests | `~/Work/tools/`, `~/Work/tools/tests/` | f6c121a | none |
| `brain/template/.gitattributes` (ledger-rows line) | `~/Work/.gitattributes` + clone git config driver | f6c121a | `wiki/log.md` union line left out (no log.md in ~/Work) |
| `brain/template/tools/agenda.py` (`TAG`, `STRUCK_TITLE`, `is_closed`, `strike_title`) | `~/Work/tools/agenda.py` | f6c121a | only these four; rest of our trimmed agenda.py kept |
| `skills/wtfhappened/SKILL.md` | `~/.claude/skills/wtfhappened/SKILL.md` | f6c121a | paths -> `~/Work`; `agent-brain-harness` CLI, `find.py`, `lint.py` steps removed |
| `harness.py` `doctor_*` (lines 686-803; idea only) | `lib/doctor.py`, `tests/test_doctor.py` | f6c121a | rewritten from scratch for `~/.claude` + `~/Work` checks; read-only; stdlib only; `ok`/`warn`/`bad` lines with fixes |

## MIT notice (travels with every file above)

MIT License

Copyright (c) 2026 agent-brain-harness contributors

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.
