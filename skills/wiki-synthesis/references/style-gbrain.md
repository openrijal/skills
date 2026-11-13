# Style: Garry Tan's GBrain

Source: Garry Tan's open-source GBrain (MIT), checked 2026-11:
- Repo and README: https://github.com/garrytan/gbrain
- Recommended schema: https://github.com/garrytan/gbrain/blob/master/docs/GBRAIN_RECOMMENDED_SCHEMA.md
- Page anatomy: https://github.com/garrytan/gbrain/blob/master/docs/guides/page-anatomy.md

GBrain is real software (a Markdown folder plus a database index, CLI, and cron jobs). This repo does **not** need it. This skill borrows only the page style and the filing discipline, which work in plain Markdown. The schema doc says GBrain extends Karpathy's wiki pattern into an operational knowledge base.

## What GBrain's docs say (summarized)

- **Compiled truth plus timeline.** Every page has two layers separated by a horizontal rule. Above the line is the current state: a one-paragraph summary, state fields, open threads, and see-also links, rewritten when new information arrives. Below the line is an append-only, reverse-chronological timeline of dated evidence, each entry with a source.
- **One primary home per fact.** Directories are mutually exclusive. Each directory has a `README.md` that says what goes there and what does not, and a top-level `RESOLVER.md` is a decision tree for filing. Unsorted items go to an inbox, which signals the schema needs to grow.
- **Timeline row format.** `- **YYYY-MM-DD** | Source - Summary`.
- **Empty sections stay.** A section with no data says `[No data yet]`, which tells the next run what to look for.
- **Corrections are the most valuable data.** If the user corrects something, write it down right away.
- **Typed links and backlinks** between pages. Facts carry sources.

## How it maps here

- GBrain's `inbox/` is **not** used. In IPARAW, the Inbox is for human review and is never synthesized. Items that do not fit anywhere are listed in the run report instead.
- The person pages are optional and sensitive. Create a person page only for people the user writes about repeatedly, and keep it to work-relevant facts the logs state. Never write personal details about third parties that the user did not record.
- No database, embeddings, or enrichment APIs are used. This skill only reads logs and writes Markdown.

## Layout

```
5-Wiki/
  RESOLVER.md      decision tree for where a thing is filed (write it once, then follow it)
  index.md         catalog of every page, one line each
  log.md           append-only run log
  people/          README.md = resolver for this folder
  organizations/
  projects/
  decisions/
  concepts/
```

Start with only the folders the logs need. Create each folder's `README.md` resolver when you create the folder.

## Page shape

Use `templates/wiki-page-gbrain.md`: frontmatter, compiled truth above a `---` rule, timeline below. The compiled truth block is rewritten each run, inside the wiki markers. The timeline is only appended to. A timeline entry always links to the daily note.

When a new claim contradicts the compiled truth: strike the old claim, state the new one, and add a timeline entry that says what changed and links the log.

## Ingest checklist (per run)

1. Read `RESOLVER.md` before creating any page. 2. For each entity or project in the new logs, find its page (check aliases) or create it. 3. Rewrite compiled truth if the logs changed it. 4. Append timeline entries. 5. Update `index.md` and `log.md`. 6. Report lint findings.
