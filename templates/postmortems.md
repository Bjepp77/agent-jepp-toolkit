---
type: ledger
updated: YYYY-MM-DD
---

# Postmortems: failure, then installed fix

A failure that is only described will happen again. A failure turned into a gate will not.
Add an entry the same day a failure is caught. Prose is the weakest fix, so every entry
says which kind of fix it got and whether that fix is really installed.

Fix status is one of:
- INSTALLED: a gate or script exists and was tested.
- PARTIAL
- NOT YET

## Entries

### #1 (YYYY-MM-DD): <one-line failure>

- **What happened.**
- **Why.**
- **Fix.** (hook / setting / script / CI / prose)
- **Status.** INSTALLED | PARTIAL | NOT YET
- **Source.**
