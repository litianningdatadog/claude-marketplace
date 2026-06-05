---
name: efficiency-audit
description: "Analyzes recent Claude Code conversation transcripts to surface recurring inefficiencies, then produces a concrete improvement plan and applies it. Use when the user wants to improve their Claude Code workflow, reduce repeated corrections, eliminate missing-context frustration, or automate recurring patterns. Trigger phrases: 'improve my workflow', 'audit my usage', 'what am I repeating', 'efficiency audit', 'review my conversations', or any request to update CLAUDE.md based on observed patterns."
---

# Efficiency Audit

## Overview

Analyze recent Claude Code conversation history to identify friction patterns, then apply
concrete fixes: CLAUDE.md rule additions, memory entries, hook repairs, and settings
improvements. Pipeline: **analyze → report → propose → apply (with approval)**.

## Pipeline

### Phase 0: Check Intent

Before doing anything else, ask the user:

> "Run the standard efficiency audit, or do you have specific areas you'd like me to focus on?"

If they say "just run it" / "standard" / "as is" — proceed to Phase 1 with defaults.

If they provide ad-hoc requirements, note them and weave them into Phase 2 synthesis:
elevate matching findings to High Impact regardless of frequency, and call out whether
their stated concern is confirmed or not found in the data.

### Phase 1: Analyze

Run the analysis script to extract patterns from the last 30 days of conversations:

```bash
python3 ~/.claude/skills/efficiency-audit/scripts/analyze_conversations.py \
  --days 30 \
  --output json \
  2>/dev/null
```

To restrict to the current project only, add `--project <current-dir-name>`. For a quick
text preview:

```bash
python3 ~/.claude/skills/efficiency-audit/scripts/analyze_conversations.py \
  --days 30 \
  --output text \
  2>/dev/null
```

### Phase 2: Synthesize Findings

After receiving the JSON output, interpret each category:

**`corrections`** — Messages where the user redirected or corrected Claude. Extract the
recurring *class* of mistake. Ask: what CLAUDE.md rule or memory entry would have prevented
this? Filter out context-compaction messages ("This session is being continued...").

**`missing_context`** — Messages where the user re-explained context. Ask: what facts are
being re-introduced session after session? These belong in CLAUDE.md project instructions
or in `~/.claude/projects/.../memory/` as persistent memories.

**`slow_start_context`** — Messages that orient Claude at session start. Ask: which facts
are stable (always true) vs. transient (task-specific)? Stable facts go in CLAUDE.md.

**`automation_candidates`** — Messages expressing recurring procedural intent
("always run X before Y", "every time I commit..."). Ask: should this become a hook in
`settings.json`? Use the `hookify:configure` skill for hook additions.

**`hook_errors`** — Failing hooks reduce reliability silently. Each error includes hook
name, failing command, and stderr. Diagnose and fix where possible. Common cause:
`$CLAUDE_PLUGIN_ROOT` containing spaces — the variable needs quoting: `"${CLAUDE_PLUGIN_ROOT}"`.

**`repeated_topics`** — High-frequency topic words reveal what the user spends time on.
Cross-reference with other categories to prioritize fixes.

### Phase 3: Produce a Prioritized Improvement Report

Present findings in this structure (omit sections with no findings):

```
## Efficiency Audit Report — <date>

### High Impact (apply immediately)
- Hook errors that fire on every session
- Corrections that recur 3+ times across sessions

### Medium Impact (apply with user review)
- CLAUDE.md additions for project-specific rules
- Memory entries for stable personal preferences

### Automation Opportunities
- Patterns that could become hooks or custom commands
- List each with proposed hook event and command

### Open Questions
- Patterns needing user input to interpret correctly
```

For each finding include: what was observed (1-2 example message quotes), which file to
change, and the exact proposed change as a diff or new content block.

### Phase 4: Apply Changes (with user approval)

Never apply changes silently. Show each proposed change, state which file it modifies,
then wait for explicit confirmation before writing.

Apply in this order:
1. Hook error fixes (most reliably broken, clearest impact)
2. Memory entries (user-local, lowest blast radius)
3. CLAUDE.md additions (affects all future sessions in the project)
4. settings.json additions (use `hookify:configure` skill for hook changes)

For CLAUDE.md additions, append to the relevant project's CLAUDE.md or the global
`~/.claude/CLAUDE.md`. Use `~/.claude/projects/.../memory/` for personal preferences
that should not appear in a checked-in file.

## False Positive Filters

Skip these when reporting — they are system-generated, not real user friction:

- "This session is being continued from a previous conversation..." → context-compaction
- Messages starting with `<command-name>` or `<command-message>` tags → skill invocations
- Security review boilerplate injected by the `dd:mcp-security-review` skill
- Subagent dispatch messages from workflow orchestration

## Re-running the Audit

Run every 2–4 weeks to catch new patterns. After applying changes, note the current
baseline counts for `corrections` and `missing_context` so the next run can measure
whether friction decreased in those areas.
