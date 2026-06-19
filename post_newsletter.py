import os
import json
from datetime import datetime, timezone
import anthropic
import requests

client = anthropic.Anthropic()  # reads ANTHROPIC_API_KEY from env

SYSTEM = """You are an automated daily VTuber newsletter generator running on a \
schedule. No human will read your reply or answer questions - your entire output is \
published verbatim to a Discord channel.

Hard rules:
- Output ONLY the finished newsletter in Discord-friendly markdown. No preamble, no \
explanation of your process, no meta-commentary, no questions, and never offer the \
reader a list of options.
- NEVER stall or refuse because news is sparse. Always produce a complete, fun \
newsletter using whatever you can find - smaller updates, ongoing storylines, popular \
clips, milestones, upcoming events, and wholesome community moments all count.
- Keep it light, positive, and forward-to-a-friend fun. Avoid NSFW content, harassment \
or misconduct allegations, and heavy/sensitive drama - lead with the celebratory and \
entertaining side of the VTuber world."""

PROMPT = """Write today's VTuber mini-newsletter using only what you find via web search.

Format it exactly like this:

**\U0001F4FA [Catchy headline for today's edition]**

A one-line teaser summarizing the vibe of today's news.

---

Cover 3-5 stories. For each, write a short punchy paragraph (2-4 sentences) with a \
fun, slightly irreverent tone - like you're texting your friend about it. Include \
agency news (Hololive, Nijisanji, indie VTubers, etc.), viral clips, milestone \
achievements, debuts/collabs, and lighthearted moments worth knowing about. If big \
breaking news is thin, fill with notable ongoing happenings and fun community moments \
so the newsletter always feels complete.

End with a **"Clip of the Day"** - describe one moment or clip people are talking \
about and why it's worth watching (link if available)."""

# --- 1. Generate the newsletter (server-side web search) ---
now = datetime.now(timezone.utc)
today = now.strftime("%A, %B %d, %Y")
month_year = now.strftime("%B %Y")

user_msg = f"""Today's date is {today} (UTC). You are writing TODAY's edition.

CRITICAL recency rules:
- Every story MUST come from a web search result published within the last 7 days. \
Do NOT use your own training/background knowledge for any specific event, name, date, \
collab, or claim - if you did not just find it via search, do not include it.
- Search with date-qualified queries that include the current month and year, e.g. \
"VTuber news {month_year}", "Hololive {month_year}", "Nijisanji {month_year}", \
"VTuber debut {month_year}", "VTuber milestone this week".
- Before including any story, check the result's publish date. If it is older than \
about a week, discard it and search again. Anything from 2025 or earlier is too old.
- If you genuinely cannot find five stories from the past week, include fewer rather \
than padding with old news - but always produce a complete newsletter.

{PROMPT}"""

messages = [{"role": "user", "content": user_msg}]
tools = [{"type": "web_search_20260209", "name": "web_search"}]  # dynamic filtering on 4.6+

for _ in range(10):  # guard against runaway pause_turn loops
    resp = client.messages.create(
        model="claude-sonnet-4-6",
        max_tokens=16000,
        system=SYSTEM,
        tools=tools,
        messages=messages,
    )
    if resp.stop_reason == "pause_turn":
        messages.append({"role": "assistant", "content": resp.content})
        continue
    break

# --- diagnostics: confirm web search actually ran ---
queries = [b.input.get("query") for b in resp.content
           if b.type == "server_tool_use" and b.name == "web_search"]
stu = getattr(resp.usage, "server_tool_use", None)
search_count = getattr(stu, "web_search_requests", None) if stu else None
print(f"web_search_requests (final turn usage): {search_count}")
print(f"search queries this turn: {queries}")

text = "".join(b.text for b in resp.content if b.type == "text").strip()
if not text:
    raise SystemExit("No newsletter text generated")

# --- 2. Post to Discord (emoji-safe + 2000-char chunking) ---
url = os.environ["DISCORD_WEBHOOK"]

chunks = [text[i:i + 1900] for i in range(0, len(text), 1900)] or [""]
for n, chunk in enumerate(chunks, 1):
    body = json.dumps({"content": chunk}, ensure_ascii=True)  # emoji-safe
    r = requests.post(
        url,
        data=body.encode("utf-8"),
        headers={"Content-Type": "application/json",
                 "User-Agent": "newsletter-bot/1.0"},
        timeout=30,
    )
    r.raise_for_status()
    print(f"Posted part {n}/{len(chunks)} ({len(chunk)} chars) -> {r.status_code}")
