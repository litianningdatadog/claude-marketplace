# Phase 3 Report Template

Present findings using this structure (omit sections with no findings):

```
## Efficiency Audit Report — <date>

### Proposed CLAUDE.md rules (approve/edit/skip each)
- [ ] (project: dd-trace-js) NEVER use worktrees — always use the branch directly.
- [ ] (global) NEVER create a new commit unless explicitly instructed; amend instead.
- [ ] (ask user) NEVER add debug logging without cleaning up before commit.

### High Impact (apply immediately)
- Hook errors that fire on every session
- `terminal_title_skill_missing` — terminal-title skill not installed; recommend installing and re-running audit
- `terminal_title_not_configured` — terminal-title skill installed but no CLAUDE.md rule enforces it
- Correction groups with `count` >= 3 (or `sessions` >= 3)

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
