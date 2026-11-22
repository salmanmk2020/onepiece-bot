import feedparser, requests, json, os, re
from bs4 import BeautifulSoup

TOKEN = os.environ["BOT_TOKEN"]
CHANNEL = os.environ["CHANNEL_ID"]
MAX_POSTS = 1
KEYWORD = "one piece"
SEEN_FILE = "seen.json"

FEEDS = [
    "https://www.animenewsnetwork.com/all/rss.xml",
    "https://www.reddit.com/r/OnePiece/.rss",
    "https://news.google.com/rss/search?q=%22One+Piece%22+anime&hl=en-US&gl=US&ceid=US:en",
]
HEADERS = {"User-Agent": "Mozilla/5.0"}

def clean(html):
    return BeautifulSoup(html or "", "html.parser").get_text(" ", strip=True)

def get_image(e):
    for key in ("media_content", "media_thumbnail"):
        if e.get(key):
            return e[key][0].get("url")
    for enc in e.get("enclosures", []):
        if enc.get("type", "").startswith("image"):
            return enc.get("href")
    m = re.search(r'<img[^>]+src="([^"]+)"', e.get("summary", ""))
    if m:
        return m.group(1)
    try:
        r = requests.get(e.link, headers=HEADERS, timeout=10)
        tag = BeautifulSoup(r.text, "html.parser").find("meta", property="og:image")
        if tag and tag.get("content"):
            return tag["content"]
    except Exception:
        pass
    return None

def send(e):
    summary = clean(e.get("summary", ""))[:300]
    caption = f"📰 {e.title}\n\n{summary}\n\n🔗 {e.link}\n\n#OnePiece #وان_پیس"[:1000]
    img = get_image(e)
    base = f"https://api.telegram.org/bot{TOKEN}"
    if img:
        r = requests.post(f"{base}/sendPhoto",
                          data={"chat_id": CHANNEL, "photo": img, "caption": caption})
        if r.ok:
            return True
    r = requests.post(f"{base}/sendMessage", data={"chat_id": CHANNEL, "text": caption})
    return r.ok

seen = set(json.load(open(SEEN_FILE))) if os.path.exists(SEEN_FILE) else set()
items = []
for url in FEEDS:
    for e in feedparser.parse(url).entries:
        txt = (e.title + " " + e.get("summary", "")).lower()
        if KEYWORD in txt and e.link not in seen:
            items.append(e)

for e in items[:MAX_POSTS]:
    if send(e):
        seen.add(e.link)

json.dump(list(seen), open(SEEN_FILE, "w"))
