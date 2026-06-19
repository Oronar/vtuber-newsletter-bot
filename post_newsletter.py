import os
import re
import json
from datetime import datetime, timezone
import anthropic
import requests

client = anthropic.Anthropic()  # reads ANTHROPIC_API_KEY from env

SYSTEM = """You are an automated daily VTuber newsletter generator running on a \
schedule. No human will read your reply or answer questions - your entire output is \
published verbatim to a Discord channel.

Hard rules:
- Output ONLY the finished newsletter in Discord-friendly markdown. The VERY FIRST \
characters of your reply must be the headline line that starts with "**" - no preamble, \
no "Let me...", no "I now have enough...", no explanation of your process, no \
meta-commentary, no questions, and never offer the reader a list of options. Do your \
searching and thinking silently; emit text only once you are writing the final \
newsletter.
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
viral clips, milestone achievements, debuts/collabs, and lighthearted moments worth \
knowing about.

Keep the newsletter balanced across the VTuber world. Hololive and Holostars news is \
welcome but must NOT dominate - at most one or two stories may be Hololive/Holostars. \
Make a real effort to feature Nijisanji, other agencies (VShojo, PRISM Project, Phase \
Connect, idol, etc.), and notable independent VTubers. If big breaking news is thin, \
fill with notable ongoing happenings and fun community moments so the newsletter \
always feels complete.

ALWAYS include a section near the end titled **\U0001FAD6 Gossip Corner** - it is a \
permanent staple of every edition. Include AT LEAST 2 items of community gossip and \
speculation sourced from the 4chan /vt/ board and its archives. If real news above was \
thin, pad this section with more items (4-6) so the newsletter still feels full. \
Clearly frame every item as unverified rumor / community chatter (e.g. "word on /vt/ \
is...", "the rumor mill says..."). Spicy stuff is fair game - drama, beef, rivalries, \
ship wars, graduation/contract rumors, who's-mad-at-who, collab and debut speculation, \
running jokes and memes. Keep the tone playful and teasing rather than mean-spirited. \
The ONLY hard lines - never repeat these: (a) unverified allegations of sexual \
misconduct, abuse, or crimes against a named person; (b) anyone's real-life identity \
or doxxing; (c) explicit NSFW content; (d) speculation about a real person's mental \
health or self-harm. Skip only the individual items that cross those four lines - never \
drop the whole section, and keep searching until you have at least 2 usable items.

End with a **"Clip of the Day"** - describe one moment or clip people are talking \
about and why it's worth watching (link if available)."""

# --- 1. Generate the newsletter (server-side web search) ---
now = datetime.now(timezone.utc)
today = now.strftime("%A, %B %d, %Y")
month_year = now.strftime("%B %Y")

user_msg = f"""Today's date is {today} (UTC). You are writing TODAY's edition.

CRITICAL recency rules:
- Every story MUST come from a web search result published within the last 24 hours \
(today or yesterday). Do NOT use your own training/background knowledge for any \
specific event, name, date, collab, or claim - if you did not just find it via search, \
do not include it.
- Search broadly across the whole VTuber scene with date-qualified queries that \
include the current month and year - cover many agencies and indies, not just one. \
e.g. "VTuber news {month_year}", "Nijisanji {month_year}", "VShojo {month_year}", \
"PRISM Project VTuber {month_year}", "Phase Connect {month_year}", "indie VTuber \
{month_year}", "Hololive {month_year}", "VTuber debut {month_year}", "VTuber news \
today".
- ALSO search X/Twitter directly for fresh community chatter and clips, since a lot of \
VTuber news breaks there first. Use site-scoped queries such as "site:x.com VTuber \
{month_year}", "site:twitter.com VTuber clip {month_year}", "site:x.com Nijisanji OR \
VShojo {month_year}", and "site:x.com VTuber debut OR milestone {month_year}". Treat \
any tweet you find as a real source - verify the post date and quote/summarize it.
- Before including any story, check the result's publish date. Web/article sources \
must be from the last 24 hours (today or yesterday). X/Twitter posts may be up to 48 \
hours old since tweets carry reliable timestamps. Discard anything older - anything \
from 2025 or earlier is far too old.
- ALWAYS search the 4chan /vt/ board and its archives for lighthearted gossip - the \
Gossip Corner is a permanent section of every edition. Live threads are ephemeral, so \
search the archives: e.g. "site:desuarchive.org /vt/ {month_year}", "warosu /vt/ \
{month_year}", "4chan /vt/ rumor {month_year}". If real news was thin, search harder \
here to pad the Gossip Corner. Apply the same recency filter and the strict safety \
filters described in the format section.
- If you genuinely cannot find five fresh stories, include fewer rather than padding \
with older news - but always produce a complete newsletter.

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

# Safety net: drop any narration the model emitted before the newsletter itself.
# The newsletter always opens with the headline line "**\U0001F4FA ...". If that
# marker exists, discard everything before it.
marker = text.find("**\U0001F4FA")
if marker > 0:
    print(f"Stripped {marker} chars of preamble before headline")
    text = text[marker:]

# --- 2. Post to Discord (emoji-safe, boundary-aware chunking) ---
def chunk_message(body, limit=1900):
    """Pack text into <=limit-char messages on paragraph boundaries so whole
    stories stay together. Falls back to sentence splits only when a single
    paragraph is too long, and to a hard split only for an over-long sentence."""
    def hard_split(s):
        return [s[i:i + limit] for i in range(0, len(s), limit)]

    def sentences(para):
        out = []
        for sent in re.split(r"(?<=[.!?])\s+", para.strip()):
            out.extend([sent] if len(sent) <= limit else hard_split(sent))
        return out

    chunks, current = [], ""

    def add(piece, sep):
        nonlocal current
        candidate = (current + sep + piece) if current else piece
        if len(candidate) <= limit:
            current = candidate
            return
        if current:
            chunks.append(current)
        current = piece

    for para in body.split("\n\n"):
        para = para.strip("\n")
        if not para:
            continue
        if len(para) <= limit:
            add(para, "\n\n")            # keep whole stories together
        else:
            for sent in sentences(para):  # story too long -> keep sentences whole
                add(sent, " ")
    if current:
        chunks.append(current)
    return chunks or [""]


url = os.environ["DISCORD_WEBHOOK"]

chunks = chunk_message(text)
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
