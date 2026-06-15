# Phase 2 Category Interpretation Guide

The script pre-clusters results into categories. Groups are sorted by frequency; the first
entries are the highest-recurrence friction. Noise is filtered before extraction, so every
group is real input.

## `corrections`

Messages where the user redirected Claude. Each group carries:
- `count`/`sessions` — frequency and breadth.
- `top_project` — where it happened most; use to route the CLAUDE.md fix.
- `preceding_action` — what Claude did *immediately before* the correction (the causal
  trigger). **Use this** to write a rule targeting the specific behavior, not just the topic.

Draft a CLAUDE.md rule per high-count group using both `examples` and `preceding_action`:

> correction: "don't commit yet"  
> preceding_action: "Committed as `abc123`..."  
> → rule: `NEVER create a git commit without explicit instruction. Finish the task, show a diff, then ask.`

Rules must be imperative, specific, and scoped to the right CLAUDE.md via `top_project`.

## `missing_context`

Messages where the user re-explained stable facts. Candidates for CLAUDE.md project
instructions or `~/.claude/projects/.../memory/` entries. Use `top_project` to route.

## `slow_start_context`

Messages that orient Claude at session start. Ask: stable (always true) or transient
(task-specific)? Stable facts go in CLAUDE.md.

## `automation_candidates`

Recurring procedural intent ("always run X before Y"). Candidates for `settings.json`
hooks — use the `hookify:configure` skill.

## `terminal_title_not_configured` / `terminal_title_skill_missing`

See `references/terminal-title-check.md` for proposed rule text, routing, and post-apply note.

## `hook_errors`

Failing hooks (e.g. `exit=127`, unquoted `${CLAUDE_PLUGIN_ROOT}`). **Don't repair here** —
hand off to the `hook-doctor` skill. Errors are historical; a `--days` re-run after fixing
confirms no new failures.
