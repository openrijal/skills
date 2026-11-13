---
name: daily-log
description: >-
  Writes one daily log note from your own activity: AI agent sessions (Claude
  Code, Codex, and others), GitHub, calendar, email, Slack, Jira, and git logs.
  Reads a config and rules file written by daily-log-setup, redacts secrets, and
  writes into your notes folder. Use for the scheduled nightly run or when asked
  for a day's log. Read-only toward every source.
license: MIT
compatibility: Needs file read and write access to a notes folder. Python 3 for the redaction and extraction scripts. Git is optional.
metadata:
  author: Nitesh Rijal
  version: "0.1.0"
---
# Daily log

Write one note for one day. The note is evidence for later, so be accurate, link sources, and never invent. If you have not run `daily-log-setup` yet, run it first. It writes the config this skill reads.

## 1. Find and read the config

Look in this order and use the first folder that contains `daily-log.config.yaml`:

1. The folder in the `DAILY_LOG_CONFIG_DIR` environment variable, or named in the prompt.
2. `~/.config/daily-log/`
3. `./.daily-log/` in the current directory.

Read `daily-log.config.yaml` and `rules.md` from that folder. Read `rules.md` **word for word** and follow it. If a rule there conflicts with a hard rule below, the hard rule wins and you say so in the run report. If no config exists, stop and tell the user to run `daily-log-setup`.

The config lives outside the skill folder on purpose, so updating the skill never overwrites it.

## Hard rules

- **Read-only toward every source.** Never post, comment, reply, send, react, merge, transition a ticket, or change anything outside the notes folder.
- **Redact before writing.** All text from sessions, chats, and email passes through `scripts/redact.py` before you use it. See step 3 and step 6.
- **No full email or chat bodies.** Summarize and link.
- **Never overwrite what a person wrote.** Write only between `<!-- daily-log:start -->` and `<!-- daily-log:end -->`.
- **Never write to the Inbox folder.** Logs go to `notes.daily_dir`.
- **Never use skip-permissions flags** or ask the user to.
- **Say so when a source is empty.** Never quietly write a thin log. See step 5.

## 2. Work out the window

Use `window.mode` and the user's timezone from the config.

- `previous_day`: 00:00 to 24:00 of the previous calendar day, in the user's timezone. Compute the ISO timestamps with offsets for `--since` and `--until`.
- `since_last_note`: from the end of the last note until now, capped at `window.max_hours`.

If the user names a different day in the prompt, use that day.

## 3. Collect from each source, read-only

For each enabled source in the config, collect activity inside the window. Skip anything in `sources.off_limits`.

**Agent sessions.** Read [references/session-sources.md](references/session-sources.md) first. For Claude Code and Codex, use the extractor and pipe it through redaction in one command, so raw text never reaches you:

```bash
python3 scripts/extract_sessions.py claude "<path>/**/*.jsonl" --since <ISO> --until <ISO> \
  | python3 scripts/redact.py --config-dir <config dir>
```

(Use `codex` for Codex.) The extractor keeps only user and assistant text and drops system prompts, tool output, and hidden reasoning. Note the file and message counts it prints on stderr. For other agents, follow their entry in `session-sources.md`. If an entry says **unverified**, list the path and check the real format before reading.

**Connectors** (GitHub, Slack, Jira, calendar, email, git logs): use the tool the config names, with the scope the config sets, for example `gh` or an MCP connector. Read only. For GitHub: PRs authored and reviewed, issues, and commits in scope. For email: threads with real people, not newsletters, promos, receipts, or notifications. For Slack: only the channels and messages the config allows.

**If Python is unavailable**, read the text yourself and mask anything that looks like a key, token, password, connection string, or private key block, and state in the run report that the scripted pass did not run.

If a source fails, record the reason and carry on.

## 4. Dedupe and group

The same PR can appear in GitHub, Slack, and an agent session. Merge them into one line with one link. Group the rest by project.

## 5. Write the note

Use `notes.template` (`builtin` means [references/templates/daily-note.md](references/templates/daily-note.md)). Fill the agent-owned sections: Summary (4 to 6 bullets), AI conversations by agent, Code, Meetings and email, Open loops. One line per item, with a link when one exists.

Then fill the **Sources** table. Every enabled source gets a row with one of:

- `N items`
- `no sessions found in window` plus the path you searched and the file count the extractor printed
- `failed: <short reason>`
- `not enabled`

Never leave a source out. If every source was empty, write one line saying nothing notable happened (`quiet_day: one_line`), still with the Sources table. If sources failed, say that too. A thin log with no explanation is a bug.

If the note exists, keep everything outside the markers and replace only the generated block.

## 6. Final redaction pass and write

Write the draft to a temp file. Run `python3 scripts/redact.py --config-dir <config dir> < draft > final`, then run `python3 scripts/redact.py --config-dir <config dir> --check < final`. If the check exits non-zero, stop and report. Write `final` to `notes.vault/<notes.daily_dir>/<filename>`. Apply any other rule from `rules.md`.

## 7. Weekly rollup (optional)

If `weekly_rollup.enabled` and the covered day is the configured day (default Friday), write the rollup to `notes.weekly_dir` from that week's daily notes, using [references/templates/weekly-rollup.md](references/templates/weekly-rollup.md): themes, shipped work, decisions, open loops, and a link to each day. Same redaction pass.

## 8. Git (optional)

Only if `git.commit` is true and the vault is a git repo: `git add -- <the note path and the rollup path>`, then `git commit -m "Daily log YYYY-MM-DD" -- <those paths>`. Never stage anything else, including the user's uncommitted edits. Push only if `git.push` is true. If a pull or rebase conflicts, abort it and report.

## 9. Report

Reply with the note path, a one-line summary, and any source that failed or was empty. Stay quiet otherwise if the scheduler is configured to deliver only problems.

## Notes

- The wiki is a separate step. The `wiki-synthesis` skill reads these logs weekly. Do not write wiki pages here.
- Sessions can hold secrets. The redaction script is a safety net, not a guarantee. Look at your first few notes before you trust the schedule.
