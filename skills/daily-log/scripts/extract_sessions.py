#!/usr/bin/env python3
"""Pull only the human-readable conversation out of agent session files. Stdlib only.

Why: Claude Code and Codex session files also hold system prompts, tool schemas,
tool output, and hidden reasoning. A daily log needs none of that, and some of
it can hold secrets. This script keeps user and assistant text and drops the rest.

Usage:
  python3 extract_sessions.py claude PATH_OR_GLOB... --since ISO --until ISO
  python3 extract_sessions.py codex  PATH_OR_GLOB... --since ISO --until ISO
  ... | python3 redact.py          # always pipe the output through redact.py

--since/--until are ISO 8601 with an offset (for example 2026-11-12T00:00:00-06:00).
Output is one block per message: "[time] role project: text". Each message is cut
at --max-chars. A summary line goes to stderr: files read, messages kept.
"""
import argparse
import glob
import json
import os
import sys
from datetime import datetime, timezone

# Text that agents inject into user turns. Not something the person typed.
INJECTED_PREFIXES = (
    "<system-reminder", "<environment_context", "<user_instructions", "<command-", "<local-command",
    "# AGENTS.md", "<INSTRUCTIONS>", "<permissions", "<collaboration_mode", "Caveat:",
)


def parse_ts(value):
    if not value:
        return None
    try:
        if isinstance(value, (int, float)):
            return datetime.fromtimestamp(value, tz=timezone.utc)
        dt = datetime.fromisoformat(value.replace("Z", "+00:00"))
        return dt if dt.tzinfo else dt.replace(tzinfo=timezone.utc)
    except ValueError:
        return None


def blocks_text(content, kinds):
    if isinstance(content, str):
        return content
    parts = []
    for b in content or []:
        if isinstance(b, dict) and b.get("type") in kinds and isinstance(b.get("text"), str):
            parts.append(b["text"])
    return "\n".join(parts)


def claude_messages(rec):
    # Keep only user and assistant records. Skips attachment, queue-operation,
    # api-request-shape, api-request-blob, custom-title, and the rest.
    if rec.get("type") not in ("user", "assistant") or rec.get("isSidechain"):
        return
    msg = rec.get("message") or {}
    role = msg.get("role") or rec["type"]
    # text blocks only: drops thinking, tool_use, tool_result
    text = blocks_text(msg.get("content"), ("text",))
    yield role, text, rec.get("cwd")


def codex_messages(rec):
    if rec.get("type") != "response_item":
        return
    p = rec.get("payload") or {}
    # role developer and system carry the harness prompts. Skip them.
    if p.get("type") != "message" or p.get("role") not in ("user", "assistant"):
        return
    yield p["role"], blocks_text(p.get("content"), ("input_text", "output_text", "text")), None


READERS = {"claude": claude_messages, "codex": codex_messages}


def expand(paths):
    files = []
    for p in paths:
        p = os.path.expanduser(p)
        hits = glob.glob(p, recursive=True) if any(c in p for c in "*?[") else [p]
        for h in hits:
            if os.path.isdir(h):
                files += glob.glob(os.path.join(h, "**", "*.jsonl"), recursive=True)
            elif os.path.isfile(h):
                files.append(h)
    return sorted(set(files))


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("agent", choices=sorted(READERS))
    ap.add_argument("paths", nargs="+")
    ap.add_argument("--since", required=True)
    ap.add_argument("--until", required=True)
    ap.add_argument("--max-chars", type=int, default=1500)
    ap.add_argument("--skip-dir", action="append", default=[], help="skip sessions whose cwd contains this text")
    args = ap.parse_args(argv)
    since, until = parse_ts(args.since), parse_ts(args.until)
    if not since or not until:
        sys.exit("extract_sessions.py: --since and --until must be ISO 8601 timestamps")
    read = READERS[args.agent]
    files = expand(args.paths)
    kept = 0
    touched = 0
    for f in files:
        # Cheap pre-filter: a file last written before the window cannot hold window messages.
        if datetime.fromtimestamp(os.path.getmtime(f), tz=timezone.utc) < since:
            continue
        hit = False
        try:
            fh = open(f, encoding="utf-8", errors="replace")
        except OSError as exc:
            sys.stderr.write("extract_sessions.py: cannot read %s: %s\n" % (f, exc))
            continue
        with fh:
            for line in fh:
                try:
                    rec = json.loads(line)
                except ValueError:
                    continue
                ts = parse_ts(rec.get("timestamp"))
                if ts is None or not (since <= ts < until):
                    continue
                for role, text, cwd in read(rec):
                    text = (text or "").strip()
                    if not text or text.startswith(INJECTED_PREFIXES):
                        continue
                    if any(s and s in (cwd or "") for s in args.skip_dir):
                        continue
                    if len(text) > args.max_chars:
                        text = text[: args.max_chars] + " ...[cut]"
                    project = os.path.basename((cwd or "").rstrip("/")) or os.path.basename(os.path.dirname(f))
                    print("[%s] %s %s: %s\n" % (ts.astimezone(since.tzinfo).strftime("%Y-%m-%d %H:%M"), role, project, text))
                    kept += 1
                    hit = True
        touched += hit
    sys.stderr.write("extract_sessions.py: %s: %d file(s) matched, %d in window, %d message(s) kept\n"
                     % (args.agent, len(files), touched, kept))
    return 0


if __name__ == "__main__":
    sys.exit(main())
