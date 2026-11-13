# skills

Three agent skills for keeping a daily log and turning it into a wiki. This is a reference repo: it shows how the author does it, and it works if you want to copy it.

- **daily-log-setup**: a one-time interview. It asks about your notes tool, vault layout, agent sessions, connectors, and rules, writes your config, installs the skills, and sets a schedule.
- **daily-log**: the runner. Each night it reads your agent sessions and other sources, redacts secrets, and writes one note for the day.
- **wiki-synthesis**: a weekly step. It reads the new daily logs and updates a wiki (entities, projects, decisions, an index) in the style you picked.

The skills follow the open [Agent Skills](https://agentskills.io/specification) format. They run in any agent that supports it. They schedule wherever your runtime or your OS can.

## Install

With the [`skills`](https://github.com/vercel-labs/skills) CLI (needs Node.js 22.20 or later):

```bash
npx skills add openrijal/skills --list                 # see what is in the repo
npx skills add openrijal/skills --skill '*'            # install all three
npx skills add openrijal/skills --skill daily-log -g -a claude-code   # one skill, global, one agent
```

Or copy by hand. Each folder in `skills/` is a complete skill. Put the folders in your agent's skills folder:

| Agent | Project folder | Global folder |
| --- | --- | --- |
| Claude Code | `.claude/skills/` | `~/.claude/skills/` |
| Codex | `.agents/skills/` | `~/.agents/skills/` |
| Cursor | `.agents/skills/` | `~/.cursor/skills/` |
| Hermes Agent | `.hermes/skills/` | `~/.hermes/skills/` |
| OpenClaw | `skills/` | `~/.openclaw/skills/` |

Folders come from the `skills` CLI's agent table. Install all three skills, because they share templates and scripts.

## Quick start

1. Tell your agent: "Run the daily-log-setup skill."
2. Answer the questions, one at a time. It never changes your notes without a yes.
3. Look at the dry-run note it writes for yesterday. Check it for anything private.
4. Accept the schedule it proposes, or schedule it yourself with [`schedulers.md`](skills/daily-log/references/schedulers.md).

Your answers go in `daily-log.config.yaml`, `rules.md`, and `deny.txt`, in `<vault>/.daily-log/` or `~/.config/daily-log/`. That folder is outside the skills, so `npx skills update` replaces skill files without touching your config.

## Vault layouts

Setup asks which you want. It only creates folders that are missing, never moves or renames files, and never overwrites an existing `AGENTS.md` or `README.md`.

- **Keep yours.** The log goes in one folder you name.
- **PARA** (the default for a new vault): `1-Projects`, `2-Areas`, `3-Resources`, `4-Archives`. Logs go in `4-Archives/Logs/`.
- **IPARAW**, the variant the author uses: PARA with an Inbox in front and a Wiki at the end.
- **A plain folder.**

Why IPARAW:

```
0-Inbox/      incoming ideas, drafts, and anything else that needs a human to review it
1-Projects/
2-Areas/
3-Resources/
4-Archives/   generated logs live here, in 4-Archives/Logs/
5-Wiki/       distilled from the logs, later
```

Agents may drop drafts or ideas into the Inbox for review. They never treat Inbox content as settled. They never synthesize it into the Wiki until a person has moved it out. They never write daily logs there. Logs are evidence, so they go to the Archives, and the Wiki is distilled from them on a schedule. Capture is cheap, review is human, and durable notes come from evidence.

## Wiki styles

If you pick IPARAW, or any layout with a wiki folder, setup asks for a style. The `wiki-synthesis` skill reads logs written since the last synthesis and updates or creates pages. It runs weekly, by default on Sunday.

1. **Karpathy's LLM wiki.** Raw sources stay untouched. The model maintains Markdown pages, an `index.md`, and an append-only `log.md`, guided by a schema file. [Source](https://gist.github.com/karpathy/442a6bf555914893e9891c11519de94f).
2. **Garry Tan's GBrain style.** Each page has current "compiled truth" above a rule and an append-only timeline below, filed by a resolver. Only the page style is used, not the GBrain software. [Source](https://github.com/garrytan/gbrain).
3. **None.** The logs work on their own.

In both styles, the synthesis links every claim to its daily note, writes only between `<!-- wiki:start -->` and `<!-- wiki:end -->`, never deletes your text, and uses the same redaction pass.

## Sample

From [`examples/sample-vault`](examples/sample-vault). Everything in it is fictional.

```markdown
# 2026-03-10 (Tuesday) Daily Log

## Summary
- Fixed the retry backoff bug in Widget API and opened a PR for review.
- Decided to keep the queue on the existing worker pool instead of adding a second service.

## Code
- PR opened: [Cap retry jitter and add regression test](https://github.com/example-org/widget-api/pull/42)

## Sources
| Source | Result |
| --- | --- |
| Claude Code | 2 sessions, 14 messages |
| Slack | not enabled |
```

The Sources table is required. If a source returns nothing, the note says so and names the path it searched. The runner never quietly writes a thin log.

## Tested runtimes

Honest status. "Checked" means the file formats and command flags were compared against the installed version and the docs. No runtime has run this on a schedule for a full week in this repo.

| Runtime | Status | Notes |
| --- | --- | --- |
| Claude Code | Tested by design | Session format checked against 2.1.322. Headless flags checked against `claude --help` and the docs. |
| Codex CLI | Tested by design | Session format checked against codex-cli 0.167.1. `codex exec` flags checked against `--help`. |
| Grok Bot | Tested by design | Reads its own transcripts with built-in tools, so it needs no session path. Uses its routines for scheduling. |
| Hermes Agent | Untested | Scheduling command checked against 0.22.7 `--help`. Session store is a SQLite file, schema not inspected. |
| OpenClaw | Untested | Scheduling command checked against 2026.10.10 `--help`. Session location not found. |
| Cursor, Gemini CLI, Aider, others | Untested | Contributions welcome. |

If you get one working, open a pull request with the version you tested and what you changed in [`session-sources.md`](skills/daily-log/references/session-sources.md).

## Safety

Session history is full of pasted keys, tokens, and private work. Treat this tool with care.

- **Read-only.** The runner never posts, sends, comments, or changes anything outside your notes folder.
- **Redaction.** All session and chat text goes through [`redact.py`](skills/daily-log/scripts/redact.py) before it reaches a note. It masks common key and token formats, private key blocks, `password=` style lines, long random strings, and your own deny-list. It errs on the side of masking, so it may hide harmless text such as `password: required`. It keeps git SHAs, UUIDs, and URLs.
- **It is a safety net, not a guarantee.** Look at your first few notes. Add names, projects, and customers to `deny.txt`.
- **Filtered input.** The extractor keeps only user and assistant text. System prompts, tool output, and hidden reasoning never reach the note.
- **No skip-permissions flags.** Scheduled runs should use read-only or allow-listed tools. The examples in `schedulers.md` do.
- **Git is opt-in.** The runner commits only the note paths, and pushes only if you set `git.push: true` yourself.
- **Never share your config folder or your notes** without reading them first.

## Tests

```bash
python3 -m unittest discover -s tests -v
```

The redaction test uses fake secrets of each type. Each one has a `<<>>` marker spliced in, so no scannable key sits in the repo. The test removes the marker, checks the secret is present, runs the redactor, and checks nothing survives. Other tests check that git SHAs, URLs, and UUIDs stay, that the extractor drops system prompts and tool output, and that every `SKILL.md` follows the spec.

## Layout

```
skills/
  daily-log-setup/SKILL.md
  daily-log/
    SKILL.md
    scripts/        redact.py, extract_sessions.py
    references/     session-sources.md, schedulers.md, templates/
  wiki-synthesis/
    SKILL.md
    scripts/        redact.py (a copy, checked by a test)
    references/     style-karpathy.md, style-gbrain.md, templates/
examples/sample-vault/   fictional demo vault (IPARAW)
tests/
```

## License

MIT. Copyright (c) 2026 Nitesh Rijal.
