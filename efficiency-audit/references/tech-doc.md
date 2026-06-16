# efficiency-audit — Technical Documentation

## Objective

Developers who use Claude Code repeatedly end up correcting the same behaviors, re-supplying the same context at session start, and missing automation opportunities across dozens of conversations. These patterns are invisible without systematic analysis. `efficiency-audit` closes that feedback loop: it mines Claude Code session transcripts, identifies recurring friction, translates findings into concrete CLAUDE.md rules and `settings.json` hooks, and applies them with explicit user approval.

---

## Problem Space

Claude Code session transcripts (`.jsonl` files under `~/.claude/projects/`) are the ground truth for how a user actually interacts with the agent. Four signal types are diagnostic:

| Signal | What it indicates |
|---|---|
| **Corrections** | User overrode Claude's default behavior repeatedly — suggests a missing CLAUDE.md rule |
| **Missing context** | User re-explained a stable fact across sessions — suggests a CLAUDE.md or memory entry |
| **Slow-start context** | Session-opening orientation messages — stable facts that belong in CLAUDE.md |
| **Automation candidates** | User stated procedural intent ("always run X before Y") — suggests a `settings.json` hook |

---

## Solution Design

### Pipeline overview

```
Phase 0 (intent check)
       ↓
Phase 1: analyze_conversations.py  →  synthesize_findings.py (LLM synthesis)
                                             ↓  (fallback: raw JSON + category-guide.md)
Phase 2: score_efficiency.py (file bloat scorer)
       ↓
Phase 3: Report (approve / edit / skip each rule)
       ↓
Phase 4: apply_rules.py  →  idempotent marker-block write to CLAUDE.md
       ↓  (opt-in)
Phase 5: Karpathy guardrails merge
```

### Key invariants

- **Never batch changes.** Every file mutation (CLAUDE.md, MEMORY.md, `settings.json`) is a separate approval step under SOSA™ governance.
- **Idempotent writes.** `apply_rules.py` uses an `<!-- efficiency-audit:start/end -->` marker block, so re-running the audit never duplicates rules.
- **CLAUDE.md routing.** When both `~/.claude/CLAUDE.md` and a project-level CLAUDE.md exist, the skill always asks the user which file to target — it never silently routes.
- **Noise filtering.** Context-compaction messages, tool output pastes, and skill-body injections are stripped before pattern matching to avoid false positives.

---

## Features

### Transcript analysis (`analyze_conversations.py`)

- Scans `~/.claude/projects/**/*.jsonl` filtered by `--days N` and `--project` (substring-tolerant matching).
- Extracts four scored message categories per session; groups by first-matched pattern to prevent double-counting.
- Tracks `preceding_action` (what Claude did immediately before a correction) to enable targeted rule drafting.
- Classifies tool errors into 8 types (`unread_write`, `permission_denied`, `git_error`, etc.).
- Persists a baseline to `~/.claude/efficiency-audit-baseline.json` for delta comparisons across re-runs.

### LLM synthesis (`synthesize_findings.py`)

- Compacts findings into a structured digest (≤30,000 chars) and calls the Claude CLI.
- Returns a `recommendations` JSON array with `proposed_rule`, `estimated_tokens_saved`, `scope`, `target`, and `confidence`.
- Falls back gracefully to the Phase 2 manual synthesis path if the CLI call times out or fails.

### File bloat scorer (`score_efficiency.py`)

- Piecewise linear scoring: 0–300 lines → 1.0 (optimal), 750 lines → 0.5 (warning), 5,000+ lines → 0.0 (Critical Context Blocker, exits 1).
- A score of 0.0 triggers the recipe-book remediation procedure before any new rules are added.
- The 200-line threshold separately triggers the `recipe-book.md` alert (extract domain-scoped rules into `.claude/rules/<name>.md`).

### Idempotent rule writer (`apply_rules.py`)

- Three modes: `--read` (inspect existing block), `--dry-run` (preview diff), plain write (apply).
- Diffs old vs. new rules with kept/removed/added symbols before committing.

### Hook error detection

- Reads `hookErrors` from `stop_hook_summary` records and `hook_non_blocking_error` attachment records.
- Deduplicates by command string or hook name.
- If `hook-doctor` is installed, refers repair there; otherwise suggests installing it.

### Terminal title integration

- Detects whether the `terminal-title` skill and hook are installed.
- If hook is missing (and no iTerm2 conflict), surfaces as a High Impact finding with a proposed hook addition.

### Karpathy guardrails (Phase 5, opt-in)

- Scans finding examples for keyword signals across four principles: Think Before Coding, Simplicity First, Surgical Changes, Goal-Driven Execution.
- Only offers the merge if ≥2 keyword hits are found across findings.
- Fetches the upstream Karpathy text, merges with the user's CLAUDE.md via LLM reasoning (deduplication, verbatim preservation of user rules), shows full diff before applying.

---

## Architecture

```
efficiency-audit/
├── .claude-plugin/plugin.json          # Plugin manifest
├── skills/efficiency-audit/SKILL.md   # Agent procedure (5 phases)
├── references/
│   ├── category-guide.md              # Phase 2 pattern interpretation
│   ├── governance.md                  # SOSA™ approval rules
│   ├── noise-filters.md               # Patterns stripped before analysis
│   ├── recipe-book.md                 # CLAUDE.md bloat remediation
│   ├── terminal-title-check.md        # Hook gap detection logic
│   ├── claude-md-routing.md           # Multi-file routing protocol
│   ├── karpathy-guardrails.md         # Phase 5 merge procedure
│   └── report-template.md            # Phase 3 output structure
└── scripts/
    ├── analyze_conversations.py       # Transcript scanner + pattern matcher
    ├── synthesize_findings.py         # LLM synthesis via Claude CLI
    ├── score_efficiency.py            # File bloat scorer
    ├── apply_rules.py                 # Idempotent marker-block writer
    └── resolve_memory_path.py         # Resolves project MEMORY.md path
```

### Data flow

1. `analyze_conversations.py` reads JSONL transcripts → emits findings JSON.
2. `synthesize_findings.py` reads findings JSON via stdin → calls Claude CLI → emits `recommendations` JSON.
3. Agent presents recommendations for user approval (Phase 3).
4. `apply_rules.py` writes approved rules into a marker block in CLAUDE.md (Phase 4).
5. `score_efficiency.py` runs independently on CLAUDE.md files to gate Phase 4 with a bloat check.

### Path resolution

Scripts are installed to a versioned cache path (`~/.claude/plugins/cache/claude-marketplace/<name>/<version>/`). SKILL.md resolves the path dynamically:

```bash
PLUGIN_ROOT=$(ls -dt ~/.claude/plugins/cache/claude-marketplace/efficiency-audit/*/ 2>/dev/null | head -1)
```

Hook configs use `${CLAUDE_PLUGIN_ROOT}` which the hook runtime expands at execution time.

---

## Re-run cadence

Every 2–4 weeks, or after any significant change in workflow patterns. Delta comparisons against the persisted baseline make repeated runs meaningful rather than redundant.
