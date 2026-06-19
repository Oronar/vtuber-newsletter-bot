# vtuber-newsletter-bot

A scheduled GitHub Action that generates a daily VTuber mini-newsletter with the
Claude API (web search enabled) and posts it to a Discord channel via webhook.

## How it works

`post_newsletter.py`:
1. Calls the Claude API (`claude-sonnet-4-6`) with the `web_search` tool to write a
   newsletter from the latest VTuber news.
2. Posts the result to a Discord webhook, encoded as ASCII-safe JSON (so emoji can't
   produce invalid-UTF-8 / "invalid JSON" errors) and split into <2000-char chunks.

`.github/workflows/newsletter.yml` runs it daily at 8:00 AM Eastern and can be
triggered manually from the **Actions** tab (**Run workflow**).

## Required setup

Add two repository secrets under **Settings -> Secrets and variables -> Actions**:

| Secret | Value |
| --- | --- |
| `ANTHROPIC_API_KEY` | Your Anthropic API key |
| `DISCORD_WEBHOOK` | Your Discord channel webhook URL |

## Notes

- Cron is UTC. `0 12 * * *` is 8 AM EDT; becomes 7 AM after NYC's November DST change
  (switch to `0 13 * * *` to hold 8 AM through the EST months).
- The `web_search` tool is billed per search, independent of model choice.
- GitHub scheduled runs can fire a few minutes late under load.
