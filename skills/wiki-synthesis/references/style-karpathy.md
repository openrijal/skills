# Style: Karpathy's LLM wiki

Source: Andrej Karpathy, "LLM Wiki" idea file (a GitHub gist, checked 2026-11):
https://gist.github.com/karpathy/442a6bf555914893e9891c11519de94f

The gist describes a pattern, not a fixed layout. This file is one reading of it for daily logs. Adjust it with the user's schema file.

## What the gist says (summarized)

- Three layers. **Raw sources** are immutable and are read, never modified. **The wiki** is a folder of LLM-written Markdown (summaries, entity pages, concept pages, an overview) that the LLM owns. **The schema** is a file such as `CLAUDE.md` or `AGENTS.md` that tells the LLM the conventions and workflows.
- Three operations. **Ingest** a source: write a summary, update the index, update the entity and concept pages it touches, append to the log. **Query** the wiki and file good answers back as pages. **Lint** periodically for contradictions, stale claims, orphan pages, and missing pages or links.
- Two special files. `index.md` is a catalog of every page with a link and a one-line summary, grouped by category. `log.md` is append-only, with entries like `## [2026-04-02] ingest | Title` so `grep "^## \[" log.md | tail -5` works.

## How it maps here

| Gist idea | In this repo |
| --- | --- |
| Raw sources | The daily and weekly logs in `4-Archives/Logs/`. Read only. |
| The wiki | `5-Wiki/` |
| The schema | The vault's `AGENTS.md` (the daily-log skill ships `references/templates/AGENTS.iparaw.md`) plus this file |
| Ingest | One synthesis run: all logs since the last run |
| Query, lint | Lint runs each time (report only). Query is outside this skill. |

## Layout

```
5-Wiki/
  index.md
  log.md
  entities/    one page per person, organization, or tool
  projects/    one page per project
  decisions/   one page per decision, named YYYY-MM-DD-short-title.md
  concepts/    optional: recurring themes and ideas
```

## Page shape

Use `templates/wiki-page-karpathy.md`. A page has frontmatter (`type`, `aliases`, `sources` as a list of daily notes), a short summary, then sections as needed. Every statement that came from a log links to it. All agent text sits inside `<!-- wiki:start -->` and `<!-- wiki:end -->`.

## Ingest checklist (per run)

1. Read new logs. 2. Write or update pages. 3. Update `index.md`. 4. Append to `log.md`. 5. Report lint findings.

A single run can touch many pages. That is expected. Keep each edit small and sourced.
