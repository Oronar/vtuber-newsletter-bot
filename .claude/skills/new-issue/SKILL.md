---
name: new-issue
description: Generate a new SIGNAL//BOOST weekly VTuber newsletter issue from live web search and write it into the docs/ archive. Two modes — "weekly" (live: creates the next numbered issue with a permanent url and pushes to main so GitHub Pages redeploys and Discord is notified) and "test"/"oneoff" (a special edition for testing or fun: writes a local preview only, never touches the archive, never pushes). Use when the user asks to generate/publish a newsletter issue, run the weekly dispatch, or make a test/one-off edition.
---

# new-issue — generate a SIGNAL//BOOST edition

The site (`docs/`) is a Jekyll page. Each issue is a JSON data file at
`docs/_data/issues/NNN.json` (zero-padded, e.g. `001.json`) plus a one-line stub
`docs/issues/NNN.html` that gives it a **permanent url** `…/issues/NNN/`. The homepage
renders whichever issue number is highest. This skill's job is to write a good issue
and, for real weekly runs, publish it.

You (the model) do the whole thing as an agent: search the web, compose the issue, write
the files, and — only in `weekly` mode — commit and push. There is no external API and
no Python generator; the old `post_newsletter.py`/Claude-API path is retired.

## Modes (parse from the invocation arguments)

- **`weekly`** — the real, scheduled edition.
  1. Find the highest existing `docs/_data/issues/NNN.json`; the new number is that **+ 1**
     (zero-padded to 3 digits). If none exist, start at `001`.
  2. Write `docs/_data/issues/NNN.json` with `kind: "weekly"`, `label: ""`, `issueNo:"NNN"`.
  3. Create the permalink stub `docs/issues/NNN.html` (copy the pattern from an existing
     one — front matter `permalink: /issues/NNN/` then
     `{%- assign issue = site.data.issues["NNN"] -%}` and an include of `page.html`).
  4. `git add` both files, commit, and **push to `main`**. Pages redeploys (homepage +
     the new permalink) and the Discord notify Action posts the permalink. **Confirm with
     the user before the first push** unless running unattended (a scheduled cloud routine).
- **`test`** / **`oneoff`** — a special edition for testing or just for fun.
  - Write a single preview file `docs/_data/issue-preview.json` with `kind: "oneoff"`,
    `label` = the argument after the mode (e.g. `test "sponsor idea"` → `"sponsor idea"`;
    default `"test"`), and any `issueNo` (it isn't published, so the number doesn't matter).
  - **Do NOT** write under `docs/_data/issues/`, create a stub, commit, or push — a test
    edition must never change the archive, the homepage, or ping Discord.
  - Preview it locally (below). The page shows a magenta "⚠ TEST ISSUE" banner because
    `kind != "weekly"`.

If no mode is given, default to **`test`** (the safe choice — never publishes).

## Editorial rules (carried from the original bot — keep these)

- **Recency:** every story must come from a web result published in the **last 7 days**.
  Do not use training knowledge for specific claims, names, dates, or numbers — if you
  didn't just find it via search, don't include it. (Tweets/X posts may be a little older
  since they carry reliable timestamps, but stay within roughly a week.)
- **Balance:** keep it across the whole scene. **Hololive/Holostars: at most two stories.**
  Make a real effort to feature Nijisanji, Phase Connect, indie collectives, and notable
  individual indies. Search many agencies, not just one. (Note: VShojo shut down in 2025
  and PRISM Project closed in 2024 — their talents are now independents.)
- **Tone:** light, positive, forward-to-a-friend fun — slightly irreverent, like you're
  texting a friend. Real talents and real agencies (this is a real fan newsletter, not
  fiction — there is no "fictional" disclaimer).
- **The Tea Corner** (the `tea` array) is a permanent section, ideally sourced from **4chan
  /vt/** and its archives (desuarchive, warosu). At least 2 items, framed as unverified
  rumor ("word on /vt/ is…", "the rumor mill says…"). Spicy is fine — drama, beef, ship
  wars, graduation/collab speculation, running jokes. **Four hard lines — never cross:**
  (a) no unverified allegations of sexual misconduct, abuse, or crime against a named
  person; (b) no real-life identities / doxxing; (c) no explicit NSFW; (d) no speculation
  about a real person's mental health or self-harm. Skip only the individual items that
  cross a line; never drop the section. (Web search often surfaces exactly this kind of
  off-limits drama — exclude it and use lighter debut/collab/redesign speculation instead.)

## Suggested searches (widen with month/year, e.g. "July 2026")

`VTuber news July 2026`, `Hololive July 2026`, `Nijisanji July 2026`,
`Phase Connect July 2026`, `indie VTuber July 2026`, `VTuber debut July 2026`,
`VTuber milestone July 2026`, `site:x.com VTuber July 2026`,
`site:desuarchive.org /vt/ July 2026`, `warosu /vt/ July 2026`. Check each result's
publish date before using it.

## Issue JSON shape

Write exactly this shape (copy an existing `docs/_data/issues/*.json` as a template).
Every string is plain text (no markdown). Use real source URLs for `href`.

```jsonc
{
  "kind": "weekly",            // or "oneoff" for the test preview file
  "label": "",                 // short tag when kind is "oneoff", else ""
  "issueNo": "002",            // weekly: previous + 1, zero-padded to 3
  "issueDate": "07 JUL 2026",  // today, "DD MON YYYY" uppercase
  "tagline": "…",              // one-line vibe of the week's dispatch
  "inThisIssue": ["…","…","…"],// 3-4 short ticker teasers
  "lead": { "kicker": "TOP SIGNAL", "title": "…", "body": "…" }, // the week's biggest story
  "stories": [                 // THE DISPATCH — 5 to 8 items, agency-balanced
    { "num": "01", "color": "#ff4fa3", "date": "06 JUL", "href": "https://…",
      "title": "…", "blurb": "2-4 punchy sentences" }
    // cycle color through: #ff4fa3, #36d6e7, #c6ff3d, #9b6bff
  ],
  "indieSubhead": "NO AGENCY, NO PROBLEM — NEWS FROM THE SELF-MADE CORNER OF THE SCENE",
  "indies": [ /* 3-4 items, same object shape as stories, indie VTubers */ ],
  "onAirSubhead": "NOTABLE SLOTS WORTH CLEARING YOUR CALENDAR FOR · ALL TIMES LOCAL-ISH",
  "onAir": [                   // 3-5 upcoming streams/events from this week's announcements
    { "when": "FRI · 20:00", "title": "…", "desc": "…", "tag": "★ DEBUT", "tagColor": "#ff4fa3" }
    // tags: "★ DEBUT"/#ff4fa3, "◆ DROP"/#c6ff3d, "EVENT"/#8b90a8, etc.
  ],
  "tea": [                     // THE TEA CORNER — 2-4 /vt/ rumors, four hard lines above
    { "color": "#ff4fa3", "text": "…" }
    // cycle color through: #ff4fa3, #36d6e7, #c6ff3d
  ],
  "footerNote": "…"            // sign-off; real, no "fictional" disclaimer
}
```

Validate it parses: `python -c "import json;json.load(open('<the file>',encoding='utf-8'))"`.

## Preview locally (no Ruby needed)

There is no local Jekyll toolchain. Preview with the scratchpad emulator used during
setup: `python render.py` renders the latest published issue; `python render.py
docs/_data/issue-preview.json` renders a test edition. It writes `rendered.html` to open
in a browser. The true build only happens on GitHub Pages after a `weekly` push.

## Publish (weekly only)

```bash
git add docs/_data/issues/NNN.json docs/issues/NNN.html
git commit -m "SIGNAL//BOOST issue NNN — <lead title>"
git push origin main
```

Pages rebuilds `main`/`docs`; the homepage moves to the new issue and `…/issues/NNN/`
becomes its permanent url. The `discord-notify.yml` Action then posts that permalink to
the `DISCORD_WEBHOOK`. (Do not put `[skip-discord]` in a weekly commit message — that
tag suppresses the Discord post and is only for infra/refactor commits.)
