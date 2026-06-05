#!/usr/bin/env python3
"""
Analyze Claude Code conversation transcripts to surface efficiency patterns.

Usage:
    python3 analyze_conversations.py [--days N] [--project PATH] [--output json|text]

Defaults to scanning all projects under ~/.claude/projects/ from the last 30 days.
"""

import argparse
import json
import os
import re
import sys
from collections import Counter, defaultdict
from datetime import datetime, timezone, timedelta
from pathlib import Path


CORRECTION_PATTERNS = [
    r"\bno[,!]?\s+(don'?t|do not|stop|never)\b",
    r"\b(don'?t|do not|stop|never|avoid)\s+(do(ing)?|use|run|add|create|write)\b",
    r"\b(wrong|incorrect|not (right|what I|what we))\b",
    r"\b(I said|I told you|as I mentioned|like I said)\b",
    r"\b(that'?s not|that is not)\s+what\b",
    r"\bplease (don'?t|do not|stop|never)\b",
    r"\b(revert|undo|go back)\b",
    r"\binstead[,\s]+(use|do|run|write)\b",
    r"\b(you should|you need to|you must)\s+not\b",
]

CONTEXT_REQUEST_PATTERNS = [
    r"\b(remember|recall|as I said|as we discussed|from (last|previous|earlier))\b",
    r"\b(context is|the situation is|for context|to clarify)\b",
    r"\b(I('?ve| have) (told|explained|mentioned|said) (you |this |before|already))\b",
    r"\b(again,? (this|the|we|I))\b",
    r"\b(same as|same pattern|same approach)\b",
]

SLOW_START_PATTERNS = [
    r"\b(first[,\s]+(let'?s?|you should|read|check|look at))\b",
    r"\b(before (you|we) (start|begin|do|proceed))\b",
    r"\b(the project (is|uses|has)|this repo(sitory)? (is|uses|has))\b",
    r"\b(we use|we don'?t use|in this project)\b",
    r"\b(always use|never use|make sure (you )?use)\b",
]

AUTOMATION_PATTERNS = [
    r"\b(every time|always (run|check|do|use)|each time|whenever)\b",
    r"\b(after (each|every) (commit|push|build|test))\b",
    r"\b(before (committing|pushing|building|testing|merging))\b",
    r"\b(automatically|auto-?\w+)\b",
    r"\b(hook|alias|shortcut|script)\b",
]


def parse_args():
    p = argparse.ArgumentParser(description="Analyze Claude Code conversations for efficiency patterns")
    p.add_argument("--days", type=int, default=30, help="Scan conversations from last N days (default: 30)")
    p.add_argument("--project", type=str, default=None, help="Restrict to a specific project path (substring match)")
    p.add_argument("--output", choices=["json", "text"], default="json", help="Output format")
    p.add_argument("--min-sessions", type=int, default=1, help="Min sessions for a pattern to appear in output")
    return p.parse_args()


def find_jsonl_files(days: int, project_filter: str | None) -> list[Path]:
    base = Path.home() / ".claude" / "projects"
    cutoff = datetime.now(tz=timezone.utc) - timedelta(days=days)
    results = []
    for f in base.rglob("*.jsonl"):
        if project_filter and project_filter not in str(f.parent):
            continue
        try:
            mtime = datetime.fromtimestamp(f.stat().st_mtime, tz=timezone.utc)
            if mtime >= cutoff:
                results.append(f)
        except OSError:
            pass
    return sorted(results, key=lambda f: f.stat().st_mtime, reverse=True)


def extract_session_data(path: Path) -> dict:
    session = {
        "path": str(path),
        "project": path.parent.name,
        "session_id": path.stem,
        "user_messages": [],
        "assistant_messages": [],
        "hook_errors": [],
        "tool_denials": [],
        "timestamps": [],
        "entrypoints": Counter(),
        "git_branches": set(),
    }

    with open(path, encoding="utf-8", errors="ignore") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            try:
                d = json.loads(line)
            except json.JSONDecodeError:
                continue

            t = d.get("type", "")
            ts = d.get("timestamp", "")
            if ts:
                session["timestamps"].append(ts)

            ep = d.get("entrypoint", "")
            if ep:
                session["entrypoints"][ep] += 1

            branch = d.get("gitBranch", "")
            if branch:
                session["git_branches"].add(branch)

            if t == "user":
                msg = d.get("message", {})
                content = msg.get("content", "")
                if isinstance(content, list):
                    text_parts = [c.get("text", "") for c in content if isinstance(c, dict) and c.get("type") == "text"]
                    content = " ".join(text_parts)
                if content:
                    session["user_messages"].append({"text": content, "ts": ts})

            elif t == "assistant":
                msg = d.get("message", {})
                content = msg.get("content", "")
                if isinstance(content, list):
                    text_parts = [c.get("text", "") for c in content if isinstance(c, dict) and c.get("type") == "text"]
                    content = " ".join(text_parts)
                if content:
                    session["assistant_messages"].append({"text": str(content)[:500], "ts": ts})

            elif t == "attachment":
                att = d.get("attachment", {})
                att_type = att.get("type", "")
                if "hook" in att_type and att.get("exitCode") not in (None, "0", 0):
                    session["hook_errors"].append({
                        "hook_name": att.get("hookName", ""),
                        "exit_code": att.get("exitCode"),
                        "stderr": att.get("stderr", "")[:200],
                        "command": att.get("command", ""),
                    })

    return session


def match_patterns(text: str, patterns: list[str]) -> list[str]:
    matches = []
    text_lower = text.lower()
    for pat in patterns:
        if re.search(pat, text_lower):
            matches.append(pat)
    return matches


def score_message(text: str) -> dict:
    return {
        "corrections": match_patterns(text, CORRECTION_PATTERNS),
        "context_requests": match_patterns(text, CONTEXT_REQUEST_PATTERNS),
        "slow_start": match_patterns(text, SLOW_START_PATTERNS),
        "automation": match_patterns(text, AUTOMATION_PATTERNS),
    }


def analyze(sessions: list[dict]) -> dict:
    findings = {
        "summary": {
            "sessions_analyzed": len(sessions),
            "total_user_messages": 0,
            "date_range": {"earliest": None, "latest": None},
            "projects": Counter(),
        },
        "corrections": [],
        "missing_context": [],
        "slow_start_context": [],
        "automation_candidates": [],
        "hook_errors": [],
        "repeated_topics": [],
    }

    all_timestamps = []
    correction_messages = []
    context_messages = []
    slow_start_messages = []
    automation_messages = []
    topic_counter = Counter()

    for sess in sessions:
        proj = sess["project"]
        findings["summary"]["projects"][proj] += 1

        for msg in sess["user_messages"]:
            findings["summary"]["total_user_messages"] += 1
            text = msg["text"]
            ts = msg["ts"]
            if ts:
                all_timestamps.append(ts)

            scores = score_message(text)

            if scores["corrections"]:
                correction_messages.append({
                    "text": text[:300],
                    "project": proj,
                    "session": sess["session_id"],
                    "ts": ts,
                })

            if scores["context_requests"]:
                context_messages.append({
                    "text": text[:300],
                    "project": proj,
                    "session": sess["session_id"],
                    "ts": ts,
                })

            if scores["slow_start"]:
                slow_start_messages.append({
                    "text": text[:300],
                    "project": proj,
                    "session": sess["session_id"],
                    "ts": ts,
                })

            if scores["automation"]:
                automation_messages.append({
                    "text": text[:300],
                    "project": proj,
                    "session": sess["session_id"],
                    "ts": ts,
                })

            # Topic clustering: extract noun phrases / keywords from user messages
            words = re.findall(r"\b[a-z][a-z_\-]{3,}\b", text.lower())
            stop = {"that", "this", "with", "from", "have", "will", "what", "when", "which", "your",
                    "just", "also", "then", "than", "been", "were", "they", "them", "into", "does",
                    "make", "need", "want", "sure", "like", "some", "each", "dont", "dont", "please",
                    "here", "there", "more", "very", "would", "could", "should", "about", "after",
                    "before", "added", "used", "using", "file", "code", "line", "lines", "change"}
            for w in words:
                if w not in stop:
                    topic_counter[w] += 1

        for he in sess["hook_errors"]:
            findings["hook_errors"].append({**he, "project": proj, "session": sess["session_id"]})

    if all_timestamps:
        all_timestamps.sort()
        findings["summary"]["date_range"]["earliest"] = all_timestamps[0]
        findings["summary"]["date_range"]["latest"] = all_timestamps[-1]

    # Deduplicate and limit findings
    findings["corrections"] = correction_messages[:20]
    findings["missing_context"] = context_messages[:20]
    findings["slow_start_context"] = slow_start_messages[:20]
    findings["automation_candidates"] = automation_messages[:20]

    # Top recurring topics (excluding 1-off mentions)
    findings["repeated_topics"] = [
        {"topic": w, "count": c}
        for w, c in topic_counter.most_common(30)
        if c >= 3
    ]

    # Deduplicate hook errors by command
    seen_hooks = set()
    deduped_hooks = []
    for he in findings["hook_errors"]:
        key = he.get("command", "") or he.get("hook_name", "")
        if key not in seen_hooks:
            seen_hooks.add(key)
            deduped_hooks.append(he)
    findings["hook_errors"] = deduped_hooks

    return findings


def print_text_report(findings: dict):
    s = findings["summary"]
    print(f"=== Claude Code Efficiency Audit ===")
    print(f"Sessions analyzed: {s['sessions_analyzed']}")
    print(f"User messages: {s['total_user_messages']}")
    dr = s["date_range"]
    print(f"Date range: {dr['earliest'][:10] if dr['earliest'] else 'N/A'} → {dr['latest'][:10] if dr['latest'] else 'N/A'}")
    print(f"Projects: {dict(s['projects'].most_common(5))}")
    print()

    sections = [
        ("CORRECTIONS / REDIRECTIONS", "corrections",
         "Messages where you corrected Claude's approach"),
        ("MISSING CONTEXT (re-explained)", "missing_context",
         "Messages that suggest Claude lacked context you'd already provided"),
        ("SLOW START (per-session orientation)", "slow_start_context",
         "Messages that set context Claude should know automatically"),
        ("AUTOMATION CANDIDATES", "automation_candidates",
         "Messages suggesting recurring tasks that could be hooks or CLAUDE.md rules"),
    ]

    for title, key, desc in sections:
        items = findings[key]
        print(f"--- {title} ({len(items)} instances) ---")
        print(f"    {desc}")
        for item in items[:5]:
            print(f"    [{item['project'][:30]}] {item['text'][:150]}")
        if len(items) > 5:
            print(f"    ... and {len(items)-5} more")
        print()

    if findings["hook_errors"]:
        print(f"--- HOOK ERRORS ({len(findings['hook_errors'])} unique) ---")
        for he in findings["hook_errors"][:5]:
            print(f"    [{he['hook_name']}] exit={he['exit_code']} cmd={he['command'][:60]}")
            if he["stderr"]:
                print(f"      stderr: {he['stderr'][:100]}")
        print()

    if findings["repeated_topics"]:
        print(f"--- TOP RECURRING TOPICS ---")
        topics = [(t["topic"], t["count"]) for t in findings["repeated_topics"][:15]]
        print("    " + ", ".join(f"{t}({c})" for t, c in topics))
        print()


def main():
    args = parse_args()
    files = find_jsonl_files(args.days, args.project)
    print(f"Scanning {len(files)} conversation files from last {args.days} days...", file=sys.stderr)

    sessions = []
    for f in files:
        try:
            sess = extract_session_data(f)
            if sess["user_messages"]:
                sessions.append(sess)
        except Exception as e:
            print(f"  Warning: could not parse {f}: {e}", file=sys.stderr)

    print(f"Parsed {len(sessions)} sessions with user messages", file=sys.stderr)
    findings = analyze(sessions)

    if args.output == "json":
        print(json.dumps(findings, indent=2, default=str))
    else:
        print_text_report(findings)


if __name__ == "__main__":
    main()
