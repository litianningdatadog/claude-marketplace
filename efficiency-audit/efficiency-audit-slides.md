# efficiency-audit

## What

**efficiency-audit**
*Stop repeating yourself. Let Claude learn from your conversations.*

- A Claude Code skill that reads your own AI conversation history to find recurring friction — then fixes it automatically.
- Built for developers who use Claude Code daily and want it to get smarter over time.

---

## The Problem: Claude Keeps Forgetting

**You say the same things every session. Claude doesn't remember.**

- "Don't commit yet" — for the fifth time this week
- "We use Go, not Python" — re-explained every Monday
- "Always read the file before editing it" — every bug has the same cause
- Each correction costs tokens, breaks flow, and builds frustration

**The symptom is friction. The root cause is missing persistent context.**

---

## What Is efficiency-audit?

**A Claude Code skill that audits your conversation history and proposes concrete fixes.**

- Reads your Claude Code transcript logs (`~/.claude/projects/**/*.jsonl`)
- Finds patterns: corrections, missing context, slow session starts, automation candidates, tool failures
- Drafts targeted `CLAUDE.md` rules and `settings.json` hooks to eliminate the friction
- Applies changes only with your explicit approval — one change at a time

**One command. Five minutes. Fewer repeated corrections for weeks.**

---

## Why This Matters

**Every repeated correction is a tax on your attention — and your tokens.**

| Friction Type | What it looks like | Cost |
|---|---|---|
| Corrections | "No, don't do X" | Wasted tokens + broken flow |
| Missing context | Re-explaining stable facts | Slower session start |
| Tool failures | Edit before Read, git errors | Debug time |
| Automation gaps | "Always run X before Y" | Manual overhead every session |

**efficiency-audit converts these from recurring costs into one-time fixes.**

---

## The 5-Phase Pipeline

**analyze → synthesize → report → apply → (opt-in) guardrails**

```
Phase 1: Analyze     — scan transcripts, score CLAUDE.md for bloat
Phase 2: Synthesize  — group findings into actionable rule drafts
Phase 3: Report      — ranked improvement plan (High → Medium → Automation)
Phase 4: Apply       — Plan → Act → Verify, one approval per change
Phase 5: Guardrails  — opt-in merge of Karpathy behavioral principles
```

Each phase is skippable or adjustable. The tool meets you where you are.

---

## Phase 1: Analyze (What Gets Scanned)

**Five pattern categories extracted from your real conversation history:**

- **`corrections`** — messages where you redirected Claude, with `preceding_action` (what Claude did just before) to write targeted rules
- **`missing_context`** — stable facts you re-explained (candidates for `CLAUDE.md` or memory)
- **`slow_start_context`** — session-opening orientation messages (stable ones belong in config)
- **`automation_candidates`** — recurring procedural intent ("always run tests before committing")
- **`tool_failures`** — Edit/Write without prior Read, git errors, permission failures, hook crashes

**Plus:** `score_efficiency.py` scores your `CLAUDE.md` on a 0.0–1.0 bloat scale. Files ≥ 5,000 lines are flagged as **Critical Context Blockers** (score = 0.0, exits non-zero).

---

## Phase 2 & 3: Synthesize and Report

**Raw patterns → ranked, human-readable improvement plan**

`synthesize_findings.py` pipes findings through Claude to produce:

```json
{
  "proposed_rule": "NEVER create a git commit without explicit instruction.",
  "estimated_tokens_saved": 340,
  "scope": "global",
  "evidence": ["don't commit yet", "i didn't say to commit"],
  "confidence": 0.92
}
```

**The report is ordered by impact:**
1. Proposed CLAUDE.md rules (approve / edit / skip each one)
2. High Impact items
3. Medium Impact items
4. Automation Opportunities (hook candidates)
5. Open Questions

---

## Phase 4: Apply (Safe by Design)

**Rules are written with idempotent marker blocks — re-running never duplicates.**

```markdown
<!-- efficiency-audit:start -->
NEVER create a git commit without explicit instruction.
Always Read a file before Edit or Write.
<!-- efficiency-audit:end -->
```

- Re-running the audit **replaces** the block in-place, not appends
- `apply_rules.py --dry-run` previews the exact diff before any write
- Changes are applied in order: memory → `CLAUDE.md` → `settings.json`

**One approval per file. No surprises.**

---

## SOSA™ Governance

**SOSA™ — Supervised Orchestrated Secured Agents**

The skill is governed by four non-negotiable rules:

1. **Stop and ask** before writing to `CLAUDE.md`, `MEMORY.md`, or `.claude/rules/`
2. **Never batch writes** — each file change is a separate approval step
3. **Show before you write** — full proposed content shown before execution
4. **No silent fallbacks** — if rejected, return to the report and ask what to do next

**Why this matters:** CLAUDE.md is a high-blast-radius file. A bad rule can silently degrade every future Claude session. The governance framework ensures each change is intentional.

---

## Phase 5: Karpathy Guardrails (Opt-In)

**Andrej Karpathy's four behavioral principles, merged into your CLAUDE.md.**

The four principles:
1. **Think Before Coding** — state assumptions; stop when ambiguous
2. **Simplicity First** — write only what was asked; no speculative features
3. **Surgical Changes** — touch only what the task requires
4. **Goal-Driven Execution** — define a verifiable outcome before acting

**The merge is smart, not naive:**
- Deduplicated against your existing rules (no blind append)
- Only offered when the audit finds evidence for a principle (≥2 matching corrections)
- Produces structured output with clear headings — you review the full diff before it's written

---

## Baseline Tracking and Deltas

**Audit results improve over time — and you can measure it.**

After each run, a baseline is saved to `~/.claude/efficiency-audit-baseline.json`.

Subsequent runs show deltas inline:

```
CORRECTIONS (22 matches, was 30, -27% ↓)
MISSING_CONTEXT (8 matches, was 14, -43% ↓)
```

**This turns a one-time audit into a feedback loop:**
- Rules you added → patterns should shrink
- New patterns emerging → new rules needed
- Recommended cadence: re-run every 2–4 weeks

---

## How to Use It

**Install once. Run whenever friction accumulates.**

```bash
# Install
/plugin marketplace add litianningdatadog/claude-marketplace
/plugin install efficiency-audit@litianningdatadog-marketplace
```

**Trigger in any Claude Code session:**
- `"audit my usage"`
- `"improve my workflow"`
- `"what am I repeating"`
- `"efficiency audit"`
- `/efficiency-audit`

**Or run scripts directly for a quick preview:**
```bash
python3 scripts/analyze_conversations.py --days 30 --output text 2>/dev/null
```

---

## Architecture Overview

**Three layers: skill, scripts, references**

```
efficiency-audit/
├── skills/efficiency-audit/SKILL.md   ← agent operating instructions (5-phase procedure)
├── scripts/
│   ├── analyze_conversations.py       ← transcript scanner
│   ├── synthesize_findings.py         ← LLM rule synthesis
│   ├── score_efficiency.py            ← CLAUDE.md bloat scorer
│   ├── apply_rules.py                 ← idempotent marker-block writer
│   └── resolve_memory_path.py         ← git-root-aware memory path resolver
└── references/
    ├── category-guide.md              ← pattern interpretation
    ├── governance.md                  ← SOSA™ rules
    ├── recipe-book.md                 ← 4-step CLAUDE.md refactor procedure
    └── karpathy-guardrails.md         ← Phase 5 merge logic
```

**No external dependencies.** Pure Python stdlib. Tests run with `python3 -m unittest`.

---

## Key Design Decisions

**Why these choices were made:**

| Decision | Rationale |
|---|---|
| Read transcripts, not memory | Memory is curated; transcripts capture what actually happened |
| Idempotent marker blocks | Re-running is safe — no duplicate rule accumulation |
| LLM synthesis via `synthesize_findings.py` | Pattern grouping alone can't write good imperative rules |
| SOSA™ governance | CLAUDE.md changes have long-term blast radius — human must stay in the loop |
| Score + Recipe Book as separate signals | File size and file structure are independent problems |
| Baseline delta tracking | Without measurement, improvement is invisible |

---

## Known Limitations & Roadmap

**What's not supported yet:**

| Gap | Impact | Status |
|---|---|---|
| `@`-imported files in `CLAUDE.md` | Score and rule routing ignore inlined content from `@path/to/file` includes | Pending |
| Multi-workspace transcript merging | Audits are scoped to one project filter at a time | Planned |
| Hook suggestion auto-generation | `automation_candidates` are surfaced but not wired to `hookify` automatically | Planned |
| Multi-agent support | Transcripts from Codex (`~/.codex/`) and OpenCode are not scanned | Future |

**`@` import support — why it matters:**

Claude Code allows `CLAUDE.md` to include external files using `@path/to/file` syntax. Today:
- `score_efficiency.py` scores only the literal bytes of the CLAUDE.md file — it does not follow `@` references
- `apply_rules.py` writes rules into the main file, even if the logical owner is an imported sub-file
- The audit may miss rules already expressed in an `@`-imported file, leading to false duplicate suggestions

**Planned fix:** resolve `@` imports before scoring and before routing proposed rules, so the tool sees the same effective context Claude sees.

**Multi-agent support — why it matters:**

The audit currently only reads Claude Code transcripts (`~/.claude/projects/**/*.jsonl`). Developers increasingly use multiple coding agents in parallel — Codex stores sessions under `~/.codex/`, and OpenCode uses its own log format. Patterns that span agents (e.g. the same correction made in both Claude Code and Codex) are invisible today.

**Planned approach:** add pluggable transcript adapters for each agent format, normalize them to the same event schema, and surface cross-agent patterns as a distinct finding category so rules can target the right config file per agent.

---

## Summary

**efficiency-audit in one sentence:**

> Reads your Claude Code conversation history, finds the friction patterns you keep hitting, drafts targeted fixes, and applies them safely — so Claude gets better at working with you over time.

**Three things to remember:**
1. **Why:** Repeated corrections and missing context are learnable — but only if someone reads the transcripts
2. **What:** A 5-phase pipeline that turns friction patterns into approved, idempotent CLAUDE.md rules
3. **How:** Install the plugin, say "audit my usage", review the ranked report, approve changes one at a time

---

*Generated from: `efficiency-audit/skills/efficiency-audit/SKILL.md` and `README.md`*
*Date: 2026-06-16*
