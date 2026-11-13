---
name: wiki-synthesis
description: >-
  Turns daily log notes into a durable wiki: reads the logs written since the
  last synthesis and updates or creates entity, project, and decision pages plus
  an index and a log, in the style chosen at setup (Karpathy LLM wiki or a
  GBrain-style compiled-truth page). Use for the weekly wiki run, or when asked
  to distill the logs into the wiki. Never deletes user text.
license: MIT
compatibility: Needs file read and write access to a notes folder. Python 3 for scripts/redact.py. Git is optional.
metadata:
  author: Nitesh Rijal
  version: "0.1.0"
---
# Wiki synthesis

Daily logs are evidence. The wiki is what you distill from them: who and what keeps coming up, what was decided, what is still open. This skill reads new logs and keeps the wiki current. It is meant to run weekly, by default on Sunday.

It is built for the IPARAW layout (`4-Archives/Logs` feeds `5-Wiki`). It works with any layout that has a logs folder and a wiki folder.

## Before you start

1. Find the config the same way the `daily-log` skill does: `DAILY_LOG_CONFIG_DIR`, then `~/.config/daily-log/`, then `./.daily-log/`. Read `daily-log.config.yaml` and `rules.md` word for word.
2. Read `wiki.enabled`, `wiki.style`, `wiki.dir`, and the logs folder (`notes.daily_dir`, `notes.weekly_dir`). If `wiki.style` is `none` or the wiki is not enabled, stop and say so.
3. Read the wiki's own schema file (`AGENTS.md` in the vault root or `5-Wiki/SCHEMA.md`) if it exists. It wins over the defaults here.
4. Read the style file for the chosen style: [references/style-karpathy.md](references/style-karpathy.md) or [references/style-gbrain.md](references/style-gbrain.md).

If the config is missing, tell the user to run `daily-log-setup` and stop.

## Hard rules

- **Sources are the logs only.** Read daily and weekly logs under the logs folder. Never read `0-Inbox/` (or whatever `wiki.inbox_dir` names). Inbox content is unreviewed. A person must move it out before it can count.
- **Never write a daily log to the Inbox.** Logs go to the logs folder. If you want to suggest something for human review, drop a draft in the Inbox and say so in the run report. Never synthesize it in the same run.
- **Never delete user-written content.** Write only inside `<!-- wiki:start -->` and `<!-- wiki:end -->` markers. On a page a person wrote, append a marked block at the bottom and leave everything else untouched. Never delete a page, a line, or a link. A claim that new evidence overturns is struck through (`~~old claim~~`) and kept, with a note on what replaced it and a link.
- **Link every claim back** to the daily note it came from, as a wiki link or relative link to the dated file (for example `[[2026-11-09]]`).
- **Redact.** Pipe every page body you write through `python3 scripts/redact.py --config-dir <config dir>` first. If Python is unavailable, check by eye for keys, tokens, passwords, and private key blocks, and say in the run report that the scripted pass did not run.
- **Do not invent.** If the logs do not say it, it is not in the wiki. Say "unclear" and link the note.
- **Skip notes that opt out.** Skip any log whose frontmatter has `wiki: skip`. Respect `sources.off_limits` and `rules.md`.
- Never post, send, or change anything outside the vault. Never use skip-permissions flags.

## Steps

1. **Find the window.** Open `<wiki dir>/log.md`. The last line that starts with `## [YYYY-MM-DD] synthesis` records the last day covered. Read every daily log dated after that day, up to and including yesterday in the user's timezone. If there is no such entry, this is the first run: read the last 14 days and say so in the report. If there are no new logs, write nothing except a `log.md` line "no new logs", and stop.
2. **Read** the new logs, plus the wiki's `index.md` so you know which pages already exist.
3. **Extract** candidates from the logs: people and organizations, tools, projects, decisions, recurring themes, and open loops. Merge duplicates and aliases before creating anything. If a page may already exist under another name, update it.
4. **Update or create pages** as the style file says. Touch only what the logs support. Typical pages by type: entities, projects, decisions (with date, choice, reason, and what it replaced), and concepts if the style uses them.
5. **Update `index.md`**: one line per page, with a link and a one-line summary, grouped by type. Add new pages. Never remove a line a person wrote.
6. **Append to `log.md`**: one entry, `## [YYYY-MM-DD] synthesis | covered <first day> to <last day>`, then the list of pages created and updated and any unresolved items. Append only.
7. **Lint (light).** Report, do not fix: pages with no inbound link, claims with no source link, contradictions between pages, and logs that mention a name with no page. Put the findings under the log entry.
8. **Redact and write.** Run the redaction pass, then write the files.
9. **Git, if configured.** If `git.commit` is true and the vault is a git repo, stage only the wiki paths you changed (`git add -- <paths>`), commit with `Wiki synthesis YYYY-MM-DD`, and push only if `git.push` is true. Never stage other files. If anything conflicts, stop and report.
10. **Report** the covered window, pages created and updated, lint findings, and anything that needs a human (for example, a draft you left in the Inbox).

## Scheduling

Default: weekly on Sunday, after the Friday weekly rollup, for example 03:00 local. Scheduling examples for each runtime are in the `daily-log` skill's `references/schedulers.md`. Use the same pattern with the prompt "Run the wiki-synthesis skill. Config folder: <dir>" and a weekly cron expression such as `0 3 * * 0`.

## First run

Offer a dry run: do steps 1 to 7, print what you would write, and write nothing. Wait for a yes before writing.
