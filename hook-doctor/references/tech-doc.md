# hook-doctor — Technical Documentation

## Objective

Claude Code plugin hooks are shell commands executed by the agent runtime at lifecycle events (`SessionStart`, `PreToolUse`, `PostToolUse`, etc.). A misconfigured hook silently fails or causes `exit 127` — breaking the behavior it was meant to enable, with no obvious error surfaced to the user. `hook-doctor` performs static analysis of all installed hook configurations, identifies the specific failure mode for each problem, and applies targeted fixes with explicit approval.

---

## Problem Space

The most common hook failure mode is `exit 127` (command not found) caused by unquoted path variable tokens in agent mode. When Claude Code runs hooks in agent mode, `${CLAUDE_PLUGIN_ROOT}` expands to a path that may contain spaces (e.g., `/Users/jane doe/.claude/...`). Without quotes, the shell tokenizes the path on the space and cannot find the command.

Other failure modes:

| Problem | Symptom |
|---|---|
| Unquoted `${CLAUDE_PLUGIN_ROOT}` | `exit 127` in agent mode |
| Script lacks execute bit | `permission denied` at runtime |
| Referenced script missing on disk | Hook silently does nothing |
| Unknown event name | Hook never fires |
| Missing `command` field | Hook handler is structurally invalid |
| Invalid JSON in hooks.json | Entire plugin's hooks fail to load |

Crucially, hooks come from two sources: plugin `hooks/hooks.json` files (installed to a versioned cache) and user/project `settings.json` files. Both need to be scanned.

---

## Solution Design

### Static analysis only

All six checks are purely static — no hooks are executed during diagnosis. This means the scan is safe to run regardless of what the hooks do, and findings are reproducible.

### Fixable vs. report-only

| Check | Fixable? | Repair action |
|---|---|---|
| `unquoted_path_var` | Yes | Wrap unquoted `${CLAUDE_*}/...` token in double quotes |
| `script_not_executable` | Yes (opt-in) | `chmod +x` the script |
| `missing_script` | No — file is absent | Report only |
| `unknown_event` | No — likely a typo | Report only |
| `missing_command_field` | No — structural issue | Report only |
| `invalid_json` | No — manual fix needed | Report only |

Fixable findings are applied by `inspect_hooks.py --apply`; report-only findings are surfaced for the user to address manually.

### Blast radius transparency

Before any fix is applied, the skill explicitly states:
- Which file will be modified (plugin cache file vs. user settings).
- That plugin cache edits don't survive a `git pull` or reinstall — the durable fix is an upstream PR.
- Options: (a) fix locally, (b) upstream PR, (c) both, (d) skip.

---

## Features

### Comprehensive source discovery

`inspect_hooks.py` scans:
- `~/.claude/plugins/marketplaces/**` and `~/.claude/plugins/cache/**` (all installed plugin hooks).
- `~/.claude/settings.json`, `~/.claude/settings.local.json` (global user settings).
- `<project>/.claude/settings.json`, `<project>/.claude/settings.local.json` (project-level settings).
- Stale agent-mode session snapshots under `~/Library/Application Support/Claude/local-agent-mode-sessions/.../hooks/hooks.json` (via `--root`).

### Path confinement

Script path resolution uses `_confine(base, candidate)` to prevent path traversal. A resolved script path is only accepted if it is relative to the declared plugin root — `../`-escaped paths are rejected.

### Symlink safety

`apply_chmod` re-checks `p.is_symlink()` immediately before modifying permissions, preventing a symlink-swap attack between scan and apply.

### Idempotent quote fix

`quote_path_vars(command)` uses a regex substitution that only matches *unquoted* path variable tokens — already-quoted tokens are not double-quoted. Re-running `--apply` on an already-fixed file is safe.

### Integration with efficiency-audit

`efficiency-audit` detects `hook_errors` by reading historical transcript records. When it finds them, it defers repair to `hook-doctor` rather than attempting in-line fixes. After `hook-doctor` resolves issues, a fresh Claude Code session plus a short `efficiency-audit --days 7` re-run confirms no new failures.

---

## Architecture

```
hook-doctor/
├── .claude-plugin/plugin.json          # Plugin manifest
├── skills/hook-doctor/SKILL.md         # Agent procedure (4 steps)
└── scripts/
    └── inspect_hooks.py                # Scanner, fixer, and reporter
```

### `inspect_hooks.py` internals

```
gather_sources(args)
    ├── find_hooks_files(root)           # rglobs hooks/hooks.json, deduplicates by realpath
    └── find_settings_files(project)    # checks 4 settings.json paths

scan_file(path, project_dir)
    ├── iter_commands(data)              # yields (event, handler) pairs from hooks dict
    ├── check: unknown_event
    ├── check: missing_command_field
    ├── check: unquoted_path_var
    └── _resolve_script_path()
         ├── check: missing_script
         └── check: script_not_executable

fix_file(path)                           # surgical raw-text replacement (unquoted_path_var)
apply_chmod(finding)                     # chmod +x with symlink re-check
```

### Event validation

`VALID_EVENTS` is a hardcoded set of 30 recognized Claude Code hook event names. Any event name not in this set triggers an `unknown_event` finding. This catches typos like `UserSubmitPrompt` vs. `UserPromptSubmit`.

---

## 4-Step Procedure

```
Step 0: Check intent (diagnose-only vs. fix-locally vs. upstream PR)
Step 1: Scan (invoke inspect_hooks.py, display grouped findings)
Step 2: Present findings (state blast radius, present options a/b/c/d)
Step 3: Apply (Plan → Act → Verify, re-scan to confirm)
Step 4: Upstream fix (prepare PR to source plugin repo)
```

Steps 3–4 are skipped entirely in diagnose-only mode.
