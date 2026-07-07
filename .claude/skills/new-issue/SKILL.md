---
name: new-issue
description: Generate a new SIGNAL//BOOST weekly VTuber newsletter issue from live web search and write it to docs/_data/issue.json. Two modes — "weekly" (live: bumps the issue number and pushes to main so GitHub Pages redeploys) and "test"/"oneoff" (a special edition for testing or fun: writes locally, marks the issue kind:"oneoff", and never pushes). Use when the user asks to generate/publish a newsletter issue, run the weekly dispatch, or make a test/one-off edition.
---

# new-issue — generate a SIGNAL//BOOST edition

This skill produces one issue of the newsletter as structured data. The site
(`docs/`) is a Jekyll page that renders whatever is in `docs/_data/issue.json`; this
skill's job is to write a good `issue.json` and, for real weekly runs, publish it.

You (the model) do the whole thing as an agent: search the web, compose the issue,
write the JSON, and — only in `weekly` mode — commit and push. There is no external
API and no Python generator; the old `post_newsletter.py`/Claude-API path is retired.

## Modes (parse from the invocation arguments)

- **`weekly`** — the real, scheduled edition.
  - Increment the issue number, set `kind: "weekly"`, `label: ""`.
  - Write `docs/_data/issue.json`.
  - `git add docs/_data/issue.json`, commit, and **push to `main`** (Pages deploys
    from `main` → `/docs`, so pushing publishes it). **Confirm with the user before
    the first push** unless running unattended (a scheduled cloud routine).
- **`test`** / **`oneoff`** — a special edition for testing or just for fun.
  - Do **NOT** change the issue number (reuse the current one).
  - Set `kind: "oneoff"` and `label` to a short tag (the argument after the mode, e.g.
    `test "sponsor idea"` → `label: "sponsor idea"`; default `label: "test"`).
  - Write `docs/_data/issue.json` and **stop — do not commit or push.** The template
    shows a magenta "⚠ TEST ISSUE — NOT A SCHEDULED DISPATCH" banner whenever
    `kind != "weekly"`, so these are unmistakable and never go live.
  - Tell the user how to preview (below) and that `git checkout docs/_data/issue.json`
    restores the last committed issue.

If no mode is given, default to **`test`** (the safe choice — never publishes).

## Editorial rules (carried from the original bot — keep these)

- **Recency:** every story must come from a web result published in the **last 7 days**.
  Do not use training knowledge for specific claims, names, dates, or numbers — if you
  didn't just find it via search, don't include it. (Tweets/X posts may be a little
  older since they carry reliable timestamps, but stay within roughly a week.)
- **Balance:** keep it across the whole scene. **Hololive/Holostars: at most two
  stories.** Make a real effort to feature Nijisanji, VShojo, PRISM Project, Phase
  Connect, idol, and notable indies. Search many agencies, not just one.
- **Tone:** light, positive, forward-to-a-friend fun — slightly irreverent, like you're
  texting a friend. Real talents and real agencies (this is not fiction — drop any
  "fictional" disclaimer from the footer).
- **The Tea Corner** (the `tea` array) is a permanent section, sourced from **4chan
  /vt/** and its archives (desuarchive, warosu). At least 2 items, framed as unverified
  rumor ("word on /vt/ is…", "the rumor mill says…"). Spicy is fine — drama, beef, ship
  wars, graduation/collab speculation, running jokes. **Four hard lines — never cross:**
  (a) no unverified allegations of sexual misconduct, abuse, or crime against a named
  person; (b) no real-life identities / doxxing; (c) no explicit NSFW; (d) no
  speculation about a real person's mental health or self-harm. Skip only the individual
  items that cross a line; never drop the section.

## Suggested searches (widen with month/year, e.g. "July 2026")

`VTuber news July 2026`, `Hololive July 2026`, `Nijisanji July 2026`,
`VShojo July 2026`, `PRISM Project VTuber July 2026`, `Phase Connect July 2026`,
`indie VTuber July 2026`, `VTuber debut July 2026`, `VTuber milestone July 2026`,
`site:x.com VTuber July 2026`, `site:desuarchive.org /vt/ July 2026`,
`warosu /vt/ July 2026`. Check each result's publish date before using it.

## Output: docs/_data/issue.json

Write exactly this shape (see the current file for a worked example). Every string is
plain text (no markdown). Use real source URLs for `href`.

```jsonc
{
  "kind": "weekly",            // or "oneoff" for test/fun editions
  "label": "",                 // short tag when kind is "oneoff", else ""
  "issueNo": "048",            // weekly: previous + 1, zero-padded to 3; test: unchanged
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
  "onAirSubhead": "NOTABLE SLOTS WORTH CLEARING YOUR CALENDAR FOR · ALL TIMES UST",
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

Validate it parses: `python -c "import json;json.load(open('docs/_data/issue.json',encoding='utf-8'))"`.

## Preview locally (no Ruby needed)

There is no local Jekyll toolchain. To eyeball a build, render with the emulator the
Step-1 work used (or just open the committed site once Pages redeploys). If a scratch
renderer isn't around, note that the true build only happens on GitHub Pages after a
`weekly` push. `git checkout docs/_data/issue.json` reverts a test edition.

## Publish (weekly only)

```bash
git add docs/_data/issue.json
git commit -m "SIGNAL//BOOST issue <NNN> — <lead title>"
git push origin main
```

GitHub Pages rebuilds `main`/`docs` automatically. (A later pass will add per-issue
archive permalinks and a push-triggered Discord-link Action; not part of this skill yet.)
