"""Do so lieu song cua video Sang Game (15/10/2026) - doc API chinh chu cua 5 kenh, ghi vao sg_so_lieu / sg_so_kenh qua cong sg-cong
(viec ghi_so_lieu, ban 9). Thay logic dang-lam/tu-dong-video/do-suc-khoe.py (file do giu nguyen lam du phong tren Mac).

  python -m do_so.chay --che-do thu|that [--so-ngay 30] [--ra file.json]

Danh sach bai lay tu KENH (khong tu so sg_dang); so chi de GAN NHAN khuon. Moi kenh chay trong try rieng.
Ma thoat: 0 = moi kenh dat; 1 = co kenh loi hoac ghi loi (phan dat van duoc ghi); 2 = thieu SG_CONG_KHOA.
Repo cong khai: khong in token, khong in so lieu tung bai; moi chuoi loi di qua chung.che.
"""
import argparse
import datetime as dt
import json
import math
import os
import re
import sys
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

from dang import chung, http, ntfy, so, yt, zernio

G = "https://graph.facebook.com/v26.0"
TH = "https://graph.threads.net/v1.0"
YT = "https://www.googleapis.com/youtube/v3"
YT_AN = "https://youtubeanalytics.googleapis.com/v2/reports"
ZER = zernio.GOC
GOC_FB, GOC_TH = "https://graph.facebook.com/", "https://graph.threads.net/"

DAU_CUA_SO = dt.datetime(2026, 10, 11, tzinfo=chung.VN)
LO_GHI = 500
TOI_DA_TRANG = 20        # vuot -> loi kenh (khong cat im lang)
NGUONG_LOI_BAI = 0.25
MA_GIOI_HAN = {4, 17, 32, 613}
LY_DO_GIOI_HAN = {"quotaExceeded", "rateLimitExceeded", "userRateLimitExceeded", "dailyLimitExceeded"}
RE_ID = re.compile(r"[A-Za-z0-9_.:-]{1,100}")
RE_NGAY = re.compile(r"\d{4}-\d{2}-\d{2}")
RE_GIO = re.compile(r"\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}(?:\.\d+)?(?:Z|[+-]\d{2}:\d{2})")
NEN_TANG = {"Facebook", "Instagram", "Threads", "YouTube", "TikTok"}
BIGINT = ("luot_xem", "thich", "binh_luan", "chia_se", "luu", "theo_doi_moi")
NUMERIC = ("xem_tb_giay", "do_dai_giay", "nguoi_la_pct", "xem_het_pct")
TEN = {"tin-nhanh": "Tin nhanh 07:30", "top5": "Top 5 12:00", "keo-thom-2": "Kèo 15:00", "keo-thom": "Kèo 20:00",
       "keo-thom-3": "Kèo 22:00", "binh-chon": "Bình chọn", "tin-web": "Tin web"}
KHONG_DONG_CHU = ("binh-chon", "tin-web")


class LoiKenh(Exception):
    pass


class LoiGioiHan(LoiKenh):
    pass


class KetQua:
    def __init__(self, ten):
        self.ten, self.bai, self.kenh, self.loi_bai, self.loi_kenh = ten, [], [], 0, None

    def them(self, d):
        if d is None:
            self.loi_bai += 1
        else:
            self.bai.append(d)


# ---------- tien ich nho ----------
_RE_LECH = re.compile(r"([+-]\d{2})(\d{2})$")


def tg(s):
    """Chuoi thoi gian ISO (Z, +0000, +00:00) -> datetime co mui gio; sai -> None."""
    if not s or not isinstance(s, str):
        return None
    s = _RE_LECH.sub(r"\1:\2", s.strip().replace("Z", "+00:00"))
    try:
        t = dt.datetime.fromisoformat(s)
    except ValueError:
        return None
    return t if t.tzinfo else t.replace(tzinfo=dt.timezone.utc)


def _ins(data, ten):
    """Gia tri metric `ten` trong list insights cua Graph/Threads. Sai cau truc o bat ky cap nao -> None."""
    if not isinstance(data, list):
        return None
    for m in data:
        if isinstance(m, dict) and m.get("name") == ten:
            if "values" in m:
                vs = m["values"]
                v = vs[0] if isinstance(vs, list) and vs else None
                return v.get("value") if isinstance(v, dict) else None
            tv = m.get("total_value")
            return tv.get("value") if isinstance(tv, dict) else None
    return None


def _so(v, nguyen=False):
    if isinstance(v, str):
        try:
            v = float(v)
        except ValueError:
            return None
    if isinstance(v, bool) or not isinstance(v, (int, float)) or not math.isfinite(v):
        return None
    return int(round(v)) if nguyen else v      # am / qua lon: de hop_le_cong loai CA BAI (khong ghi null)


def _dong1(s):
    return (s or "").strip().split("\n")[0][:140].strip() or None if isinstance(s, str) else None


def _tong(x):
    """{"summary": {"total_count": N}} cua Graph; sai kieu -> None."""
    x = x.get("summary") if isinstance(x, dict) else None
    return x.get("total_count") if isinstance(x, dict) else None


def _link(s):
    return s[:300] if isinstance(s, str) and s.startswith("https://") else None


def nhan_khuon(dang, do_dai, la_chu):
    ten = TEN.get(dang, dang) if dang else ("Video dài" if do_dai and do_dai > 120 else "tin-nóng / ngoài lịch")
    return ten + (" (chữ)" if la_chu and dang not in KHONG_DONG_CHU else "")


def hop_le_cong(d):
    """Kiem dung nhu cong sg-cong (lamSachBai). True = cong se nhan dong nay. Dung chung cho client va test."""
    try:
        if d.get("nen_tang") not in NEN_TANG or not isinstance(d.get("id_bai"), str) or not RE_ID.fullmatch(d["id_bai"]):
            return False
        if not isinstance(d.get("ngay"), str) or not RE_NGAY.fullmatch(d["ngay"]):
            return False
        dt.date.fromisoformat(d["ngay"])
        if not isinstance(d.get("gio_dang"), str) or not RE_GIO.fullmatch(d["gio_dang"]) or tg(d["gio_dang"]) is None:
            return False
        if d.get("link") is not None and not (isinstance(d["link"], str) and d["link"].startswith("https://")):
            return False
        for c in ("tieu_de", "khuon", "dang"):
            if d.get(c) is not None and not isinstance(d[c], str):
                return False
        for c in BIGINT:
            v = d.get(c)
            if v is not None and not (isinstance(v, int) and not isinstance(v, bool) and 0 <= v < 2 ** 53):
                return False
        for c in NUMERIC:
            v = d.get(c)
            if v is not None and not (isinstance(v, (int, float)) and not isinstance(v, bool) and math.isfinite(v) and 0 <= v < 1e7):
                return False
    except (ValueError, TypeError, AttributeError):
        return False
    return True


def hop_le_kenh(k):
    v = k.get("nguoi_theo_doi")
    return k.get("nen_tang") in NEN_TANG and (v is None or (isinstance(v, int) and not isinstance(v, bool) and 0 <= v < 2 ** 53))


def _dong(ten, id_bai, gio, dang, do_dai, la_chu, link, tieu_de, **so_):
    """Dong gui sg-cong. Sai dinh dang id/gio -> None (dem la loi bai) de KHONG lam cong tra 400 ca lo."""
    id_bai = str(id_bai or "")
    if not RE_ID.fullmatch(id_bai) or gio is None:
        return None
    gio = gio.replace(microsecond=0)
    d = {"nen_tang": ten, "id_bai": id_bai, "ngay": gio.astimezone(chung.VN).date().isoformat(), "gio_dang": chung.iso(gio),
         "dang": dang[:40] if dang else None, "khuon": nhan_khuon(dang, do_dai, la_chu)[:60], "link": _link(link),
         "tieu_de": tieu_de}
    for c in BIGINT:
        d[c] = _so(so_.get(c), True)
    for c in NUMERIC:
        d[c] = _so(so_.get(c))
    return d if hop_le_cong(d) else None       # vi pham gioi han cong -> bo bai (dem loi_bai), khong de ca lo bi 400


def _lay(url, *, headers=None, params=None):
    """GET -> (ok, json_dict, mo_ta_loi_da_che). Ma gioi han toc do -> LoiGioiHan. Loi mang -> ok False."""
    try:
        r = http.gui("GET", url, headers=headers, params=params, timeout=60)
    except http.LoiMang as e:
        return False, {}, str(e)
    try:
        j = json.loads(r.text)
    except ValueError:
        j = None
    thieu_json = not isinstance(j, dict)       # 200 ma than khong phai JSON object -> loi
    j = {} if thieu_json else j
    err = j.get("error")
    ma, msg, ly_do = None, "", set()
    if isinstance(err, dict):
        ma = err.get("code") if isinstance(err.get("code"), (int, str)) else None
        msg = str(err.get("message") or "")
        ly_do = {str(x.get("reason")) for x in (err.get("errors") or []) if isinstance(x, dict)}
    if r.status == 429 or ma in MA_GIOI_HAN or ly_do & LY_DO_GIOI_HAN:
        raise LoiGioiHan(f"gioi han toc do (HTTP {r.status}, ma {ma})")
    if 200 <= r.status < 300 and err is None and not thieu_json:
        return True, j, ""
    if thieu_json and 200 <= r.status < 300:
        return False, j, f"HTTP {r.status} than khong phai JSON object"
    return False, j, chung.cat(f"HTTP {r.status} ma {ma} {msg}", 160)


def _phan_trang(url, params, tien_to, headers=None):
    """Sinh tung phan tu 'data' theo paging.next, duyet HET trang (API chua chac sap giam dan); toi da TOI_DA_TRANG."""
    for _ in range(TOI_DA_TRANG):
        ok, j, mo_ta = _lay(url, headers=headers, params=params)
        if not ok:
            raise LoiKenh(mo_ta)
        yield from (x for x in (j.get("data") or []) if isinstance(x, dict))
        nxt = (j.get("paging") or {}).get("next")
        if not isinstance(nxt, str) or not nxt.startswith(tien_to):
            return
        url, params = nxt, None
    raise LoiKenh(f"qua {TOI_DA_TRANG} trang")


class Ctx:
    def __init__(self, cong, bat_dau, bay_gio, dong_so):
        self.cong, self.bat_dau, self.bay_gio = cong, bat_dau, bay_gio
        self.so = dong_so
        self.tra = {(r["kenh"], str(r["id_bai"])): r for r in dong_so}
        self.do_dai = {}          # (ngay SO, dang) -> do dai giay cua video Facebook, IG dung lai

    def token(self, kenh):
        t = self.cong.doc_token(kenh)
        du = t.get("du_lieu") if isinstance(t, dict) else None
        if not isinstance(du, dict) or not du:
            raise LoiKenh(f"chua co token {kenh}")
        chung.dang_ky_tu_du_lieu(du)
        return du

    def dang(self, kenh, id_bai):
        return (self.tra.get((kenh, str(id_bai))) or {}).get("dang")

    def khoa_do_dai(self, kenh, id_bai):
        r = self.tra.get((kenh, str(id_bai)))
        return (r.get("ngay"), r.get("dang")) if r and r.get("dang") else None


# ---------- tung kenh ----------
def _co_lap(kq, fn, *a):
    """Loi bat ngo khi xu ly MOT bai -> bo bai, dem loi_bai. Gioi han toc do van dung ca kenh."""
    try:
        fn(*a)
    except LoiGioiHan:
        raise
    except Exception:
        kq.loi_bai += 1


def _insights(url, params, kq):
    """Insights cua mot bai -> list 'data' hoac None (da dem loi_bai neu loi / rong)."""
    ok, ij, _ = _lay(url, params=params)
    d = ij.get("data") if ok else None
    if not isinstance(d, list) or not d:
        kq.loi_bai += 1
        return None
    return d


def _theo_doi(kq, ten, ok, gia_tri, mo_ta=""):
    """Doc nguoi theo doi loi/khong doc duoc -> LoiKenh (goi SAU khi da do bai de phan dat van duoc ghi)."""
    n = _so(gia_tri, True) if ok else None
    if n is None or not hop_le_kenh({"nen_tang": ten, "nguoi_theo_doi": n}):
        raise LoiKenh(f"nguoi theo doi {ten}: {mo_ta or 'khong doc duoc'}")
    kq.kenh.append({"nen_tang": ten, "nguoi_theo_doi": n})


def _fb_bai(ctx, kq, v, pt):
    gio = tg(v.get("created_time"))
    if v.get("published") is False or (gio is not None and gio < ctx.bat_dau):
        return
    vid = str(v.get("id") or "")
    if gio is None or not RE_ID.fullmatch(vid):
        kq.loi_bai += 1
        return
    d = _insights(f"{G}/{vid}/video_insights", {"access_token": pt}, kq)       # loi/rong: BO bai (dashboard giu lan do tot truoc)
    if d is None:
        return
    plays = _so(_ins(d, "fb_reels_total_plays"))
    if plays is None:
        plays = _so(_ins(d, "total_video_views"))
    if plays is None:                  # khong co luot xem = khong do duoc
        kq.loi_bai += 1
        return
    vt = _so(_ins(d, "post_video_view_time"))
    dai = _so(v.get("length"))
    dang = ctx.dang("fb", vid)
    link = v.get("permalink_url")
    if isinstance(link, str) and link.startswith("/"):
        link = "https://www.facebook.com" + link
    row = _dong("Facebook", vid, gio, dang, dai, False, link, _dong1(v.get("description")),
                luot_xem=plays, thich=_tong(v.get("likes")), binh_luan=_tong(v.get("comments")),
                xem_tb_giay=round(vt / 1000 / plays, 1) if plays and vt is not None else None, do_dai_giay=dai)
    kq.them(row)
    khoa = ctx.khoa_do_dai("fb", vid)
    if row and khoa and dai:
        ctx.do_dai[khoa] = dai


def do_facebook(ctx, kq):
    t = ctx.token("fb")
    page, pt = t["page_id"], t["page_token"]
    fields = ("id,description,created_time,length,permalink_url,published,"
              "likes.summary(true).limit(0),comments.summary(true).limit(0)")
    for v in _phan_trang(f"{G}/{page}/videos", {"fields": fields, "limit": 100, "access_token": pt}, GOC_FB):
        _co_lap(kq, _fb_bai, ctx, kq, v, pt)
    ok, j, mo_ta = _lay(f"{G}/{page}", params={"fields": "followers_count", "access_token": pt})
    _theo_doi(kq, "Facebook", ok, j.get("followers_count"), mo_ta)


def _ig_bai(ctx, kq, m, pt):
    gio = tg(m.get("timestamp"))
    if gio is not None and gio < ctx.bat_dau:
        return
    mid = str(m.get("id") or "")
    if gio is None or not RE_ID.fullmatch(mid):
        kq.loi_bai += 1
        return
    metric = "views,reach,likes,comments,shares,saved"
    if m.get("media_product_type") == "REELS":
        metric += ",ig_reels_avg_watch_time"
    d = _insights(f"{G}/{mid}/insights", {"metric": metric, "access_token": pt}, kq)
    if d is None:
        return
    if _so(_ins(d, "views")) is None:
        kq.loi_bai += 1
        return
    aw = _so(_ins(d, "ig_reels_avg_watch_time"))      # mili giay
    khoa = ctx.khoa_do_dai("ig", mid)
    kq.them(_dong("Instagram", mid, gio, ctx.dang("ig", mid), None, m.get("media_type") in ("IMAGE", "CAROUSEL_ALBUM"),
                  m.get("permalink"), _dong1(m.get("caption")), luot_xem=_ins(d, "views"), thich=_ins(d, "likes"),
                  binh_luan=_ins(d, "comments"), chia_se=_ins(d, "shares"), luu=_ins(d, "saved"),
                  xem_tb_giay=round(aw / 1000, 1) if aw is not None else None,
                  do_dai_giay=ctx.do_dai.get(khoa) if khoa else None))


def do_instagram(ctx, kq):
    t = ctx.token("ig")
    iguid, pt = t["ig_user_id"], t["page_token"]
    fields = "id,caption,media_type,media_product_type,timestamp,permalink"
    for m in _phan_trang(f"{G}/{iguid}/media", {"fields": fields, "limit": 100, "access_token": pt}, GOC_FB):
        _co_lap(kq, _ig_bai, ctx, kq, m, pt)
    ok, j, mo_ta = _lay(f"{G}/{iguid}", params={"fields": "followers_count", "access_token": pt})
    _theo_doi(kq, "Instagram", ok, j.get("followers_count"), mo_ta)


def _th_bai(ctx, kq, p, tok):
    gio = tg(p.get("timestamp"))
    if gio is not None and gio < ctx.bat_dau:
        return
    pid = str(p.get("id") or "")
    if gio is None or not RE_ID.fullmatch(pid):
        kq.loi_bai += 1
        return
    d = _insights(f"{TH}/{pid}/insights", {"metric": "views,likes,replies,reposts,quotes", "access_token": tok}, kq)
    if d is None:
        return
    if _so(_ins(d, "views")) is None:
        kq.loi_bai += 1
        return
    chia_se = (_so(_ins(d, "reposts")) or 0) + (_so(_ins(d, "quotes")) or 0)
    kq.them(_dong("Threads", pid, gio, ctx.dang("threads", pid), None, p.get("media_type") != "VIDEO",
                  p.get("permalink"), _dong1(p.get("text")), luot_xem=_ins(d, "views"), thich=_ins(d, "likes"),
                  binh_luan=_ins(d, "replies"), chia_se=chia_se))


def do_threads(ctx, kq):
    t = ctx.token("threads")
    uid, tok = t["threads_user_id"], t["token"]
    fields = "id,text,media_type,permalink,timestamp"
    for p in _phan_trang(f"{TH}/{uid}/threads", {"fields": fields, "limit": 100, "access_token": tok}, GOC_TH):
        _co_lap(kq, _th_bai, ctx, kq, p, tok)
    ok, j, mo_ta = _lay(f"{TH}/{uid}/threads_insights", params={"metric": "followers_count", "access_token": tok})
    _theo_doi(kq, "Threads", ok, _ins(j.get("data"), "followers_count") if ok else None, mo_ta)


_RE_THOI_LUONG = re.compile(r"P(?:(\d+)D)?(?:T(?:(\d+)H)?(?:(\d+)M)?(?:(\d+(?:\.\d+)?)S)?)?")


def giay_iso(s):
    m = _RE_THOI_LUONG.fullmatch(s) if isinstance(s, str) else None
    if not m or not any(m.groups()):
        return None
    d, h, p, g = (float(x) if x else 0 for x in m.groups())
    return d * 86400 + h * 3600 + p * 60 + g or None      # 0 giay (P0D, live) -> khong ro


def _yt_bai(ctx, kq, it, an):
    vid = str(it.get("id") or "")
    sn, st = it.get("snippet") or {}, it.get("statistics") or {}
    if _so(st.get("viewCount")) is None:
        kq.loi_bai += 1
        return
    gio = tg(sn.get("publishedAt"))
    dai = giay_iso((it.get("contentDetails") or {}).get("duration"))
    a = an.get(vid) or {}
    kq.them(_dong("YouTube", vid, gio, ctx.dang("youtube", vid), dai, False,
                  f"https://www.youtube.com/shorts/{vid}" if dai is not None and dai <= 180
                  else f"https://www.youtube.com/watch?v={vid}", _dong1(sn.get("title")),
                  luot_xem=st.get("viewCount"), thich=st.get("likeCount", 0), binh_luan=st.get("commentCount", 0),
                  chia_se=a.get("shares"), theo_doi_moi=a.get("subscribersGained"), xem_tb_giay=a.get("averageViewDuration"),
                  do_dai_giay=dai))


def do_youtube(ctx, kq):
    t = ctx.token("youtube")
    h = {"Authorization": "Bearer " + yt.lam_moi_access(t)[0]}
    ok, j, mo_ta = _lay(f"{YT}/channels", headers=h, params={"part": "contentDetails,statistics", "mine": "true"})
    items = j.get("items") if ok else None
    if not isinstance(items, list) or not items or not isinstance(items[0], dict):
        raise LoiKenh(f"channels: {mo_ta or 'khong co kenh'}")
    kenh = items[0]
    try:
        uploads = kenh["contentDetails"]["relatedPlaylists"]["uploads"]
    except (KeyError, TypeError):
        raise LoiKenh("channels: khong co uploads playlist") from None
    sub = _so((kenh.get("statistics") or {}).get("subscriberCount"), True) if isinstance(kenh.get("statistics"), dict) else None
    ids, trang = [], None
    for _ in range(TOI_DA_TRANG + 1):
        if _ == TOI_DA_TRANG:
            raise LoiKenh(f"playlistItems: qua {TOI_DA_TRANG} trang")
        p = {"part": "contentDetails,status", "playlistId": uploads, "maxResults": 50}
        if trang:
            p["pageToken"] = trang
        ok, j, mo_ta = _lay(f"{YT}/playlistItems", headers=h, params=p)
        if not ok:
            raise LoiKenh(f"playlistItems: {mo_ta}")
        for it in j.get("items") or []:
            if not isinstance(it, dict):
                continue
            cd = it.get("contentDetails") if isinstance(it.get("contentDetails"), dict) else {}
            if (it.get("status") or {}).get("privacyStatus") != "public" or not cd.get("videoId"):
                continue
            gio = tg(cd.get("videoPublishedAt"))
            if gio is not None and gio >= ctx.bat_dau:
                ids.append(str(cd["videoId"]))
        trang = j.get("nextPageToken")
        if not trang:
            break
    bay = ctx.bay_gio
    bd = (ctx.bat_dau.astimezone(dt.timezone.utc) - dt.timedelta(days=1)).date()
    try:      # Analytics tinh ngay theo gio Thai Binh Duong
        kt = bay.astimezone(ZoneInfo("America/Los_Angeles")).date()
    except ZoneInfoNotFoundError:
        kt = (bay.astimezone(dt.timezone.utc) - dt.timedelta(hours=8)).date()
    for i in range(0, len(ids), 50):
        lo = ids[i:i + 50]
        ok, vj, mo_ta = _lay(f"{YT}/videos", headers=h, params={"part": "statistics,contentDetails,snippet", "id": ",".join(lo)})
        if not ok:
            raise LoiKenh(f"videos: {mo_ta}")
        an = {}
        if bd <= kt:
            ok, aj, _ = _lay(YT_AN, headers=h, params={
                "ids": "channel==MINE", "startDate": bd.isoformat(), "endDate": kt.isoformat(), "dimensions": "video",
                "metrics": "views,averageViewDuration,subscribersGained,shares", "filters": "video==" + ",".join(lo)})
            if ok:
                ten = [c.get("name") for c in aj.get("columnHeaders") or [] if isinstance(c, dict)] or \
                    ["video", "views", "averageViewDuration", "subscribersGained", "shares"]
                for r in aj.get("rows") or []:
                    if not isinstance(r, list):
                        continue
                    d = dict(zip(ten, r))
                    if d.get("views"):          # views = 0: Analytics tre 24-48 h, coi nhu chua co so
                        an[d.get("video")] = d
            else:                        # khong co so Analytics: bo ca lo (dashboard giu lan do tot truoc)
                kq.loi_bai += len(lo)
                continue
        for it in vj.get("items") or []:
            if isinstance(it, dict):
                _co_lap(kq, _yt_bai, ctx, kq, it, an)
    _theo_doi(kq, "YouTube", True, sub, "khong doc duoc subscriberCount")


def _id_tai_khoan(p):
    """Cac id tai khoan ghi tren bai Zernio (accountId, account, platforms[].accountId); khong co -> rong."""
    ids = set()

    def them(v):
        if isinstance(v, dict):
            v = v.get("_id") or v.get("id")
        if isinstance(v, str) and v:
            ids.add(v)
    them(p.get("accountId"))
    them(p.get("account"))
    for x in p.get("platforms") or []:
        if isinstance(x, dict):
            them(x.get("accountId"))
    return ids


def do_tiktok(ctx, kq):
    khoa = os.environ.get("ZERNIO_KHOA", "").strip()
    if not khoa:
        raise LoiKenh("thieu env ZERNIO_KHOA")
    chung.dang_ky_bi_mat(khoa)
    h = {"Authorization": "Bearer " + khoa}
    posts, accounts, pages, trang = [], [], 1, 1
    while trang <= pages:
        if trang > TOI_DA_TRANG:
            raise LoiKenh(f"analytics: qua {TOI_DA_TRANG} trang")
        ok, j, mo_ta = _lay(f"{ZER}/analytics", headers=h, params={"platform": "tiktok", "limit": 100, "page": trang})
        if not ok:
            raise LoiKenh(f"analytics: {mo_ta}")
        posts += [p for p in (j.get("posts") or []) if isinstance(p, dict)]
        if trang == 1:
            accounts = [a for a in (j.get("accounts") or []) if isinstance(a, dict)]
            pg = (j.get("pagination") or {}).get("pages")
            pages = pg if isinstance(pg, int) and pg > 0 else 1
        trang += 1
    acc = os.environ.get("ZERNIO_TIKTOK_ACC", "").strip() or zernio.ACC_MAC_DINH
    dich = {acc}
    zp = []
    for p in posts:
        gio = tg(p.get("publishedAt"))
        thuoc = _id_tai_khoan(p)
        # Bai KHONG ghi tai khoan van nhan: endpoint analytics theo khoa, hien chi co 1 tai khoan TikTok.
        if thuoc and not (thuoc & dich):        # co ghi tai khoan va khong phai tai khoan dich -> bo
            continue
        if p.get("status") == "published" and gio is not None and gio >= ctx.bat_dau:
            zp.append((gio, p))
    # ghep khuon: luot 1 trung id (latePostId hoac _id), luot 2 bai hop thu theo gio gan nhat <= 90 phut, moi dong so mot lan
    cho = [r for r in ctx.so if r.get("kenh") == "tiktok"]
    khop = {}
    for _, p in zp:
        for r in cho:
            if str(r["id_bai"]) in (p.get("latePostId"), p.get("_id")):
                khop[p.get("_id")] = r
                cho.remove(r)
                break
    cap = []
    for gio, p in zp:
        if p.get("_id") in khop:
            continue
        for i, r in enumerate(cho):
            g2 = tg(r.get("gio_cong_khai"))
            if g2 is not None:
                cap.append((abs((g2 - gio).total_seconds()), str(p.get("_id")), i))
    dung = set()
    for lech, pid, i in sorted(cap):
        if lech <= 5400 and pid not in khop and i not in dung:
            khop[pid] = cho[i]
            dung.add(i)
    for gio, p in zp:
        _co_lap(kq, _tt_bai, kq, gio, p, khop)
    ds = [a for a in accounts if a.get("_id") in dich]
    _theo_doi(kq, "TikTok", bool(ds), ds[0].get("followersCount") if ds else None, "khong thay tai khoan dich")


def _tt_bai(kq, gio, p, khop):
    r = khop.get(p.get("_id")) or {}
    an = p.get("analytics") if isinstance(p.get("analytics"), dict) else {}
    au = an.get("audienceTypes") if isinstance(an.get("audienceTypes"), dict) else {}
    hoan_tat = _so(an.get("completionRate"))
    nl = _so(au.get("nonFollower"))
    link = p.get("platformPostUrl")
    kq.them(_dong("TikTok", p.get("_id"), gio, r.get("dang"), _so(an.get("videoDurationSeconds")), False,
                  link.split("?")[0] if isinstance(link, str) else None, _dong1(p.get("content")),
                  luot_xem=an.get("views"), thich=an.get("likes"), binh_luan=an.get("comments"), chia_se=an.get("shares"),
                  luu=an.get("saves"), theo_doi_moi=an.get("follows"), do_dai_giay=an.get("videoDurationSeconds"),
                  nguoi_la_pct=round(100 * nl, 1) if nl is not None else None,
                  xem_het_pct=round(100 * hoan_tat, 1) if hoan_tat is not None and an.get("views") else None))


KENH = (("Facebook", do_facebook), ("Instagram", do_instagram), ("Threads", do_threads),
        ("YouTube", do_youtube), ("TikTok", do_tiktok))     # Facebook truoc Instagram (do_dai dung chung)


def qua_nguong(so_bai, loi_bai):
    return loi_bai > 0 and loi_bai / (so_bai + loi_bai) > NGUONG_LOI_BAI


def chay_kenh(ten, fn, ctx):
    kq = KetQua(ten)
    try:
        fn(ctx, kq)
    except Exception as e:
        kq.loi_kenh = chung.cat(f"{type(e).__name__}: {e}", 200)
    if not kq.loi_kenh and qua_nguong(len(kq.bai), kq.loi_bai):
        kq.loi_kenh = f"qua nhieu loi bai ({kq.loi_bai}/{len(kq.bai) + kq.loi_bai})"
    chung.log(f"{ten}: {len(kq.bai)} bai, {kq.loi_bai} loi bai" + (f", LOI KENH: {kq.loi_kenh}" if kq.loi_kenh else ""))
    return kq


def ghi(cong, do_luc, bai, kenh):
    """Chia lo 500; kenh chi o lo dau. Tra danh sach loi (da che)."""
    lo_bai = [bai[i:i + LO_GHI] for i in range(0, len(bai), LO_GHI)] or [[]]
    loi = []
    for i, lo in enumerate(lo_bai):
        k = kenh if i == 0 else []
        if not lo and not k:
            continue
        try:
            cong.goi("ghi_so_lieu", do_luc=do_luc, bai=lo, kenh=k)
        except Exception as e:
            loi.append(chung.cat(f"ghi lo {i + 1}: {type(e).__name__}: {e}", 200))
    return loi


def chay(che_do, so_ngay, cong, ra=None):
    bay = chung.bay_gio().replace(microsecond=0)
    bat_dau = max(DAU_CUA_SO, bay - dt.timedelta(days=so_ngay))
    chung.log(f"do so lieu: che do {che_do}, tu {bat_dau.astimezone(chung.VN).date().isoformat()} (VN)")
    dong_so, ngay = [], bat_dau.astimezone(chung.VN).date()
    while ngay <= bay.astimezone(chung.VN).date():      # cong khong phan trang (gioi han 1000 dong) -> doc tung ngay
        dong_so += cong.doc_dang(ngay.isoformat(), ngay.isoformat(), "that")
        ngay += dt.timedelta(days=1)
    dong_so = [r for r in dong_so if r.get("trang_thai") == "da_dang" and r.get("id_bai") and r.get("kenh")]
    ctx = Ctx(cong, bat_dau, bay, dong_so)
    kqs = [chay_kenh(ten, fn, ctx) for ten, fn in KENH]
    bai, kenh = {}, {}
    for kq in kqs:
        for d in kq.bai:
            bai[(d["nen_tang"], d["id_bai"])] = d      # trung khoa trong cung lo -> cong upsert se loi, giu ban sau
        for k in kq.kenh:
            kenh[k["nen_tang"]] = k
    bai, kenh = list(bai.values()), list(kenh.values())
    do_luc = chung.iso(bay)
    n_loi = sum(1 for kq in kqs if kq.loi_kenh)
    loi_ghi = []
    if che_do == "that":
        loi_ghi = ghi(cong, do_luc, bai, kenh)
    else:
        chung.log("che do thu: khong ghi")
    if ra:
        with open(ra, "w", encoding="utf-8") as f:
            json.dump({"do_luc": do_luc, "bai": bai, "kenh": kenh}, f, ensure_ascii=False)
    chung.log(f"Tong: {len(bai)} bai, {len(kenh)} nguoi theo doi kenh, {n_loi} kenh loi" + (f", {len(loi_ghi)} lo ghi loi" if loi_ghi else ""))
    if n_loi or loi_ghi:
        tom_tat = "; ".join([f"{kq.ten}: {kq.loi_kenh}" for kq in kqs if kq.loi_kenh] + loi_ghi)
        _bao_loi(che_do, f"Đo số liệu: {n_loi} kênh lỗi" if n_loi else "Đo số liệu: lỗi ghi sổ", tom_tat)
        return 1
    return 0


def _bao_loi(che_do, tieu_de, noi_dung):
    """Chi che do that. ntfy gui THANH CONG + co env DA_BAO_FILE -> ghi file co de buoc cuoi workflow khong bao lai."""
    if che_do != "that":
        return
    if ntfy.loi(tieu_de, noi_dung) is True and os.environ.get("DA_BAO_FILE"):
        try:
            open(os.environ["DA_BAO_FILE"], "w").close()
        except OSError:
            pass


def main(argv=None, cong=None):
    ap = argparse.ArgumentParser(description="Do so lieu song Sang Game")
    ap.add_argument("--che-do", required=True, choices=["thu", "that"])
    ap.add_argument("--so-ngay", type=int, default=30)
    ap.add_argument("--ra", default=None)
    a = ap.parse_args(argv)
    if a.so_ngay < 1:
        ap.error("--so-ngay phai >= 1")
    try:
        cong = cong or so.Cong()
    except so.LoiCong as e:
        chung.log_loi(f"do_so: {e}")
        _bao_loi(a.che_do, "Đo số liệu: thiếu khoá cổng", str(e))
        return 2
    try:
        return chay(a.che_do, a.so_ngay, cong, a.ra)
    except Exception as e:
        mo_ta = chung.cat(f"{type(e).__name__}: {e}", 300)
        chung.log_loi(f"do_so: loi bat ngo: {mo_ta}")
        _bao_loi(a.che_do, "Đo số liệu: lỗi bất ngờ", mo_ta)
        return 1


if __name__ == "__main__":
    sys.exit(main())
