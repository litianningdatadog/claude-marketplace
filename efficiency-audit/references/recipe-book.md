# File Bloat Remediation — Recipe Book Principle

A `CLAUDE.md` over ~200 lines signals that domain-specific rules have leaked into the root
instruction file. Those rules load on *every* session in every context, even when irrelevant.
The fix: extract them into path-scoped rule files under `.claude/rules/` — Claude Code loads
these only when the active file matches the declared patterns.

**Distinct from the scorer's thresholds** (300→750→5000 lines). The scorer measures continuous
bloat; this procedure triggers at 200 lines and produces a structural refactor, not a trim.

## When to run

After Phase 1, check:
```bash
wc -l ~/.claude/CLAUDE.md .claude/CLAUDE.md 2>/dev/null
```
If either exceeds 200 lines, run this procedure *before* proposing new audit rules.
Adding rules to a bloated file makes the problem worse.

## Step 1 — Classify every rule

Classify each rule as **Core** (applies everywhere — stays in root) or **Domain-scoped**
(applies only to a file type, directory, or tool — extract). Show as a table:

```
| Rule (first 60 chars)         | Classification | Suggested scope   |
|-------------------------------|----------------|-------------------|
| NEVER commit without …        | Core           | keep in CLAUDE.md |
| Use type hints in all …       | Domain         | **/*.py           |
| Always run go test ./… before | Domain         | **/*.go           |
```

Wait for user approval before proceeding.

## Step 2 — Draft path-scoped rule files

For each domain group, draft `.claude/rules/<name>.md` with `paths:` frontmatter:

```markdown
---
description: Python coding conventions
paths: ["**/*.py", "**/pyproject.toml"]
---

Use type hints on all function signatures.
Prefer `pathlib.Path` over `os.path`.
Tests live in `tests/` and use `pytest`.
```

Name files descriptively (`python.md`, `go.md`, `sql.md`). Show full proposed content
of each file before writing.

## Step 3 — Draft the trimmed root CLAUDE.md

Produce a new version containing only Core rules and project architecture. Show the full
new content as a diff or complete block before writing.

## Step 4 — Apply (Plan → Act → Verify, SOSA™ approval required)

Apply in this order:
1. Create `.claude/rules/*.md` files first (additive — safely revertible independently).
2. Trim `CLAUDE.md` second (only after rules files are confirmed correct).

Verify: confirm frontmatter is valid YAML and `wc -l CLAUDE.md` is now under 200.

## Rules file frontmatter reference

| Key | Required | Example |
|-----|----------|---------|
| `description` | recommended | `"Python conventions"` |
| `paths` | required for scoping | `["**/*.py"]` |

Omitting `paths` means the file loads in all contexts — only omit for truly universal
additions that don't belong in root `CLAUDE.md` for other reasons.
