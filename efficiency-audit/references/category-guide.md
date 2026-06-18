# Phase 2 Category Interpretation Guide

Draft thresholds: `corrections` count ≥ 3 → CLAUDE.md rule (use `examples` + `preceding_action`); `missing_context` sessions ≥ 3 → CLAUDE.md fact; `tool_failures` count ≥ 2 → CLAUDE.md rule.

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

## `git_workflow_errors`

Messages where the user flagged a broken git operation — stale remote refs in cascade
rebases, PRs showing unexpected file counts, out-of-date base branches, or corrective
force-push loops. Threshold: count ≥ 2.

Unlike `corrections` (which catches generic redirections), this category targets multi-step
git command anti-patterns where a later step reads `origin/<branch>` state that an earlier
step in the same pipeline hasn't pushed yet.

**Rule pattern:** produce a CLAUDE.md *procedure block*, not a one-liner rule. The
key invariant to encode:

> In a single cascade command (reset + cherry-pick + push for multiple stacked branches),
> reference the **local** branch name, not `origin/<branch>`. The remote tracking ref
> is stale until after `git push`.
>
> CORRECT: `git reset --hard tianning.li/log-capture-2-plugin`
> WRONG:   `git reset --hard origin/tianning.li/log-capture-2-plugin` (stale until pushed)

Route to the project's CLAUDE.md if `top_project` is set; otherwise global.

## `hook_errors`

Failing hooks (e.g. `exit=127`, unquoted `${CLAUDE_PLUGIN_ROOT}`). **Don't repair here.**
First check whether the `hook-doctor` skill is installed:

```bash
ls ~/.claude/plugins/cache/litianningdatadog-marketplace/hook-doctor/*/skills/hook-doctor/SKILL.md 2>/dev/null | grep -q . && echo "installed" || echo "not_installed"
```

- **Installed** → recommend running `/hook-doctor`. It scans all plugins, explains the blast
  radius, and applies fixes with explicit opt-in.
- **Not installed** → surface in Phase 3:
  > "Hook errors were found but the `hook-doctor` skill is not installed. Install it from
  > the [claude-marketplace repo](https://github.com/litianningdatadog/claude-marketplace): run
  > `/plugin install hook-doctor@claude-marketplace`, then re-run `/efficiency-audit`."

Errors are historical — they persist until they age out of the `--days` window. After
fixing, a fresh session plus a small `--days` re-run confirms no new failures appear.

**Already diagnosed / deferred this session:** If hook-doctor was run earlier in this
session and the user chose to defer (option d / skip), do NOT silently omit the finding
or say "Skipping" — that implies the issue is resolved. Instead, surface it explicitly as
an open action item:

> "⚠ Hook issues exist (N fixable) — deferred this session. Run `/hook-doctor` when ready to fix."

"Deferred" means the problem is still there. "Resolved" (fixed or confirmed clean by
hook-doctor) means it can be omitted. Never conflate the two.
