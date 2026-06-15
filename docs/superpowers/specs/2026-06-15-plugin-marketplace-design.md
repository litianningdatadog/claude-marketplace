# Plugin Marketplace Design

**Date:** 2026-06-15  
**Status:** Approved  
**Scope:** Restructure `claude-skills` repo into a public, read-only plugin marketplace with standardized installation, browsing, and update lifecycle.

---

## Goals

- Standardize the full skill lifecycle: discover, install, update, remove
- Public read-only access; contributions via PR only
- No manual registry maintenance — CI auto-generates from `SKILL.md` frontmatters
- Start with "latest from main" versioning; schema reserves `version` field for future semver

---

## Repository Structure

```
claude-skills/
├── efficiency-audit/            # skill dirs — unchanged
├── hook-doctor/
├── quicknotes/
├── scripts/
│   └── generate_registry.py     # parses SKILL.md files → registry.json
├── .github/
│   └── workflows/
│       └── deploy-registry.yml  # CI: generate + deploy to GitHub Pages
├── registry.json                # auto-generated, do not edit by hand
├── index.html                   # GitHub Pages human-browsable catalog
├── install.sh                   # bootstrap one-liner for claude-skills CLI
├── README.md                    # updated with marketplace install instructions
└── CLAUDE.md                    # unchanged
```

Skill directories are untouched. `SKILL.md` frontmatter remains the single source of truth.

---

## Registry Manifest Schema (`registry.json`)

```json
{
  "schema_version": 1,
  "updated_at": "2026-06-15T00:00:00Z",
  "source": "https://github.com/litianningdatadog/claude-skills",
  "skills": [
    {
      "name": "efficiency-audit",
      "description": "Analyzes recent Claude Code conversation transcripts...",
      "path": "efficiency-audit",
      "version": null,
      "has_scripts": true
    }
  ]
}
```

- `schema_version` (top-level): manifest format version; CLI rejects registries with an unsupported `schema_version`
- `updated_at`: ISO 8601 datetime (UTC); used by CLI to detect stale cached copies
- `version` (per-skill): `null` now; populated with a semver string when versioning is adopted
- `path`: name of the top-level skill directory in the repo; used by the CLI to download the correct directory
- `has_scripts`: true if a `scripts/` subdirectory exists in the skill directory

### Registry Discovery Rules (`generate_registry.py`)

Only **top-level directories** whose `SKILL.md` frontmatter `name` field matches the directory name are included. Nested `SKILL.md` files (e.g. under `docs/`, `scripts/`, `.github/`) are ignored. This prevents documentation files from being published as skills.

---

## CLI Tool (`claude-skills`)

A shell script installed to `~/.local/bin/claude-skills`. Dependencies: `curl`, Python 3 (standard on any Claude Code machine). No `git` required for skill download (uses GitHub tarball API).

### Commands

```bash
claude-skills add <url>               # register a marketplace source
claude-skills list                    # list available skills from all sources
claude-skills install [source/]<name> # install a skill; source prefix disambiguates
claude-skills update                  # re-fetch registries + update CLI-installed skills
claude-skills remove <name>           # uninstall from ~/.claude/skills/
claude-skills sources                 # list registered sources
```

### State Files

**`~/.claude/marketplace/sources.json`** — registered sources:
```json
{
  "sources": [
    {
      "name": "claude-skills",
      "registry_url": "https://litianningdatadog.github.io/claude-skills/registry.json",
      "repo_url": "https://github.com/litianningdatadog/claude-skills",
      "added_at": "2026-06-15T00:00:00Z"
    }
  ]
}
```

**`~/.claude/marketplace/installed.json`** — tracking record for CLI-managed skills:
```json
{
  "installed": [
    {
      "name": "efficiency-audit",
      "source": "claude-skills",
      "installed_at": "2026-06-15T00:00:00Z",
      "registry_updated_at": "2026-06-15T00:00:00Z"
    }
  ]
}
```

All datetime fields use ISO 8601 UTC format throughout both files.

### Skill Name Collision Across Sources

If two registered sources publish a skill with the same `name`, `claude-skills list` displays each with a `source/name` prefix (e.g. `claude-skills/efficiency-audit`). `claude-skills install efficiency-audit` prints an ambiguity error and asks the user to qualify: `claude-skills install claude-skills/efficiency-audit`.

### Install Flow

1. Fetch `registry.json` from all registered source URLs
2. Locate the skill entry; extract `path` and source `repo_url`
3. Download the skill directory as a GitHub repository tarball (`/archive/refs/heads/main.tar.gz`), extract only the matching `path/` subtree to a temporary directory
4. Move the temp directory atomically to `~/.claude/skills/<name>/` — if the destination already exists, replace it atomically (rename over); warn the user if the destination was not recorded in `installed.json` (i.e. it was manually installed)
5. Record the install in `~/.claude/marketplace/installed.json`
6. Claude Code TUI picks up the skill automatically on next session

**Atomicity:** The download and extraction happen in a temp directory (e.g. `~/.claude/marketplace/tmp/`). The final move is a single `mv` (rename) so a failure before step 4 leaves the existing skill intact.

### Update Behavior

`claude-skills update` only touches skills recorded in `installed.json` (CLI-managed). Skills placed manually via `cp -R` are ignored. For each CLI-managed skill, the CLI re-fetches the registry and replaces the skill directory using the same atomic install flow.

### Remove Behavior

`claude-skills remove <name>` deletes `~/.claude/skills/<name>/` and removes the entry from `installed.json`. It does not touch `sources.json`.

### Bootstrap (`install.sh`)

`install.sh` performs:
1. Downloads the `claude-skills` shell script from the Pages site
2. Installs it to `~/.local/bin/claude-skills` and sets the execute bit
3. Checks whether `~/.local/bin` is on `$PATH`; prints a warning with the required export line if not
4. Runs `claude-skills add https://litianningdatadog.github.io/claude-skills/registry.json` to register the official source
5. Prints a success message and usage hint

---

## CI/CD Pipeline (`.github/workflows/deploy-registry.yml`)

Triggers on push to `main`. Two jobs:

### Job 1: `generate`

1. Run `scripts/generate_registry.py` — discovers top-level skill directories, parses YAML frontmatter, writes `registry.json`
2. Check whether `registry.json` actually changed (compare against the previous committed version)
3. If changed: commit with message `chore: regenerate registry.json [skip ci]` and push to `main` using the `GITHUB_TOKEN` with `contents: write` permission declared at the workflow level. The `[skip ci]` suffix prevents the commit from re-triggering the workflow.
4. If unchanged: skip the commit step

### Job 2: `deploy-pages` (depends on `generate`)

1. Assemble Pages artifact: `registry.json` + `install.sh` + `index.html`
2. Deploy to GitHub Pages → `https://litianningdatadog.github.io/claude-skills/`

### Public Endpoints

| URL | Purpose |
|-----|---------|
| `.../registry.json` | Machine-readable skill index (CLI consumes this) |
| `.../install.sh` | Bootstrap one-liner |
| `.../index.html` | Human-browsable skill catalog |

### Adding a New Skill

Push the skill directory + update `README.md`. CI auto-regenerates `registry.json` and redeploys Pages. No other steps required.

---

## One-Time Manual Setup (GitHub UI)

1. **Settings → Pages → Source:** set to "GitHub Actions"
2. **Settings → Actions → General → Workflow permissions:** set to "Read and write"
3. **Branch protection note:** if `main` has branch protection rules enabled (e.g. required reviews), the CI bot push in Job 1 will be rejected. Either exempt the `github-actions[bot]` from the protection rules, or configure Job 1 to push `registry.json` to a `gh-pages` branch instead of `main` and adjust the deploy job accordingly.

---

## Future Extensions

- **Semver per skill:** populate `version` field in `SKILL.md` frontmatter; CLI pins or upgrades selectively
- **Contribution flow:** PR template + CI validation that checks `SKILL.md` schema before merge
- **Categories/tags:** add `tags` array to `SKILL.md` frontmatter; `generate_registry.py` passes them through; `index.html` renders filter UI
