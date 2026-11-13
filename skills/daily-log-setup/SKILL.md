---
name: daily-log-setup
description: >-
  One-time interview that sets up a daily log for one person: note tool and vault
  layout (Obsidian, Logseq, plain Markdown; PARA or IPARAW), daily-note template,
  agent sessions, connectors (Slack, Jira, GitHub, calendar, email), wiki style,
  and personal rules. Writes a config and a rules file, installs the daily-log
  skills, and schedules the runs. Use when someone wants a daily log or work
  journal set up.
license: MIT
compatibility: Works in any agent that can ask questions, read and write files, and run shell commands. Needs the daily-log skill installed alongside it. Python 3 recommended.
metadata:
  author: Nitesh Rijal
  version: "0.1.0"
---
# Daily log setup

Run this once per person. It asks questions, writes two files (a config and a rules file) **outside** the skill folders, and schedules the nightly run. The `daily-log` skill reads those files every day. Because they live outside the skill folder, updating the skills never overwrites your answers.

Ask **one question per message**, in order, and wait for each answer. Use the platform's choice UI if it has one. Propose a default for each question. Record each answer as you go. Do not skip a question because you think you know the answer.

## Before you start

1. Confirm the `daily-log` skill is installed next to this one (the same skills folder). Its `references/` folder holds the templates and scheduler examples you will use. If it is missing, tell the user to run `npx skills add openrijal/skills --skill '*'` or copy the `daily-log` folder from the repo, then continue.
2. Check Python: `python3 --version`. The runner uses it for redaction. If it is missing, tell the user and continue. The runner then redacts by eye, which is weaker.
3. **Never** create, move, rename, or delete anything in the user's notes before a clear yes for that specific change.

## Question 1: Note tool, then vault layout

**1a. Note tool.** Ask which they use: Obsidian, Logseq, plain Markdown files, or another tool.
- Obsidian: ask for the vault path and check it exists and holds `.obsidian/`. Read `.obsidian/daily-notes.json` or the Periodic Notes plugin data for the daily folder, date format, and template path, and offer those as defaults.
- Logseq: ask for the graph folder. Daily notes are in `journals/`.
- Plain Markdown: ask for a folder. Default `~/daily-log/`.
- Another tool (Notion, Google Docs): say the log works best as local Markdown. Offer a local folder, and a manual copy into their tool.
- No tool yet: suggest Obsidian (free, local Markdown, https://obsidian.md) or a plain folder. Install nothing without a yes.

**1b. Vault layout.** Ask which layout they want. Explain each in one line:

| Layout | Folders | When to pick it |
| --- | --- | --- |
| **Keep mine** | Whatever exists | You already have a system. The log goes in one folder you name. |
| **PARA** (default for a new vault) | `1-Projects`, `2-Areas`, `3-Resources`, `4-Archives` | Projects, Areas, Resources, Archives. Logs go in `4-Archives/Logs/`. |
| **IPARAW** (the author's variant) | `0-Inbox`, `1-Projects`, `2-Areas`, `3-Resources`, `4-Archives`, `5-Wiki` | PARA with an Inbox in front and a Wiki at the end. See below. |
| **Plain folder** | One folder | No structure, just dated files. |

Present IPARAW as **the variant the author uses, and why**, not as a standard:

- `0-Inbox` holds incoming ideas, drafts, and anything else that needs a human to review it. Agents may drop drafts there. Agents never treat Inbox content as settled, never synthesize it into the Wiki until a person has moved it out, and never write daily logs there.
- Daily synthesis notes go under `4-Archives/Logs/`. They are evidence, so they live with the archives.
- `5-Wiki` is distilled from those logs later (see Question 6). The point: capture is cheap, review is human, and durable knowledge is built from evidence.

**Scaffolding rules.** If the chosen layout needs folders that do not exist, list exactly which folders and files you would create, and ask. Only after a yes:

- Create **missing** folders only.
- Never move, rename, or delete an existing file or folder.
- Never overwrite an existing `AGENTS.md` or `README.md`. If one exists, offer to write the guide to `AGENTS.suggested.md` instead, and let the user merge it.
- Offer the vault guide from the `daily-log` skill: `references/templates/AGENTS.para.md` or `AGENTS.iparaw.md`. Create it only if no `AGENTS.md` exists and the user says yes.

Record: `notes.tool`, `notes.vault`, `notes.layout`, `notes.daily_dir`, `notes.weekly_dir`.
Defaults: PARA and IPARAW use `4-Archives/Logs/Daily` and `4-Archives/Logs/Weekly`. Plain uses `<folder>/`.

## Question 2: Daily-note template

Ask whether they have a template.
- **Yes:** read it. Keep its headings and frontmatter exactly. Ask which sections the agent may fill and which are theirs alone. Agent text goes between `<!-- daily-log:start -->` and `<!-- daily-log:end -->`.
- **No:** show `references/templates/daily-note.md` from the `daily-log` skill and offer changes.

Ask the filename format. Default `YYYY-MM-DD.md`.

## Question 3: Agent sessions

Ask whether the log should read their AI agent sessions. If yes, ask which agents and **verify every path with a real listing**. Never guess one. Use `daily-log/references/session-sources.md` for the known locations and formats, and its **checked** or **unverified** stamps.

For each agent: list the folder, show the path and a count of recent session files, and get a yes before saving it. For Claude Code and Codex, run the extractor on one recent file to prove it returns text:

```bash
python3 <daily-log>/scripts/extract_sessions.py claude "<path>/**/*.jsonl" --since <yesterday ISO> --until <today ISO> | python3 <daily-log>/scripts/redact.py | head
```

If a path is unverified (Hermes, OpenClaw, Cursor, others), say so, inspect the real format, and save it only as `verified: false`. Hosted assistants have no files. Use their transcript tool if the agent has one.

Ask how far back to read (default: the previous day) and which projects or folders are off limits.

## Question 4: Connectors and CLIs

Ask whether the log may use connectors or CLIs. Ask about these by name, one at a time:

- **Slack:** a Slack MCP, or none. Which channels, whether DMs are allowed, and whether to read only their own messages and mentions.
- **Jira:** an Atlassian MCP or `acli`. Which projects, and whether to read only issues assigned to or updated by them.
- **GitHub:** an MCP or `gh`. Which orgs or repos, and whether to include PRs authored, PRs reviewed, issues, and commits.
- **Calendar, email, git logs in local repos**, and anything else (Linear, Notion).

For each one they allow, check it works now (`gh auth status`, a cheap read through the MCP) and report what failed and how to fix it. Say plainly that the log is **read-only**: it never posts, comments, transitions, or sends. For email, say that only threads with real people are used and bodies are summarized, never copied.

## Question 5: Other rules

Ask whether they have other rules, and offer examples to adopt or change (see `references/templates/rules.example.md`): first person and short sentences, links instead of pasted content, keep personal items out, weekend handling, carry unchecked items forward, quiet-day behavior, weekly rollup on Friday, commit the notes after writing, and a **deny-list** of names, projects, or customers that must never appear in a note.

Write their answers **in their own words** to `rules.md`. Do not compress it into YAML. The runner reads it word for word. Put deny-list entries in `deny.txt`, one per line (a literal, or `re:<regex>`).

## Question 6: Memory and wiki style (only for IPARAW, or any layout with a wiki folder)

Skip this if the layout has no wiki folder and the user does not want one.

Explain: the daily logs are evidence. A weekly synthesis can distill them into wiki pages (people and organizations, projects, decisions, an index, and a log). Ask which style they want:

1. **Karpathy's LLM wiki.** Raw sources (the logs) stay untouched. An LLM maintains a folder of Markdown pages plus `index.md` and an append-only `log.md`, following a schema file. Operations: ingest, query, lint. Source: https://gist.github.com/karpathy/442a6bf555914893e9891c11519de94f
2. **Garry Tan's GBrain style.** Each page has "compiled truth" on top (the current state, rewritten as things change) and an append-only timeline below. Filing follows a resolver so each fact has one home. Only the page style is used here, not the GBrain software. Source: https://github.com/garrytan/gbrain
3. **Skip the wiki for now.** The logs still work. Add it later.

Say what both options share: only logs in `4-Archives/Logs/` are read, never the Inbox. Agents write only inside `<!-- wiki:start -->` markers, never delete your text, link every claim to its daily note, and run the same redaction pass. The default schedule is weekly on Sunday.

Record `wiki.enabled`, `wiki.style` (`karpathy`, `gbrain`, or `none`), `wiki.dir` (default `5-Wiki`), and `wiki.inbox_dir`. If they pick a style and the wiki folder lacks `index.md` and `log.md`, offer to create them from the `wiki-synthesis` skill's `references/templates/`, with the same no-overwrite rules. For the GBrain style, also offer `RESOLVER.md`. Make sure the `wiki-synthesis` skill is installed.

## Phase 2: Write the config

Ask where to keep the config, and record the choice:

- `<vault>/.daily-log/`: travels with the vault. Warn that this folder is inside the vault. If the vault is a git repo that will be public or shared, it will not be ignored by default, so offer to add `.daily-log/` to `.gitignore`.
- `~/.config/daily-log/`: stays on this machine, outside any repo.

Write `daily-log.config.yaml`, `rules.md`, and `deny.txt` there, starting from `references/templates/daily-log.config.example.yaml` in the `daily-log` skill. Set `git.push` to `false` unless they said yes to pushing. Show the finished files and apply their edits. If a config already exists, show a diff, back the old one up as `*.bak`, and only overwrite after a yes.

## Phase 3: Install the skills

Prefer the CLI, which asks which agents and scope:

```bash
npx skills add openrijal/skills --skill daily-log --skill daily-log-setup --skill wiki-synthesis
# global (all projects):        add -g
# one agent:                    add -a claude-code   (or codex, cursor, hermes-agent, openclaw, ...)
```

Or copy the three folders by hand into the agent's skills folder. Known folders (from the `skills` CLI docs, checked 2026-11):

| Agent | Project | Global |
| --- | --- | --- |
| Claude Code | `.claude/skills/` | `~/.claude/skills/` |
| Codex | `.agents/skills/` | `~/.agents/skills/` |
| Cursor | `.agents/skills/` | `~/.cursor/skills/` |
| Hermes Agent | `.hermes/skills/` | `~/.hermes/skills/` |
| OpenClaw | `skills/` | `~/.openclaw/skills/` |
| Grok Bot | use the product's skill library | |

Ask: global, one project, or one agent only. Warn that a project install may be committed, and that the skills hold no personal data (the config does, and it lives elsewhere). Read the installed `SKILL.md` back to confirm it landed.

## Phase 4: Schedule

Read `daily-log/references/schedulers.md`. Check what this runtime and OS can schedule. Ask what time, in their timezone (suggest 00:30 for the previous day, or end of workday), and weekdays or every day. If they chose a wiki, ask for the synthesis time (default Sunday 03:00).

Before scheduling:

1. **Do a dry run now.** Run the `daily-log` skill once for yesterday, show the note, and let them check it for private details and secrets. Fix the rules and deny-list if anything slipped through.
2. Warn: **never use skip-permissions flags** in a scheduled command, and prefer read-only or allow-listed tool permissions for headless runs. Show the exact command from `schedulers.md` with their paths filled in.
3. Create the schedule only after a yes. Report the exact schedule, the command, and the next run time. If nothing on this machine can schedule a run, say so and explain how to run the skill by hand.

## Don'ts

- Do not ask more than one question per message.
- Do not save a path or connector you have not checked yourself.
- Do not install software, write outside the chosen folders, or create a schedule without a yes.
- Do not commit or push anything.
- Do not move, rename, or overwrite the user's files.
