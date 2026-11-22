if ("reddit.com" in e.link or "news.google.com" in e.link
            or summary.lower().startswith(title.lower()[:30])):
        summary = ""
    if spoiler:
        t = "<tg-spoiler>" + esc(title) + "</tg-spoiler>"
    else:
        t = "<b>" + esc(title) + "</b>"
    text = label + "\n\n" + t + "\n"
    if summary:
        if spoiler:
            text += "\n<tg-spoiler>" + esc(summary) + "</tg-spoiler>\n"
        else:
            text += "\n" + esc(summary) + "\n"
    text += ('\n🔗 <a href="' + html.escape(e.link) + '">' + esc(source_label(e)) + "</a>"
             + "\n\n#OnePiece #وان_پیس")
    key_t = "t:" + re.sub(r"\W+", "", title.lower())[:80]
    return {"text": text[:1000], "prio": prio, "spoiler": spoiler,
            "e": None if spoiler else e, "keys": [e.link, key_t]}


def birthday_items(now):
    out = []
    for n in BDAYS.get((now.month, now.day), []):
        out.append({
            "text": "🎂 امروز تولد <b>" + n + "</b> است!\n\n#تولد_شخصیت #OnePiece #وان_پیس",
            "prio": 0,
            "keys": ["bday:%d:%d-%d:%s" % (now.year, now.month, now.day, n)],
        })
    return out


def episode_item():
    q = ("query { Page(perPage:1) { airingSchedules(mediaId:21, notYetAired:false, sort:TIME_DESC) "
         "{ episode airingAt media { coverImage { extraLarge } } } } }")
    try:
        r = requests.post("https://graphql.anilist.co", json={"query": q}, timeout=15)
        s = r.json()["data"]["Page"]["airingSchedules"][0]
        if time.time() - s["airingAt"] > 3 * 86400:
            return None
        ep = s["episode"]
        return {
            "text": "📺 قسمت <b>%d</b> انیمه وان‌پیس پخش شد!\n\n"
                    '🔗 <a href="https://anilist.co/anime/21">AniList</a>\n\n#OnePiece #وان_پیس' % ep,
            "prio": 1,
            "image": s["media"]["coverImage"]["extraLarge"],
            "keys": ["ep:%d" % ep],
        }
    except Exception:
        return None


def send(it):
    base = "https://api.telegram.org/bot" + TOKEN
    img = it.get("image") or (get_image(it["e"]) if it.get("e") else None)
    if img:
        r = requests.post(base + "/sendPhoto", timeout=30, data={
            "chat_id": CHANNEL, "photo": img,
            "caption": it["text"], "parse_mode": "HTML"})
        print("TELEGRAM photo:", r.status_code, r.text[:200])
        if r.ok:
            return True
    r = requests.post(base + "/sendMessage", timeout=30, data={
        "chat_id": CHANNEL, "text": it["text"], "parse_mode": "HTML",
        "link_preview_options": json.dumps({"is_disabled": True})})
    print("TELEGRAM text:", r.status_code, r.text[:200])
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
print("تعداد خبر آماده:", len(items))

for it in items[:MAX_POSTS]:
    if send(it):
        seen.update(it["keys"])

json.dump(list(seen), open(SEEN_FILE, "w"))
