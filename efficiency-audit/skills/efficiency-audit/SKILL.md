---
name: efficiency-audit
description: "Analyzes recent Claude Code conversation transcripts to surface recurring inefficiencies, then produces a concrete improvement plan and applies it. Use when the user wants to improve their Claude Code workflow, reduce repeated corrections, eliminate missing-context frustration, fix git workflow anti-patterns, or automate recurring patterns. Trigger phrases: 'improve my workflow', 'audit my usage', 'what am I repeating', 'efficiency audit', 'review my conversations', or any request to update CLAUDE.md based on observed patterns."
---

## Phase 0: Check Intent

Ask: "Standard audit, or specific areas to focus on?" Elevate ad-hoc requirements to High Impact in Phase 3.

## Phase 1: Analyze

```bash
PLUGIN_ROOT=$(ls -dt ~/.claude/plugins/cache/litianningdatadog-marketplace/efficiency-audit/*/ 2>/dev/null | head -1)
python3 "${PLUGIN_ROOT}/scripts/analyze_conversations.py" --days 30 --project "$(basename "$PWD")" --output json 2>/dev/null \
| python3 "${PLUGIN_ROOT}/scripts/synthesize_findings.py" 2>/dev/null
```

Synthesis succeeds → Phase 3. Fails → re-run without pipe, go to Phase 2.

Score separately (independent exit code — never combine with synthesis above):

```bash
MEMORY_MD=$(python3 "${PLUGIN_ROOT}/scripts/resolve_memory_path.py" 2>/dev/null)
python3 "${PLUGIN_ROOT}/scripts/score_efficiency.py" .claude/CLAUDE.md ~/.claude/CLAUDE.md "$MEMORY_MD" 2>/dev/null
```

Score < 0.5 → warning; 0.0 → run `references/recipe-book.md` first. Check: `references/terminal-title-check.md`.

## Phase 2: Synthesize

Read `references/category-guide.md`.

## Phase 3: Report

Detect CLAUDE.md locations:

```bash
for f in ~/.claude/CLAUDE.md .claude/CLAUDE.md CLAUDE.md; do [ -f "$f" ] && echo "exists: $f"; done
```

One → route silently. Multiple → read `references/claude-md-routing.md`, wait for choice. None → ask.

**Always use this exact format — never a table:**

```
---
High Impact
Rule N — <title> (~X tokens/month)
▎ <evidence>
▎ Routing: A) <path> [← recommended] | B) <path>
---
Medium Impact  [omit if empty]
Rule N — ...
---
Hook Issues  [omit if hook_errors empty; wording below]
---
Total: ~X tokens/month. Reply: numbers (1 3), all, skip N. Dry-run before writing.
```

**Hook Issues** — if `hook_errors` non-empty, never write "skipping" or "already handled":

```bash
ls ~/.claude/plugins/cache/litianningdatadog-marketplace/hook-doctor/*/skills/hook-doctor/SKILL.md 2>/dev/null | grep -q . && echo installed || echo not_installed
```

- not_installed → `Hook errors found. Install: claude plugin install hook-doctor@litianningdatadog-marketplace`
- installed, not yet diagnosed → `Run /hook-doctor to scan. (Evidence: X failures, Y sessions.)`
- installed, deferred this session → `⚠ Run /hook-doctor when ready. (Evidence: X failures, Y sessions.)`
- installed, confirmed clean → omit section.

Only cite transcript numbers (failures, sessions). Never use hook-doctor output counts.

## Phase 4: Apply

Read `references/governance.md`. Order: memory → CLAUDE.md → settings.json. Hook fixes → `hook-doctor`.

```bash
python3 "${PLUGIN_ROOT}/scripts/apply_rules.py" --dry-run <path> '["r1", "r2"]'
python3 "${PLUGIN_ROOT}/scripts/apply_rules.py" <path> '["r1", "r2"]'
```

One rule at a time: run `--dry-run`, print output, **STOP — ask "Looks right? yes / edit / skip."** Do not write until they reply in this turn. On yes: write, verify, report. Repeat.

## Phase 5: Karpathy Guardrails (opt-in)

Read `references/karpathy-guardrails.md`; offer once if threshold met, skip if declined. Governs Phase 4 apply, not analysis.

## Utilities

- Noise false positives: `references/noise-filters.md`
- CLAUDE.md > 200 lines: `references/recipe-book.md` first
- Re-run every 2–4 weeks
