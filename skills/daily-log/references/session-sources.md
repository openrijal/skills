# Session sources

Where each agent keeps its history, and how to read it. Each entry carries a stamp:

- **checked** means the author looked at real files from that version and the layout matched.
- **unverified** means the layout comes from docs or guesswork. Check it with a real listing before you trust it.

These formats are undocumented and change between versions. If a path or field is wrong on your machine, fix it in your config and open an issue or PR with the new version.

## Rules for every source

1. List the path first. Never save or read a path you have not seen with your own eyes.
2. Read only user and assistant text. Session files also hold system prompts, tool schemas, tool output, hidden reasoning, and pasted environment dumps.
3. Pipe everything through `scripts/redact.py` before it enters your notes or your context.
4. If a source returns nothing for the window, say so in the note ("no sessions found in ~/.claude/projects for this window"). A quiet source and a broken source look the same until you check the file count.

`scripts/extract_sessions.py` does steps 2 and 4 for the two formats below that are marked checked.

## Claude Code

- Checked against Claude Code 2.1.322, 2026-11.
- Path: `~/.claude/projects/<encoded-project-path>/<session-id>.jsonl`, one JSON object per line.
- Keep: records with `type` of `user` or `assistant`. Use `message.content` text blocks only (`content` is a string or a list of blocks).
- Skip: `thinking` and `tool_use` and `tool_result` blocks, plus these record types: `attachment`, `queue-operation`, `api-request-shape`, `api-request-blob` (these two hold full system prompts and tool schemas), `custom-title`, `session-owner`.
- Useful fields: `timestamp` (ISO, UTC), `cwd`, `sessionId`, `gitBranch`, `isSidechain` (subagent turns; skipped).
- Run: `python3 scripts/extract_sessions.py claude "~/.claude/projects/**/*.jsonl" --since <ISO> --until <ISO> | python3 scripts/redact.py`

## Codex CLI

- Checked against codex-cli 0.167.1, 2026-11.
- Path: `~/.codex/sessions/<YYYY>/<MM>/<DD>/rollout-*.jsonl`.
- Keep: `type: response_item` with `payload.type: message` and `payload.role` of `user` or `assistant`. Text is in `payload.content[].text` (`input_text` or `output_text`).
- Skip: `payload.role: developer` (harness prompts), `custom_tool_call` and other tool items, `event_msg`, `world_state`, `turn_context`, `token_usage_record`. The first user messages often contain injected `AGENTS.md` and environment text. The extractor drops those.
- Run: `python3 scripts/extract_sessions.py codex "~/.codex/sessions/**/*.jsonl" --since <ISO> --until <ISO> | python3 scripts/redact.py`

## Hermes Agent

- Checked: version 0.22.7 installed, 2026-11. Session location and schema: **unverified**.
- `~/.hermes/state.db` is a SQLite file and `~/.hermes/sessions.json` exists. The schema was not inspected.
- To use it: copy `state.db` to a temp file, open the copy read-only, run `.schema`, find the messages table, and confirm with a real row count before adding it to your config. Prefer the `hermes` CLI's own session listing if your version has one.

## OpenClaw

- Checked: version 2026.10.10 installed, 2026-11. Session location: **unverified**.
- Agent state lives under `~/.openclaw/agents/<id>/`. No JSONL session folder was found there. Its docs say job state is in a SQLite database. Find the real location with `openclaw --help` and a directory listing.

## Cursor

- **Unverified.** Editor chat history lives in the editor's `workspaceStorage` SQLite files (macOS: `~/Library/Application Support/Cursor/User/workspaceStorage/`, Linux: `~/.config/Cursor/User/workspaceStorage/`). The schema changes often. Treat as experimental.

## Gemini CLI, Aider, others

- **Unverified.** Gemini CLI keeps logs under `~/.gemini/tmp/`. Aider writes `.aider.chat.history.md` in each repo. Neither was inspected.

## Hosted assistants (Grok Bot, ChatGPT, Claude.ai)

- No local files. Use the platform's own transcript or history tool if your agent has one. If it has none, mark the source "not readable" in your config.
- A Grok Bot agent reads its own transcripts with its transcript tools, which is how the Grok Bot setup avoids file paths entirely.

## Paths with a lot of files

Some tools keep thousands of cache and worktree files next to their history. Read only the known history path. Never walk the whole tool directory.
