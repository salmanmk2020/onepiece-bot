if force == "spoiler":
        label, spoiler, prio = CATS[0][1], True, 2
    summary = clean(e.get("summary", ""))[:250]
    if ("reddit.com" in e.link or "news.google.com" in e.link
            or summary.lower().startswith(title.lower()[:30])):
        summary = ""
    t = f"<tg-spoiler>{esc(title)}</tg-spoiler>" if spoiler else f"<b>{esc(title)}</b>"
    text = f"{label}\n\n{t}\n"
    if summary:
        text += f"\n{'<tg-spoiler>' + esc(summary) + '</tg-spoiler>' if spoiler else esc(summary)}\n"
    text += (f'\n🔗 <a href="{html.escape(e.link)}">{esc(source_label(e))}</a>'
             f"\n\n#OnePiece #وان_پیس")
    key_t = "t:" + re.sub(r"\W+", "", title.lower())[:80]
    return {"text": text[:1000], "prio": prio, "spoiler": spoiler,
            "e": None if spoiler else e, "keys": [e.link, key_t]}

def birthday_items(now):
    return [{"text": f"🎂 امروز تولد <b>{n}</b> است!\n\n#تولد_شخصیت #OnePiece #وان_پیس",
             "prio": 0, "keys": [f"bday:{now.year}:{now.month}-{now.day}:{n}"]}
            for n in BDAYS.get((now.month, now.day), [])]

def episode_item():
    q = """query { Page(perPage:1) { airingSchedules(mediaId:21, notYetAired:false, sort:TIME_DESC) {
           episode airingAt media { coverImage { extraLarge } } } } }"""
    try:
        r = requests.post("https://graphql.anilist.co", json={"query": q}, timeout=15)
        s = r.json()["data"]["Page"]["airingSchedules"][0]
        if time.time() - s["airingAt"] > 3 * 86400:
            return None
        ep = s["episode"]
        return {"text": f'📺 قسمت <b>{ep}</b> انیمه وان‌پیس پخش شد!\n\n'
                        f'🔗 <a href="https://anilist.co/anime/21">AniList</a>\n\n#OnePiece #وان_پیس',
                "prio": 1, "image": s["media"]["coverImage"]["extraLarge"],
                "keys": [f"ep:{ep}"]}
    except Exception:
        return None

def send(it):
    base = f"https://api.telegram.org/bot{TOKEN}"
    img = it.get("image") or (get_image(it["e"]) if it.get("e") else None)
    if img:
        r = requests.post(f"{base}/sendPhoto", timeout=30, data={
            "chat_id": CHANNEL, "photo": img, "caption": it["text"], "parse_mode": "HTML"})
        if r.ok:
            return True
    r = requests.post(f"{base}/sendMessage", timeout=30, data={
        "chat_id": CHANNEL, "text": it["text"], "parse_mode": "HTML",
        "link_preview_options": json.dumps({"is_disabled": True})})
    return r.ok

seen = set(json.load(open(SEEN_FILE))) if os.path.exists(SEEN_FILE) else set()
now = datetime.now(ZoneInfo("Asia/Tehran"))
items = birthday_items(now)
ep = episode_item()
if ep:
    items.append(ep)

queued = set()
for url, need_kw, force in FEEDS:
    for e in load(url):
        tl = e.title.lower()
        key_t = "t:" + re.sub(r"\W+", "", tl)[:80]
        if e.link in seen or key_t in seen or key_t in queued:
            continue
        if need_kw and "one piece" not in tl and "onepiece" not in tl:
            continue
        if any(b in tl for b in BLOCK) or not fresh(e):
            continue
        queued.add(key_t)
        items.append(news_item(e, force))

items = [i for i in items if not any(k in seen for k in i["keys"])]
items.sort(key=lambda x: x["prio"])

for it in items[:MAX_POSTS]:
    if send(it):
        seen.update(it["keys"])

json.dump(list(seen), open(SEEN_FILE, "w"))
