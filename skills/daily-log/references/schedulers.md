# Scheduling the daily run

Pick one scheduler. The skill itself works anywhere. Only the scheduling differs.

Read these first:

- **Never use skip-permissions flags.** That means `claude --dangerously-skip-permissions`, `codex --dangerously-bypass-approvals-and-sandbox`, or `--sandbox danger-full-access`. The log needs to read history and write one note. It does not need your whole machine.
- **Prefer read-only or allow-listed tools.** The examples below allow only reads, one write location, and the git commands for the note.
- **Run it once by hand first.** A headless run cannot answer a permission prompt. Run the command in a terminal, see which prompts appear, and add those to the allow list.
- **Pass the config location.** The runner finds its config from `DAILY_LOG_CONFIG_DIR`, then `~/.config/daily-log/`, then `./.daily-log/` in the working directory. In a scheduled job, set the variable.
- **Timezone.** Cron on a laptop uses the machine's timezone. Hosted schedulers often use UTC. Set it explicitly where the tool allows.
- **Log output** to a file so you can see why a night failed.

Replace `VAULT` with your notes folder and `CFG` with your config folder in every example.

## What was checked

| Tool | Version checked | What was checked |
| --- | --- | --- |
| Claude Code | 2.1.322 | flags in `claude --help`, headless docs |
| Codex CLI | 0.167.1 | flags in `codex exec --help`, non-interactive docs |
| Hermes Agent | 0.22.7 | `hermes cron create --help`, cron docs |
| OpenClaw | 2026.10.10 | `openclaw cron create --help`, cron docs |
| Grok Bot routines | n/a | not checked against a public doc; it is the product's own feature |
| systemd timer | n/a | the `OnCalendar` expression was parsed with `systemd-analyze calendar` |
| launchd | n/a | the plist parses as a valid property list; it was not loaded into launchd |
| cron, Task Scheduler | n/a | standard syntax, not run |

No scheduler here has been run end to end in this repo for a full week. Treat them as starting points.

## Claude Code (headless)

```bash
cd VAULT && DAILY_LOG_CONFIG_DIR=CFG claude -p "/daily-log" \
  --permission-mode dontAsk \
  --add-dir ~/.claude/projects \
  --allowedTools "Read,Write,Edit,Bash(python3 *),Bash(git add *),Bash(git commit *),Bash(git status *)"
```

- `dontAsk` denies anything not on the allow list. Do not add `Bash` alone.
- Do not use `--bare`. It skips skill discovery, so `/daily-log` will not load.
- `--permission-prompts none` (Claude Code 2.1.259 or later) tells the model not to retry denied calls. It is optional.
- Claude Code's own scheduling is separate from this. Use cron, launchd, or systemd below to call the command.

Source: https://code.claude.com/docs/en/headless

## Codex CLI

```bash
codex exec --sandbox workspace-write --cd VAULT --add-dir ~/.codex/sessions \
  --skip-git-repo-check "Use the daily-log skill. Config folder: CFG"
```

- `codex exec` is read-only by default. Writing the note needs `--sandbox workspace-write`.
- `--skip-git-repo-check` is only needed if the vault is not a git repo.
- To read history in `~/.codex/sessions`, that folder may need to be readable from the sandbox. Test it. If the sandbox blocks the read, run the extractor outside the agent (see "Split the work" below).
- Mention the skill by name in the prompt. Codex can also pick it from the description.

Source: https://developers.openai.com/codex/noninteractive

## Hermes Agent

```bash
hermes cron create "30 0 * * *" \
  "Run the daily-log skill for yesterday. Config folder: CFG" \
  --name "Daily log" --skill daily-log --workdir VAULT --deliver local
```

- Use cron syntax. The docs say natural-language schedules such as "daily at 9am" are not reliable in the standalone CLI.
- Hermes cron jobs start fresh sessions with no memory, so the prompt must stand alone.
- Hermes also has its own installer: `hermes skills install`. Its skills folder is `~/.hermes/skills/`.

Source: https://hermes-agent.nousresearch.com/docs/user-guide/features/cron

## OpenClaw

```bash
openclaw cron create "30 0 * * *" \
  "Run the daily-log skill for yesterday. Config folder: CFG" \
  --name "Daily log" --tz "America/Chicago" --no-deliver
```

- Always pass `--tz`. Without it, cron expressions use the gateway host's timezone.
- `openclaw automations` is an alias for `openclaw cron`.
- Recurring top-of-hour jobs are staggered by up to 5 minutes unless you pass `--exact`.
- Needs `operator.admin` to create jobs.

Source: https://docs.openclaw.ai/cli/cron

## Grok Bot routines

Ask the bot: "Run the daily-log skill every night at 12:30 AM my time, covering the previous day. Stay quiet unless a source or the git step failed."

The bot creates a routine in your timezone. Grok Bot agents can read their own transcripts with built-in tools, so the Grok Bot source needs no file path. Other bots in the same account can run the same skill.

## cron (Linux, macOS)

```cron
CRON_TZ=America/Chicago
30 0 * * * cd VAULT && DAILY_LOG_CONFIG_DIR=CFG /usr/local/bin/claude -p "/daily-log" --permission-mode dontAsk --add-dir ~/.claude/projects --allowedTools "Read,Write,Edit,Bash(python3 *),Bash(git add *),Bash(git commit *),Bash(git status *)" >> ~/.local/state/daily-log.log 2>&1
```

- Use absolute paths. Cron has a tiny `PATH`.
- `CRON_TZ` works in cronie and some other crons, not all. Check your `man 5 crontab`.
- On macOS, cron jobs may lack permission to read some folders. Prefer launchd.

## launchd (macOS)

Save as `~/Library/LaunchAgents/com.example.daily-log.plist`, then `launchctl load ~/Library/LaunchAgents/com.example.daily-log.plist`.

```xml
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0"><dict>
  <key>Label</key><string>com.example.daily-log</string>
  <key>ProgramArguments</key><array>
    <string>/bin/sh</string><string>-c</string>
    <string>cd VAULT &amp;&amp; DAILY_LOG_CONFIG_DIR=CFG /usr/local/bin/claude -p "/daily-log" --permission-mode dontAsk --add-dir ~/.claude/projects --allowedTools "Read,Write,Edit,Bash(python3 *),Bash(git add *),Bash(git commit *),Bash(git status *)"</string>
  </array>
  <key>StartCalendarInterval</key><dict><key>Hour</key><integer>0</integer><key>Minute</key><integer>30</integer></dict>
  <key>StandardOutPath</key><string>/tmp/daily-log.out</string>
  <key>StandardErrorPath</key><string>/tmp/daily-log.err</string>
</dict></plist>
```

launchd uses the machine's local time. If the Mac is asleep at 00:30, the job runs when it wakes.

## systemd timer (Linux)

`~/.config/systemd/user/daily-log.service`:

```ini
[Unit]
Description=Daily log

[Service]
Type=oneshot
WorkingDirectory=VAULT
Environment=DAILY_LOG_CONFIG_DIR=CFG
ExecStart=/usr/local/bin/claude -p "/daily-log" --permission-mode dontAsk --add-dir %h/.claude/projects --allowedTools "Read,Write,Edit,Bash(python3 *),Bash(git add *),Bash(git commit *),Bash(git status *)"
```

`~/.config/systemd/user/daily-log.timer`:

```ini
[Unit]
Description=Daily log, nightly

[Timer]
OnCalendar=*-*-* 00:30:00 America/Chicago
Persistent=true

[Install]
WantedBy=timers.target
```

Enable with `systemctl --user enable --now daily-log.timer`. Check with `systemctl --user list-timers`. `Persistent=true` runs a missed job after wake. To run while logged out, run `loginctl enable-linger $USER`.

## Task Scheduler (Windows)

```powershell
$action  = New-ScheduledTaskAction -Execute "claude" -Argument '-p "/daily-log" --permission-mode dontAsk --add-dir "$env:USERPROFILE\.claude\projects" --allowedTools "Read,Write,Edit,Bash(python3 *),Bash(git add *),Bash(git commit *),Bash(git status *)"' -WorkingDirectory "VAULT"
$trigger = New-ScheduledTaskTrigger -Daily -At 12:30AM
Register-ScheduledTask -TaskName "DailyLog" -Action $action -Trigger $trigger
```

Set `DAILY_LOG_CONFIG_DIR` as a user environment variable first. Windows uses the machine's local time. Windows users should check that `python3` resolves, or use `py -3` in the allow list.

## Split the work (for sandboxes that block history reads)

If your agent cannot read the session folders, run the extractor in the scheduler and hand the agent the redacted text:

```bash
python3 SKILL_DIR/scripts/extract_sessions.py claude "~/.claude/projects/**/*.jsonl" \
  --since "$(date -d 'yesterday 00:00' --iso-8601=seconds)" --until "$(date -d 'today 00:00' --iso-8601=seconds)" \
  | python3 SKILL_DIR/scripts/redact.py --config-dir CFG > /tmp/daily-log-claude.txt
```

(`date -d` is GNU. On macOS use `gdate` from coreutils or compute the timestamps in Python.) Then tell the agent in the prompt: "Claude Code input is in /tmp/daily-log-claude.txt."
