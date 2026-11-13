# Vault guide (IPARAW)

This vault uses IPARAW: PARA with an Inbox in front and a Wiki at the end.

## Folders
- `0-Inbox/`: incoming ideas, drafts, and anything else that needs a human to review it. Unsorted on purpose.
- `1-Projects/`: work with an end date or a goal.
- `2-Areas/`: ongoing responsibilities with no end date.
- `3-Resources/`: reference material and topics of interest.
- `4-Archives/`: finished or inactive items. Generated logs live in `4-Archives/Logs/`.
- `5-Wiki/`: distilled, durable notes, built from the logs by the wiki-synthesis skill or by a person.

## Inbox rules
- Agents may drop drafts, ideas, and open questions into `0-Inbox/` for a person to review.
- Agents never treat Inbox content as settled. It is unreviewed.
- Agents never synthesize Inbox content into `5-Wiki/`. Only a person moves a note out of the Inbox, and only then can it count.
- Agents never write daily logs to `0-Inbox/`. Logs go to `4-Archives/Logs/`.

## Daily logs
- Daily logs go in `4-Archives/Logs/Daily/YYYY-MM-DD.md`. Weekly rollups go in `4-Archives/Logs/Weekly/`.
- Daily logs are evidence, not wiki pages. Do not put daily digests in `5-Wiki/`.
- Agents write only inside the `<!-- daily-log:start -->` and `<!-- daily-log:end -->` markers of a note.
- Never rewrite text a person wrote.

## Wiki
- The wiki is distilled from `4-Archives/Logs/`. Every claim links back to the daily note it came from.
- Agents write only inside `<!-- wiki:start -->` and `<!-- wiki:end -->` markers. Text outside the markers belongs to a person.
- Agents never delete wiki pages or user-written lines. Outdated claims are struck through and kept.

## Rules
- Do not move, rename, or delete notes without being asked.
- Link instead of pasting. Keep private details out of anything shared.
- Commits and pushes happen only when the config allows them.
