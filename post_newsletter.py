import os
import json
import anthropic
import requests

client = anthropic.Anthropic()  # reads ANTHROPIC_API_KEY from env

PROMPT = """You are writing a daily VTuber mini-newsletter. Search the web for the \
latest VTuber news, clips, drama, milestones, and moments from the past 24 hours.

Format it like a fun, shareable newsletter with this structure:

**\U0001F4FA [Catchy headline for today's edition]**

A one-line teaser summarizing the vibe of today's news.

---

Cover 3-5 stories. For each, write a short punchy paragraph (2-4 sentences) with a \
fun, slightly irreverent tone - like you're texting your friend about it. Include \
agency news (Hololive, Nijisanji, indie VTubers, etc.), viral clips, milestone \
achievements, debuts/graduations, and any drama or funny moments worth knowing about.

End with a **"Clip of the Day"** - describe one moment or clip that people are \
talking about and why it's worth watching (link if available).

Keep it light, entertaining, and something you'd actually want to forward to a friend \
who's into VTubers. Use web search for fresh info from the last 24 hours."""

# --- 1. Generate the newsletter (server-side web search) ---
messages = [{"role": "user", "content": PROMPT}]
tools = [{"type": "web_search_20260209", "name": "web_search"}]

for _ in range(10):  # guard against runaway pause_turn loops
    resp = client.messages.create(
        model="claude-haiku-4-5",
        max_tokens=16000,
        tools=tools,
        messages=messages,
    )
    if resp.stop_reason == "pause_turn":
        messages.append({"role": "assistant", "content": resp.content})
        continue
    break

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
