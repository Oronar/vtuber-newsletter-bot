import os
import json
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

PROMPT = """Write today's VTuber mini-newsletter. Use web search to find the most \
recent VTuber news, clips, milestones, debuts, collabs, and fun moments - prioritize \
the freshest you can find (ideally the last 24-48 hours), but don't restrict yourself \
to a hard 24-hour window if bigger or more interesting recent stories are available.

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
messages = [{"role": "user", "content": PROMPT}]
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
