---
name: efficiency-audit
description: "Analyzes recent Claude Code conversation transcripts to surface recurring inefficiencies, then produces a concrete improvement plan and applies it. Use when the user wants to improve their Claude Code workflow, reduce repeated corrections, eliminate missing-context frustration, or automate recurring patterns. Trigger phrases: 'improve my workflow', 'audit my usage', 'what am I repeating', 'efficiency audit', 'review my conversations', or any request to update CLAUDE.md based on observed patterns."
---

# Efficiency Audit

Pipeline: **analyze → report → propose → apply (with approval)**.

## Phase 0: Check Intent

Ask: "Standard audit, or specific areas to focus on?"
Elevate ad-hoc requirements to High Impact in Phase 2; confirm whether found or not found.

## Phase 1: Analyze

```bash
PLUGIN_ROOT=$(ls -dt ~/.claude/plugins/cache/litianningdatadog-marketplace/efficiency-audit/*/ 2>/dev/null | head -1)
```

```bash
python3 "${PLUGIN_ROOT}/scripts/analyze_conversations.py" \
  --days 30 --project "$(basename "$PWD")" --output json 2>/dev/null
```

```bash
MEMORY_MD=$(python3 "${PLUGIN_ROOT}/scripts/resolve_memory_path.py" 2>/dev/null)
python3 "${PLUGIN_ROOT}/scripts/score_efficiency.py" \
  .claude/CLAUDE.md ~/.claude/CLAUDE.md "$MEMORY_MD" 2>/dev/null
```

Score < 0.5 → warning; 0.0 → Critical Context Blocker (High Impact — run recipe-book procedure before adding rules).
Also check terminal title setup: `references/terminal-title-check.md`.

## Phase 2: Synthesize

Read `references/category-guide.md` for category interpretation and rule-drafting guidance.

## Phase 3: Report

Draft fixes before writing the report:
- `corrections` count ≥ 3 → draft a CLAUDE.md rule using `examples` + `preceding_action`.
- `missing_context` sessions ≥ 3 → write a candidate CLAUDE.md fact.

Route each rule per `references/claude-md-routing.md`. Report structure: `references/report-template.md`.

## Phase 4: Apply

Read `references/governance.md` before proceeding. Plan → Act → Verify each change; never batch.
Apply order: memory entries → CLAUDE.md → settings.json.
Hook fixes are out of scope — hand off to `hook-doctor`.

## Phase 5: Karpathy Guardrails (evidence-based, opt-in)

Run the evidence check in `references/karpathy-guardrails.md` (Phase 5 sections).
If the trigger threshold is met, surface the offer and follow the merge procedure there.
If user declines, do not ask again this session.

## Behavioral Guardrails

Read `references/karpathy-guardrails.md` at every phase; flag violations as `[GUARDRAIL: ...]`.

## Utilities

- Noise false positives: `references/noise-filters.md`
- CLAUDE.md > 200 lines: run `references/recipe-book.md` *before* proposing rules
- Re-run every 2–4 weeks; baseline delta confirms rules are reducing friction
