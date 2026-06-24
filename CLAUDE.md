# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## What this is

A single-file Python script (`post_newsletter.py`) that runs as a scheduled GitHub
Action. It asks the Claude API (with server-side web search) to write a daily VTuber
mini-newsletter, then posts it to a Discord channel via webhook. There is no app
framework, package, or test suite — the whole program is ~195 lines in one module.

## Running it

```bash
pip install anthropic requests
ANTHROPIC_API_KEY=... DISCORD_WEBHOOK=... python post_newsletter.py
```

Both env vars are required (`ANTHROPIC_API_KEY` is read implicitly by the `anthropic`
client; `DISCORD_WEBHOOK` is read explicitly). The script makes live API calls and
posts to Discord on every run — there is no dry-run flag, so to test changes without
posting, comment out the `requests.post` loop or point `DISCORD_WEBHOOK` at a throwaway
webhook. In CI these come from repository secrets (Settings → Secrets and variables →
Actions).

The GitHub Action (`.github/workflows/newsletter.yml`) runs daily at `0 12 * * *` UTC
and can be triggered manually from the **Actions** tab. GitHub cron is fixed UTC with
no DST awareness, so 12:00 UTC is 8 AM EDT in summer but 7 AM EST after NYC's November
fallback — switch to `0 13 * * *` to hold 8 AM through the EST months.

> **Status: the workflow is currently disabled** (as of 2026-06-23) because the Claude
> API account ran out of credits. It was disabled via `gh workflow disable "VTuber
> Newsletter"`, not by a code change, so the YAML is unchanged. Re-enable with
> `gh workflow enable "VTuber Newsletter"` (or the **Actions** tab → workflow →
> **⋯ → Enable workflow**) once credits are restored; the daily schedule resumes
> automatically.

## Architecture

The script runs top-to-bottom in two phases:

1. **Generate** — A `messages.create` call with the `web_search` tool. The model does
   all searching and writing server-side; the script just loops on `stop_reason ==
   "pause_turn"` (up to 10 times) to let multi-step search turns complete, then takes
   the final response.

2. **Post** — `chunk_message()` splits the newsletter into ≤1900-char pieces on
   paragraph boundaries (falling back to sentence then hard splits) so Discord's
   2000-char limit is respected without breaking stories mid-paragraph. Each chunk is
   POSTed as ASCII-safe JSON (`ensure_ascii=True`) so emoji can't produce invalid-UTF-8
   / "invalid JSON" errors at Discord.

### Prompt design is the product

Most of the file is the `SYSTEM` / `PROMPT` / `user_msg` strings, and most behavior
lives there, not in code. Key invariants the editorial prompts enforce — preserve these
when editing:

- **No preamble.** The model is told its entire output is published verbatim, so it must
  start with the headline line `**📺 ...` and emit nothing else first. A code-level
  safety net (`text.find("**\U0001F4FA")`) strips any narration that slips in before the
  headline — so the headline emoji marker is load-bearing and the format string and that
  `find()` must stay in sync.
- **Recency.** Stories must come from web results in the last 24h (48h for X/Twitter
  posts); the model is told not to use training knowledge for specific claims.
- **Balance.** Hololive/Holostars capped at one or two stories; Nijisanji, VShojo, PRISM,
  Phase Connect, and indies must be represented.
- **Gossip Corner** is a permanent section (≥2 items, sourced from 4chan /vt/ archives
  like desuarchive/warosu) with four hard content lines: no unverified
  misconduct/abuse/crime allegations against named people, no doxxing/real-life
  identities, no explicit NSFW, no real-person mental-health/self-harm speculation. The
  git history shows these guardrails were deliberately tuned — read recent commits before
  loosening or tightening them.

### Things that move together

- `model="claude-sonnet-4-6"` and the `web_search_20260209` tool type are a matched pair;
  the dynamic-filtering comment notes web search behavior depends on model version.
- The diagnostics block (`web_search_requests`, `queries`) prints to CI logs to confirm
  search actually ran — useful when debugging an edition that looks stale.
