"""Tim VIDEO (trailer/gameplay chinh chu) cua mot game tren Steam Store — nguon thu 2 khi trang PS Store khong co media video.
Chi dung stdlib (job chon chay bang python3 he thong). Dung boi khuon/top5/chon-top5.py.

  tim_video(ten) -> list[dict(url, ten, app_id)]   (url = hls_h264 .m3u8; sap theo uu tien Trailer/Gameplay/Launch, PEGI/Rating cuoi)

Cach lam (24/10/2026, ke-hoach-video-game.md):
  1. https://store.steampowered.com/api/storesearch/?term=<ten>&cc=us&l=en -> chon item type=app, ten KHOP (chuan hoa bo (R)(TM), PS4/PS5,
     Edition...; ti le giong >= 0,85), KHONG nhan DLC/bundle/soundtrack/Upgrade/Ticket...
  2. https://store.steampowered.com/api/appdetails?appids=<id>&filters=movies -> movies[].hls_h264
Khong tim duoc / loi mang -> [] (khong nem ngoai le).
"""
import difflib
import json
import re
import time
import urllib.parse
import urllib.request

UA = "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0 Safari/537.36"
NGUONG = 0.85
# Tu lam item KHONG phai game goc (DLC/bundle/nhac/ve nang cap...). So khop theo tu nguyen ven.
_TU_LOAI = {"dlc", "bundle", "soundtrack", "ost", "upgrade", "ticket", "pack", "season", "pass", "demo", "expansion", "artbook", "wallpaper",
            "costume", "costumes", "skin", "skins", "booster", "tool", "sdk", "beta", "playtest", "server", "dedicated", "voucher", "credits", "coins"}
# Tu BO khi chuan hoa ten (bien the ban/nen tang), khong bo tu mang nghia cua ten game.
_TU_BO = {"ps4", "ps5", "ps", "edition", "for", "full", "game", "definitive", "deluxe", "complete", "goty", "ultimate", "standard", "remastered", "the"}


_LA_MA = {"ii": "2", "iii": "3", "iv": "4", "v": "5", "vi": "6", "vii": "7", "viii": "8", "ix": "9", "x": "10", "xi": "11", "xii": "12", "xiii": "13", "xiv": "14", "xv": "15", "xvi": "16"}


def chuan_hoa(ten):
    """Ten -> chuoi so sanh: bo (R)(TM)(C), chu thuong, bo 'PS4 & PS5', bo dau cau, bo tu bien the (Edition...), so La Ma (IV) -> so (4)."""
    t = re.sub(r"[®™©]", " ", str(ten or "")).lower()
    t = re.sub(r"\bps\s?[45](\s*(&|and|/)\s*ps\s?[45])?\b", " ", t).replace("&", " and ")
    ws = [w for w in re.sub(r"[^a-z0-9]+", " ", t).split() if w not in _TU_BO]
    while ws and ws[-1] == "and":
        ws.pop()
    return " ".join(_LA_MA.get(w, w) for w in ws)


def _so(chuoi):
    return sorted(w for w in chuoi.split() if w.isdigit())


def la_game_goc(ten_steam):
    """False neu ten co tu cua DLC/bundle/nhac/ve nang cap."""
    return not (set(re.sub(r"[^a-z0-9]+", " ", str(ten_steam or "").lower()).split()) & _TU_LOAI)


def giong(a, b):
    ca, cb = chuan_hoa(a), chuan_hoa(b)
    if not ca or not cb:
        return 0.0
    if _so(ca) != _so(cb):   # Resident Evil 5 != Resident Evil 4 (ti le chu giong 0,93 nhung la game khac)
        return 0.0
    return difflib.SequenceMatcher(None, ca, cb).ratio()


def _lay_json(url, lan=3, cho=30):
    for k in range(lan):
        try:
            return json.loads(urllib.request.urlopen(urllib.request.Request(url, headers={"User-Agent": UA}), timeout=cho).read().decode("utf-8", "ignore"))
        except Exception:
            time.sleep(1.5 * (k + 1))
    return None


def tim_app(ten, lay_json=None):
    """Item Steam KHOP ten nhat (type=app, khong DLC/bundle, giong >= NGUONG) -> dict(id, ten, giong) hoac None."""
    lay_json = lay_json or _lay_json
    j = lay_json("https://store.steampowered.com/api/storesearch/?" + urllib.parse.urlencode({"term": ten, "cc": "us", "l": "en"}))
    tot = None
    for it in (j or {}).get("items") or []:
        if it.get("type") != "app" or not it.get("id") or not la_game_goc(it.get("name")):
            continue
        r = giong(ten, it.get("name"))
        if r >= NGUONG and (tot is None or r > tot["giong"]):
            tot = dict(id=int(it["id"]), ten=it.get("name"), giong=round(r, 3))
    return tot


def _uu_tien(ten_video):
    """Diem nho = uu tien: trailer 0, gameplay/launch 1, khac 5. PHAT: PEGI/Rating/ESRB +3 (nhe); Trial/Demo +3 nua (24/10: SOTTR «ESRB EN - Trial Trailer»
    ngang «ESRB EN Launch Trailer» va dung truoc nho thu tu goc, nhung ban Trial khong co doan sang du dai -> Launch len truoc); RTX/NVIDIA/GeForce (logo hang card do hoa),
    Accolade/Review/Award (chu trich danh gia), Teaser (it canh game) +10 -> chi dung khi khong con video nao khac."""
    t = str(ten_video or "").lower()
    diem = 0 if "trailer" in t else 1 if re.search(r"gameplay|launch", t) else 5
    return diem + (3 if re.search(r"pegi|rating|esrb|cero|usk|classification", t) else 0) + (3 if re.search(r"\b(trial|demo)\b", t) else 0) + (10 if re.search(r"rtx|nvidia|geforce|accolade|review|award|teaser", t) else 0)


def video_cua_app(app_id, lay_json=None):
    """appdetails?filters=movies -> list[dict(url, ten, app_id)] sap theo uu tien (on dinh: giu thu tu goc khi bang diem)."""
    lay_json = lay_json or _lay_json
    j = lay_json(f"https://store.steampowered.com/api/appdetails?appids={app_id}&filters=movies")
    d = ((j or {}).get(str(app_id)) or {})
    if not d.get("success"):
        return []
    out = []
    for m in (d.get("data") or {}).get("movies") or []:
        u = m.get("hls_h264")
        if u:
            out.append(dict(url=u, ten=m.get("name") or "", app_id=int(app_id)))
    return sorted(out, key=lambda v: _uu_tien(v["ten"]))


def tim_video(ten, lay_json=None):
    """Ten game (PS Store) -> video chinh chu tren Steam. [] neu khong co app khop hoac app khong co video."""
    app = tim_app(ten, lay_json)
    return video_cua_app(app["id"], lay_json) if app else []
