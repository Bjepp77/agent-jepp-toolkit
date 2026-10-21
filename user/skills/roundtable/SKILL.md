---
name: round-table
description: >
  Evaluate a plan, decision, or piece of work through a panel of expert personas built
  from real craft, battle-test each one, synthesize as CEO, then execute. Trigger when
  Brandon says things like "round table this," "executive round table," "round table,"
  "spin up personas," "have a [X], [Y], and [Z] evaluate this," "get expert opinions then
  decide and do it," "persona panel," "pressure-test this from different lenses," or any
  request that names multiple expert roles to judge something and wants a single decided
  plan executed at the end. Runs: draft a plan -> grounded persona subagents (each self-
  red-teaming) -> round table -> diligence -> CEO call -> execute -> confirm critiques landed.
---
<!-- Provenance: Brandon Jeppson's own Round Table skill, ported from MegaMind/Claude_Cowork/Skills/roundtable-skill/SKILL.md on 2026-10-21. Changes: loop log de-vaulted, Verify Before Handover pointer, "Feeding a build" section added (from the retired forge skill and the 2026-10-21 round table). -->


# Round Table

A reusable decision-and-execution process. The job: embody the best version of the stakeholders Brandon would want reviewing his work, synthesize their views into one strong output, and stay honest about the human expertise that's still missing.

Brandon uses this pattern often: have several expert personas independently evaluate something, battle-test each view, reconcile in a round table, then have one "CEO" make the call and carry it out.

## When to run this
Any task framed as "evaluate this from multiple expert angles, then decide and do it." The personas may be named by Brandon or chosen by you to fit the task.

## Lite vs full (pick based on stakes — don't ask, just pick)
- **Lite (default):** quick gut-check, low stakes. Exactly 3 personas, each self-red-teams in one pass. No working files. Runs in a single response, ends in chat. If it needs a file, it's not lite — escalate to full and say so.
- **Full:** high-stakes ship (goes to a manager, client or partner, or is an irreversible call). 3-4 personas, each self-red-teaming. Plan saved to a working file; round-table reasoning saved only if it'll be reused. Full diligence + closeout.
- Default lite. Go full only when a wrong answer is costly. Never prompt "lite or full" — pick and move; Brandon will say "go full" if he wants it.

## Inputs to confirm (ask only if genuinely ambiguous)
- **The object:** what's being evaluated (a plan, a draft, a strategy, a file system, a decision).
- **The personas:** who's on the panel. If unspecified, pick 3-4 that genuinely stress the work from different directions. Match lenses to the object (a shipping deliverable wants a domain leader, a skeptic/buyer, a bar-setter, an end-user; a file cleanup does not need a "buyer"). Distinct incentives beat prestigious titles.
- **The output:** what "execute" produces (a document, a rebuild, a zip, a set of edits).

Use AskUserQuestion only if these are truly unclear. Otherwise pick sensible defaults and proceed.

## The process (run in order)

### 1. Draft the plan
Gather the real source material first so the plan is grounded, not hypothetical. Write a short, concrete plan for the object under review (full mode: save it to a working file). Make it specific enough to attack: proposed structure, what's in/out, the claims being made.

### 2. Spin up the panel (grounded, in parallel)
Launch persona subagents in a **single message with multiple Agent tool calls** so they run concurrently. Give each:
- A sharp identity and lens ("You are a [role]. Your lens: [what they uniquely care about].").
- **Ground in real craft first (silent):** before judging, establish the real craft of the role — the frameworks they actually use, the standards they hold, what they kill on sight. The returned report must show that grounding only as specifics (named frameworks, exact standards applied), never as a preamble explaining its method.
- The exact files to read (the plan + only the source slice they need), by absolute path. Don't dump the whole corpus into every subagent.
- A demand for honesty over flattery, grounded in real quoted details.
- **Self-red-team in one pass:** draft the verdict, then attack it as a hostile same-domain rival would, and return only what survives plus a one-line note on what the red-team killed. (Don't try to run a persona and a separate red-team agent as a back-and-forth — parallel subagents can't negotiate.)
- A fixed output contract, so the panel is comparable:
  - **Verdict** (3-4 sentences).
  - **ADD** (what the plan misses, from this lens).
  - **CUT** (fluff / overclaim / credibility risk).
  - **REFRAME** (weak framings rewritten, with exact language).
  - **Strongest single thing** from this lens + how to frame it.
  - **Survived the red-team** (the 1-2 points that held up under attack — these carry the most weight).
  - **Distrust triggers** (what would make this persona doubt the work).

### 3. Reconvene as a round table
Synthesize the reports into one record:
- **Convergence:** what every persona agreed on (these become non-negotiable).
- **Conflicts:** where personas disagree, stated as a real tension to resolve.
- **Collapse check:** if two personas overlap heavily, the panel lacked distinct incentives — note it and weight their shared point less, not more.
- Full mode: save this to a file only if the reasoning will be reused.

### 4. Do diligence before deciding (the spine — never skip)
Verify any factual or numerical claim the panel flagged against the primary source (the tracker, the CRM, the actual files). If a flagged claim can't be verified against a primary source, cut it from the final output — don't hedge it, don't ship it with a caveat. This is the step most likely to change the output. Run it even on lite and single-pass: a wrong number in front of a partner is the costly failure here.

### 5. Act as CEO — make the call
Take the reports + diligence findings and decide. Resolve each conflict explicitly (state the ruling and why). Judgment, not consensus — pick the strongest defensible path even when personas disagree, and challenge unanimous convergence rather than rubber-stamping it (the panel can be confidently wrong together). The final plan must be impressive and true at the same time; cut anything that only survives if no one checks.

### 6. Execute
Build the thing the plan calls for, applying every CEO ruling. If it's a deliverable Brandon keeps, save it to the right folder and, when useful, package it (e.g., a zip) and present the files.

### 7. Closeout
- **Full mode:** check the output against each persona's ADD / CUT / REFRAME — mark each addressed or consciously rejected (with a reason). Then add the **human gap:** a short note on what a real person in these seats would add that an LLM can't (current internal context, taste, relationships, this-quarter politics), framed as the 2-3 real people Brandon should pressure-test with before he ships. Also note the **lift:** how many panel items actually changed the deliverable — if zero survived diligence, run lite or single-pass next time.
- **Lite mode:** one line — what the panel changed and the single biggest thing to watch. Skip the full table and human-gap note.

## Output style
Follow Brandon's standing preferences: tight, scannable, no em dashes, no corporate jargon, sales-floor-direct. In chat, narrate the round table briefly — each persona's position in a line or two, then the CEO decision. Never dump the full subagent reports.

## Defaults
- Mode: lite unless a wrong answer is costly. Don't ask — pick and move.
- Personas, if unspecified: 3-4 with genuinely different incentives, matched to the object.
- Always ground personas in real craft before they judge.
- Always run diligence (#4), even on lite.
- Full mode: always run the closeout + human-gap note. Lite: one-line closeout.
- Always end by actually executing, not just recommending.

## Feeding a build (added 2026-10-21, replaces forge)
When the object is a feature or app about to be built, run the round table before Team Kit `/spec`:
- The CEO rulings go into the spec's "Decisions already made". Rejected options go into "Considered and rejected".
- Name **the one invariant**: the single rule that wins every conflict. Put it under "Constraints in this repo".
- Then follow `docs/overnight-build.md` in the agent-jepp-toolkit repo: restore-point tag, `/spec`, human approval, `/build-spec`.
- Never launch a build with `--dangerously-skip-permissions` on a real repo.

## Loop log (mandatory)
Every run, embedded or standalone, appends one line: date | object | mode | panel | lift (how many panel items changed the deliverable, and the biggest one).
Where: the project's `docs/roundtable-log.md` when the run is about a repo, otherwise `~/Work/wiki/roundtable-log.md`. A round table that runs and does not log is a failed run.

Before presenting, run the "Verify before handover" checklist in `~/.claude/CLAUDE.md`.
