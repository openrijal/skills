#!/usr/bin/env python3
"""Mask secrets in text. Stdlib only.

Usage:
  python3 redact.py < in.txt > out.txt
  python3 redact.py --config-dir ~/.config/daily-log < in.txt > out.txt
  python3 redact.py --deny "Project Falcon" --deny "re:acme-\\d+" < in.txt
  python3 redact.py --check < note.md        # exit 3 if anything would be masked

Masks: private key blocks, JWTs, AWS/GitHub/OpenAI/Anthropic/Slack/Google/Stripe
keys, bearer and basic auth headers, passwords in URLs, key=value secrets, and
long high-entropy strings. Plus a deny-list: one literal or "re:<regex>" per
line in <config-dir>/deny.txt, or --deny / --deny-file.

Not masked on purpose: 40-hex git SHAs, UUIDs, and anything inside a URL path,
because daily notes link to commits and pages.
"""
import argparse
import math
import os
import re
import sys
from collections import Counter

MASK = "[REDACTED:{}]"

# Specific token shapes. Order matters: first match wins on overlapping text.
TOKEN_PATTERNS = [
    ("private-key", re.compile(
        r"-----BEGIN [A-Z0-9 ]*PRIVATE KEY(?: BLOCK)?-----.*?-----END [A-Z0-9 ]*PRIVATE KEY(?: BLOCK)?-----",
        re.S)),
    # Truncated block: header with no footer. Mask the header and the base64 lines after it.
    ("private-key", re.compile(
        r"-----BEGIN [A-Z0-9 ]*PRIVATE KEY(?: BLOCK)?-----(?:[ \t]*\r?\n?[A-Za-z0-9+/=\\n]{16,})*")),
    ("jwt", re.compile(r"\beyJ[A-Za-z0-9_-]{8,}\.eyJ[A-Za-z0-9_-]{8,}\.[A-Za-z0-9_-]{4,}")),
    ("aws-access-key", re.compile(r"\b(?:AKIA|ASIA|AGPA|AIDA|AROA|ANPA|ANVA|AIPA)[A-Z0-9]{16}\b")),
    ("github-token", re.compile(r"\bgithub_pat_[A-Za-z0-9_]{20,}")),
    ("github-token", re.compile(r"\bgh[pousr]_[A-Za-z0-9]{20,}")),
    ("anthropic-key", re.compile(r"\bsk-ant-[A-Za-z0-9_-]{20,}")),
    ("openai-key", re.compile(r"\bsk-(?:proj-|svcacct-|admin-)?[A-Za-z0-9_-]{20,}")),
    ("slack-token", re.compile(r"\bxox[abposr]-[A-Za-z0-9-]{10,}")),
    ("slack-token", re.compile(r"\bxapp-[A-Za-z0-9-]{10,}")),
    ("google-api-key", re.compile(r"\bAIza[0-9A-Za-z_-]{35}\b")),
    ("stripe-key", re.compile(r"\b[sr]k_(?:live|test)_[A-Za-z0-9]{16,}")),
    ("bearer-token", re.compile(r"(?i)\b(bearer|basic)\s+[A-Za-z0-9._~+/=-]{16,}")),
    ("url-password", re.compile(r"(?i)\b([a-z][a-z0-9+.-]*://[^\s:/@]+:)([^\s@/]{3,})(@)")),
]

SENSITIVE_KEY = (
    r"[A-Za-z0-9_.-]*(?:password|passwd|pwd|passphrase|secret|token|api[_-]?key|apikey|"
    r"access[_-]?key|private[_-]?key|client[_-]?secret|credentials?)[A-Za-z0-9_.-]*"
)
KEY_VALUE = re.compile(
    r"(?i)(?P<key>\b" + SENSITIVE_KEY + r")(?P<sep>(?:\\*[\"'])?\s*[:=]\s*)(?P<q>(?:\\*[\"'])?)(?P<val>[^\s\\\"',;<>{}\[\]()]{6,})"
)
PLACEHOLDER = re.compile(r"(?i)^(\[REDACTED|\$\{|\$[A-Z_]+$|%|x{4,}|\*{3,}|<|your[_-]|example|changeme|none$|null$|true$|false$)")

URL = re.compile(r"https?://[^\s\"'<>)\]]+")
ENTROPY_CANDIDATE = re.compile(r"(?<![A-Za-z0-9+_=-])[A-Za-z0-9+_=-]{32,}(?![A-Za-z0-9+_=-])")
GIT_SHA = re.compile(r"^[0-9a-f]{40}$")
UUID = re.compile(r"^[0-9a-fA-F]{8}(-[0-9a-fA-F]{4}){3}-[0-9a-fA-F]{12}$")


def shannon(s):
    counts = Counter(s)
    n = len(s)
    return -sum(c / n * math.log2(c / n) for c in counts.values())


def looks_random(tok):
    if GIT_SHA.match(tok) or UUID.match(tok):
        return False
    classes = sum([any(c.islower() for c in tok), any(c.isupper() for c in tok), any(c.isdigit() for c in tok)])
    if classes < 2 or not any(c.isdigit() for c in tok):
        return False
    return shannon(tok) >= 4.0


def load_deny(args):
    entries = list(args.deny or [])
    paths = list(args.deny_file or [])
    if args.config_dir:
        paths.append(os.path.join(os.path.expanduser(args.config_dir), "deny.txt"))
    for p in paths:
        p = os.path.expanduser(p)
        if os.path.isfile(p):
            with open(p, encoding="utf-8") as fh:
                entries += [ln.strip() for ln in fh if ln.strip() and not ln.lstrip().startswith("#")]
    compiled = []
    for e in entries:
        try:
            compiled.append(re.compile(e[3:]) if e.startswith("re:") else re.compile(re.escape(e), re.I))
        except re.error as exc:
            sys.stderr.write("redact.py: bad deny pattern %r: %s\n" % (e, exc))
    return compiled


def redact(text, deny=()):
    counts = Counter()

    def sub(pattern, label, s, repl=None):
        def _r(m):
            counts[label] += 1
            return repl(m) if repl else MASK.format(label)
        return pattern.sub(_r, s)

    for label, pat in TOKEN_PATTERNS:
        if label == "url-password":
            text = sub(pat, label, text, lambda m: m.group(1) + MASK.format(label) + m.group(3))
        elif label == "bearer-token":
            text = sub(pat, label, text, lambda m: m.group(1) + " " + MASK.format(label))
        else:
            text = sub(pat, label, text)

    def kv(m):
        val = m.group("val")
        if PLACEHOLDER.match(val):
            return m.group(0)
        counts["secret-assignment"] += 1
        return m.group("key") + m.group("sep") + m.group("q") + MASK.format("secret-assignment")
    text = KEY_VALUE.sub(kv, text)

    url_spans = [m.span() for m in URL.finditer(text)]

    def in_url(start, end):
        return any(s <= start and end <= e for s, e in url_spans)

    def ent(m):
        tok = m.group(0)
        if in_url(*m.span()) or not looks_random(tok):
            return tok
        counts["high-entropy"] += 1
        return MASK.format("high-entropy")
    text = ENTROPY_CANDIDATE.sub(ent, text)

    for pat in deny:
        text = sub(pat, "deny-list", text)
    return text, counts


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--config-dir", help="directory that may hold deny.txt")
    ap.add_argument("--deny", action="append", help="extra literal or re:<regex> to mask")
    ap.add_argument("--deny-file", action="append", help="file with one deny entry per line")
    ap.add_argument("--check", action="store_true", help="print nothing, exit 3 if anything would be masked")
    ap.add_argument("--report", action="store_true", help="print mask counts to stderr")
    args = ap.parse_args(argv)
    data = sys.stdin.buffer.read().decode("utf-8", errors="replace")
    out, counts = redact(data, load_deny(args))
    total = sum(counts.values())
    if args.report or args.check:
        sys.stderr.write("redact.py: masked %d item(s) %s\n" % (total, dict(counts)))
    if args.check:
        return 3 if total else 0
    sys.stdout.write(out)
    return 0


if __name__ == "__main__":
    sys.exit(main())
