"""Threads (@sangamecomvn): BAI CHU viet rieng, 2 bai/ngay (Hao chot 12/10/2026; Threads thoi dang lai video reels).
CLI:  python -m dang.threads_chu --loai sang|chieu|binh_chon --ngay YYYY-MM-DD --che-do thu|that
  sang  (09:30 VN): nguon manifest Release v-<ngay>-tin-nhanh. So: game re nhat trong kiem_lai (gia VND, vung).
        Anh = bia PS Store cua DUNG game do (image.api.playstation.com); khong lay duoc -> bia-reels.jpg Release tin-nhanh; Pages hong -> CHI CHU.
  chieu (17:00 VN): bai CO ANH (bia-reels.jpg qua GitHub Pages), nguon v-<ngay>-keo-thom-2. Pages hong -> dang CHI CHU, khong bo bai.
  binh_chon (13:00 VN): bai TEXT + poll (poll_attachment). Nguon (tuy chon) manifest v-<ngay>-top5: game hang 1; thieu Release / gia lech ->
        bo >= 8 cau co dinh (xoay theo ngay). Khoa so sg_dang = 'binh-chon' (dang_bai) KHAC nguon Release (dang_nguon).
Ma thoat: 0 xong · 1 loi · 3 khong dang (thieu Release/manifest, hoac gia/han lech) - chua ghi so, co the chay lai.
che_do=thu: CHI IN bai (doc Release + kiem gia + kiem URL anh, chi doc), khong token, khong ghi so, khong tao container, khong ntfy.

Tai lieu Threads API da doc (12/10/2026): https://developers.facebook.com/docs/threads/posts
  POST /{threads-user-id}/threads  media_type=TEXT|IMAGE|VIDEO, text (<= 500 ky tu), image_url (IMAGE), topic_tag (1-50 ky tu, khong '.' va '&'),
  roi POST /{id}/threads_publish creation_id=... sau ~30 giay. topic_tag CO trong API -> gan qua tham so (khong chen #hashtag vao chu).
Nguon huong dan noi dung: creators.instagram.com/threads (chu rieng, hoi lai de mo hoi thoai, khong engagement bait).
Quy uoc loi nhu x.py: giu quyen bang cong.giu_dang TRUOC moi goi mang Threads; loi sau publish = khong_ro (khong dang lai)."""
import argparse
import datetime as dt
import hashlib
import os
import re
import sys
import tempfile
import urllib.parse

from . import chay, chung, gia, http, manifest, ntfy, site, threads
from .chung import LoiDang
from .so import Cong, LoiCong

TOPIC_TAG = "PlayStation"
NGUON = {"sang": "tin-nhanh", "chieu": "keo-thom-2", "binh_chon": "top5"}      # dang_nguon: Release doc manifest
BAI = {"sang": "tin-nhanh", "chieu": "keo-thom-2", "binh_chon": "binh-chon"}   # dang_bai: khoa dong sg_dang (giu_dang / cap_nhat_dang)
GIO_DANG = {"sang": "09:30", "chieu": "17:00", "binh_chon": "13:00"}
UA = gia.UA
ANH_PS_HOST = "image.api.playstation.com"
TRAN = 400          # Threads cho 500; chua du dia
CHO_TRUOC_PUBLISH = 30   # tai lieu: ~30 giay
TU_CAM = ("bình luận", "binh luan", "tag bạn", "tag ban", "share", "chia sẻ", "giveaway", "tặng", "http", "www.", "!!!", "#")
VUNG = {"en-hk": "Hồng Kông", "en-us": "Mỹ", "en-sg": "Singapore", "en-th": "Thái Lan", "en-id": "Indonesia", "en-in": "Ấn Độ"}

# ---------------------------------------------------------------- mau cau (hang thuan, khong goi AI)
MO_SANG = (   # pham vi = CA ban tin (kiem_lai gom moi game co gia trong ban tin da kiem lai gia) - khong noi "nhom giam sau", khong so tong hop
    "Trong bản tin giảm giá sáng nay, món rẻ nhất là {ten}, {gia} ở Store {vung}.",
    "Bản tin giảm giá sáng nay, rẻ nhất là {ten}, chỉ {gia} ở Store {vung}.",
    "Lướt qua bản tin giảm giá sáng nay, giá thấp nhất thuộc về {ten} với {gia} ở Store {vung}.",
    "Sáng nay trong bản tin giảm giá, {ten} là món rẻ nhất, còn {gia} ở Store {vung}.",
)
HOI_SANG = (
    "Đợt này mọi người đã nhắm game nào chưa, hay đang chờ giảm sâu thêm?",
    "Bạn định mua ngay món nào trong đợt này, hay để dành chờ đợt sau?",
    "Trong bản tin hôm nay, game nào bạn thấy đáng mua nhất?",
    "Game nào đang nằm trong danh sách chờ của bạn, và giá này đã đủ để bạn chốt chưa?",
)
MO_CHIEU = (   # khong noi % giam (gia.kiem_lai khong kiem gia goc)
    "{ten} đang có giá {gia} ở PS Store {vung}.",
    "Chiều nay, {ten} có giá {gia} ở PS Store {vung}.",
    "Vừa kiểm lại giá: {ten} còn {gia} ở PS Store {vung}.",
    "{ten} đang xuống {gia} ở PS Store {vung}.",
)
HOI_CHIEU = (
    "Ai chơi rồi thấy game này đáng mua ở mức giá này không, hay nên chờ giảm sâu hơn?",
    "Bạn sẽ mua ngay ở giá này hay chờ thêm đợt giảm sau?",
    "Ai đã chơi rồi, game này có đáng tiền ở mức này không?",
    "Mua ở Store nước ngoài thế này bạn thấy tiện không, hay vẫn ngại khoản thẻ thanh toán?",
)


# Bo cau binh chon CO DINH (khong phu thuoc Release/gia): y kien that cua nguoi choi PlayStation Viet, khong bait/giveaway.
# Moi lua chon <= 25 ky tu, 2-4 lua chon. 10 cau > 7 ngay -> xoay theo toordinal khong lap trong 7 ngay.
BINH_CHON_CO_DINH = (
    ("Bạn đang dùng gói PS Plus nào?", ("Essential", "Extra", "Premium", "Chưa đăng ký")),
    ("Khi mua game, bạn ưu tiên điều gì nhất?", ("Phụ đề tiếng Việt", "Chơi chung nhiều người", "Giá rẻ", "Cốt truyện, đồ họa")),
    ("Bạn mua game PlayStation bản digital hay đĩa?", ("Digital", "Đĩa", "Tùy từng game")),
    ("Game mới ra, bạn mua ngay hay chờ sale lớn?", ("Mua ngay khi ra mắt", "Chờ sale lớn", "Chờ thật rẻ mới mua")),
    ("Thể loại game bạn chơi nhiều nhất?", ("Hành động, phiêu lưu", "Nhập vai (RPG)", "Thể thao, đua xe", "Bắn súng, sinh tồn")),
    ("Bạn thường chơi game PlayStation với ai?", ("Một mình", "Bạn bè, người thân", "Online với người lạ")),
    ("Một game đáng mua với bạn thường ở mức giá nào?", ("Dưới 300 nghìn", "300 – 600 nghìn", "600 nghìn – 1 triệu", "Trên 1 triệu")),
    ("Bạn đang chơi game trên máy nào?", ("PS5", "PS4", "Cả PS4 lẫn PS5")),
    ("Bạn đã mua game ở PS Store nước ngoài chưa?", ("Rồi, thường xuyên", "Rồi, thỉnh thoảng", "Chưa, đang tìm hiểu", "Chưa, không định mua")),
    ("Phụ đề tiếng Việt quan trọng với bạn cỡ nào?", ("Rất quan trọng", "Có thì tốt", "Không quan trọng")),
)
LUA_CHON_TOP1 = ("Mua luôn", "Chờ giảm thêm", "Không hứng thú")


# ---------------------------------------------------------------- ham thuan
def gon_ten(t):
    """Ten game de dua vao bai: bo ®™, ngoac, hau to nen tang."""
    t = re.sub(r"[®™]", "", t or "")
    t = re.sub(r"\s*\([^()]*\)", "", t)
    t = re.sub(r"\s+for PS[45]$", "", t.strip())
    t = re.sub(r"\s+PS[45](?:\s*&\s*PS[45])?$", "", t.strip())
    return chung.bo_duoi_nen_tang(re.sub(r"\s+", " ", t).strip())


def tien(n):
    return f"{int(n):,}".replace(",", ".") + "đ"


def han_vn(ms):
    d = dt.datetime.fromtimestamp(int(ms) / 1000, chung.VN)
    return f"{d:%H:%M} ngày {d.day:02d}/{d.month:02d}"


def _chon(mau, khoa):
    """Doi ngay lien nhau -> mau khac nhau (buoc nguyen to cung do dai mau)."""
    return mau[khoa % len(mau)]


def _so_ngay(ngay):
    return dt.date.fromisoformat(ngay).toordinal()


def _deal_ok(m):
    return isinstance(m, dict) and isinstance(m.get("gia_vnd"), (int, float)) and m["gia_vnd"] > 0 and m.get("ten") and m.get("pid") \
        and m.get("loc") in VUNG and str(m.get("endTime") or "").isdigit()


def re_nhat(muc):
    ung = [m for m in (muc or []) if _deal_ok(m)]
    if not ung:
        raise LoiDang("manifest khong co muc kiem_lai dung duoc (gia_vnd/vung/endTime) - khong soan bai")
    return min(ung, key=lambda m: m["gia_vnd"])


def kiem_van(text):
    """Chan cung truoc khi dang: do dai, tu cam (engagement bait / link), viet hoa ca cau, phai co cau hoi."""
    t = text.lower()
    for c in TU_CAM:
        if c in t:
            raise LoiDang(f"bai Threads chua '{c}' - khong dang")
    if len(text) > TRAN:
        raise LoiDang(f"bai Threads dai {len(text)} > {TRAN}")
    if "?" not in text:
        raise LoiDang("bai Threads khong co cau hoi")
    for cau in re.split(r"(?<=[.?])\s+", text):
        chu = re.sub(r"[^A-Za-zÀ-ỹ]", "", cau)
        if len(chu) >= 8 and chu.isupper():
            raise LoiDang("bai Threads co ca cau viet hoa")
    return text


def _poll(lua_chon):
    return threads.kiem_poll(dict(zip(threads.POLL_KHOA, lua_chon)))


def cau_co_dinh(ngay):
    """-> (text, poll) tu bo co dinh, xoay theo toordinal ngay (10 cau: 7 ngay lien tiep khong lap). Khong phu thuoc Release / gia."""
    cau, lua_chon = BINH_CHON_CO_DINH[_so_ngay(ngay) % len(BINH_CHON_CO_DINH)]
    return kiem_van(cau), _poll(lua_chon)


def soan_binh_chon(man, ngay):
    """-> (text, poll, muc_can_kiem_lai). Co manifest Top 5 dung duoc: cau ve game hang 1 (kiem_lai[0]) -> muc=[deal] (phai kiem gia).
    Khong co / khong dung duoc -> cau co dinh, muc=[] (khong nhac gia nen khong can kiem)."""
    muc = (man or {}).get("kiem_lai") or []
    if muc and _deal_ok(muc[0]):
        deal = muc[0]
        text = (f"{gon_ten(deal['ten'])} đứng đầu danh sách Top 5 hôm nay, còn {tien(deal['gia_vnd'])} ở Store {VUNG[deal['loc']]}. "
                f"Bạn sẽ làm gì?")
        return kiem_van(text), _poll(LUA_CHON_TOP1), [deal]
    text, poll = cau_co_dinh(ngay)
    return text, poll, []


def _ghep(*phan):
    return " ".join(p for p in phan if p)


def soan_sang(man, ngay, so_my=True):
    """-> (text, muc_can_kiem_lai). Chi chu. Chi dung ten, gia VND, vung cua game re nhat trong kiem_lai (da kiem lai gia)."""
    deal = re_nhat(man.get("kiem_lai"))
    n = _so_ngay(ngay)
    mo = _chon(MO_SANG, n).format(ten=gon_ten(deal["ten"]), gia=tien(deal["gia_vnd"]), vung=VUNG[deal["loc"]])
    hoi = _chon(HOI_SANG, 3 * n + 1)
    return kiem_van(_ghep(mo, hoi)), [deal]


def _khoa_ten(t):
    return gon_ten(t).casefold()


def soan_chieu(man, ngay, so_my=True):
    """-> (text, muc_can_kiem_lai) ; muc[0] = ban re nhat, muc[1] (neu co) = ban Mỹ cung ten da chuan hoa (moi vung giu pid rieng)."""
    muc = man.get("kiem_lai")
    deal = re_nhat(muc)
    khoa = _khoa_ten(deal["ten"])
    my = next((m for m in muc if _deal_ok(m) and m["loc"] == "en-us" and _khoa_ten(m["ten"]) == khoa), None)
    can_kiem = [deal]
    so_sanh = ""
    if so_my and my and my["gia_vnd"] > deal["gia_vnd"]:
        so_sanh = f"Rẻ hơn Store Mỹ {tien(my['gia_vnd'] - deal['gia_vnd'])}."
        can_kiem.append(my)
    n = _so_ngay(ngay)
    mo = _chon(MO_CHIEU, n).format(ten=gon_ten(deal["ten"]), gia=tien(deal["gia_vnd"]), vung=VUNG[deal["loc"]])
    han = f"Hạn tới {han_vn(deal['endTime'])}."
    hoi = _chon(HOI_CHIEU, 3 * n + 1)
    # qua dai -> bo han, roi bo so sanh (cau hoi luon giu)
    for phan in ((so_sanh, han), (so_sanh, ""), ("", "")):
        t = _ghep(mo, phan[0], phan[1], hoi)
        if len(t) <= TRAN:
            if not phan[0] and len(can_kiem) > 1:
                can_kiem = can_kiem[:1]
            return kiem_van(t), can_kiem
    raise LoiDang("bai chieu dai qua gioi han ngay ca khi bo han va so sanh")


# ---------------------------------------------------------------- manifest + dang
def kiem_nhe(man, ngay, dang):
    """Release da qua bo kiem cua may dung; o day chi doi chieu khung (khong tai video)."""
    if man.get("phien_ban") != 1 or man.get("ngay_dang") != ngay or man.get("dang") != dang or man.get("che_do") != "that":
        raise manifest.LoiManifest(f"manifest khong dung khung that {ngay}/{dang} (phien_ban/ngay_dang/dang/che_do)")
    ban = man.get("ban") or {}
    for b in manifest.BAN:
        if ((ban.get(b) or {}).get("kiem") or {}).get("dat") is not True:
            raise manifest.LoiManifest(f"ban {b} khong dat bo kiem")
    return man


def tai_man(ngay, dang, thu_muc):
    p = manifest.tai_tep(ngay, dang, "manifest.json", thu_muc, che_do="that")
    return kiem_nhe(manifest._doc(p), ngay, dang), chung.sha256_tep(p)


def gio_dang(ngay, loai):
    h, m = map(int, GIO_DANG[loai].split(":"))
    d = dt.date.fromisoformat(ngay)
    return dt.datetime(d.year, d.month, d.day, h, m, tzinfo=chung.VN)


def url_anh(man, ngay, dang):
    """URL Pages cua bia-reels.jpg (kiem 200 image/jpeg); hong -> None (dang chi chu)."""
    goc = os.environ.get("PAGES_URL") or "https://{}.github.io/{}".format(*manifest.REPO.split("/"))
    try:
        u = site.url_cong_khai(goc, ngay, dang, man)[1]
        site.kiem_url(u, "image/jpeg", lan=3, nghi=5)
        return u
    except (LoiDang, KeyError, TypeError) as e:
        chung.log(f"threads_chu: anh khong dung duoc, dang CHI CHU: {e}")
        return None


def anh_ps_game(deal):
    """URL bia PS Store (image.api.playstation.com) cua DUNG game (loc/pid) -> kiem HEAD 200 + image/jpeg|png (Threads chi nhan JPEG/PNG).
    Khong lay duoc -> None (nguoi goi dung bia Release / chi chu). Chi doc, khong ghi gi."""
    try:
        r = http.gui("GET", f"https://store.playstation.com/{deal['loc']}/product/{deal['pid']}", headers={"User-Agent": UA},
                     theo_chuyen_huong=True, timeout=30)
        if r.status != 200:
            raise LoiDang(f"trang san pham HTTP {r.status}")
        u = gia.gia_trang.media(r.text, deal["pid"]).get("anh")
        if not isinstance(u, str) or urllib.parse.urlparse(u).hostname != ANH_PS_HOST or not u.startswith("https://"):
            raise LoiDang(f"khong co anh bia {ANH_PS_HOST} cua dung pid")
        h = http.gui("HEAD", u, timeout=30)
        ct = h.headers.get("content-type", "").split(";")[0].strip().lower()
        if h.status != 200 or ct not in ("image/jpeg", "image/png"):
            raise LoiDang(f"anh bia HTTP {h.status} {ct}")
        return u
    except (LoiDang, http.LoiMang, KeyError, TypeError, AttributeError) as e:
        chung.log(f"threads_chu: anh PS Store cua {deal.get('pid')} khong dung duoc: {e}")
        return None


CUA_SO = {"sang": (dt.time(9, 0), dt.time(12, 0)), "chieu": (dt.time(16, 30), dt.time(20, 0)),
          "binh_chon": (dt.time(12, 30), dt.time(15, 0))}   # gio VN; schedule GitHub hay tre


def kiem_ngay_gio(loai, ngay):
    """che_do that: --ngay phai la hom nay (gio VN) va gio hien tai nam trong cua so cua loai. Tra ly do loi hoac None."""
    bay = chung.bay_gio().astimezone(chung.VN)
    if ngay != bay.date().isoformat():
        return f"--ngay {ngay} khong phai hom nay gio VN ({bay.date().isoformat()})"
    tu, den = CUA_SO[loai]
    if not (tu <= bay.time() <= den):
        return f"ngoai cua so dang bai {loai} ({tu:%H:%M}-{den:%H:%M} gio VN), bay gio {bay:%H:%M}"
    return None


def _binh_chon_kiem_gia(man, sha, ngay):
    """-> (text, poll, muc, man, sha). Top 5 + gia khop -> cau game hang 1; thieu manifest / khong soan duoc / gia-han lech / kiem loi -> cau co dinh
    (sha = sha256 cua chinh bai co dinh de sg_dang co manifest_sha, man=None)."""
    if man:
        try:
            text, poll, muc = soan_binh_chon(man, ngay)
            van_de = []
            if muc:
                van_de, canh_bao = gia.kiem_lai(muc, chung.bay_gio())
                for c in canh_bao:
                    chung.log(f"kiem_lai canh bao: {c}")
            if not van_de:
                return text, poll, muc, man, sha
            chung.log_loi(f"threads_chu: binh_chon gia/han lech - dung cau co dinh: {'; '.join(van_de)}")
        except Exception as e:   # moi loi kiem/soan -> cau co dinh (khong nhac gia nen an toan)
            chung.log_loi(f"threads_chu: binh_chon khong dung duoc Top 5 ({type(e).__name__}: {e}) - dung cau co dinh")
    text, poll = cau_co_dinh(ngay)
    return text, poll, [], None, hashlib.sha256(text.encode("utf-8")).hexdigest()


def chay_loai(a, cong=None, thu_muc=None, dich=None):
    dang_nguon, dang_bai = NGUON[a.loai], BAI[a.loai]   # Release doc / khoa so sg_dang
    binh_chon = a.loai == "binh_chon"
    if a.che_do == "that":
        ly = kiem_ngay_gio(a.loai, a.ngay)
        if ly:
            chung.log_loi(f"threads_chu: {ly} - khong dang")
            ntfy.loi(f"Threads {a.loai} {a.ngay}: khong dang (sai ngay/gio)", ly)
            return 3
    thu_muc = thu_muc or tempfile.mkdtemp(prefix="sg-threads-")
    that = a.che_do == "that"
    man = sha = None
    try:
        man, sha = tai_man(a.ngay, dang_nguon, thu_muc)
    except manifest.LoiManifest as e:
        chung.log_loi(f"threads_chu: {e}")
        if not binh_chon:   # binh chon co bo cau co dinh -> thieu Release khong phai loi
            if that:
                ntfy.loi(f"Threads {a.loai} {a.ngay}: khong dang (thieu/sai Release)", str(e))
            return 3
    except (AttributeError, KeyError, TypeError, ValueError) as e:   # manifest sai cau truc
        chung.log_loi(f"threads_chu: manifest {dang_nguon} sai cau truc ({type(e).__name__}: {e})")
        if not binh_chon:
            if that:
                ntfy.loi(f"Threads {a.loai} {a.ngay}: khong dang (manifest sai cau truc)", f"{type(e).__name__}: {e}")
            return 3
        man = sha = None
    poll = None
    if binh_chon:
        text, poll, muc, man, sha = _binh_chon_kiem_gia(man, sha, a.ngay)
        ung_vien = [None]   # poll chi gan duoc vao bai TEXT
    else:
        try:
            text, muc = (soan_sang if a.loai == "sang" else soan_chieu)(man, a.ngay)
        except LoiDang as e:
            chung.log_loi(f"threads_chu: {e}")
            if that:
                ntfy.loi(f"Threads {a.loai} {a.ngay}: khong soan duoc bai", str(e))
            return 3
        van_de, canh_bao = gia.kiem_lai(muc[:1], chung.bay_gio())   # ban re nhat duoc nhac trong bai; fail-closed
        for c in canh_bao:
            chung.log(f"kiem_lai canh bao: {c}")
        if van_de:
            ly = "; ".join(van_de)
            chung.log_loi(f"threads_chu: gia/han lech - khong dang: {ly}")
            if that:
                ntfy.loi(f"Threads {a.loai} {a.ngay}: gia/han lech, khong dang", ly)
            return 3
        if len(muc) > 1:   # ban Mỹ (dung pid Mỹ): lech/loi -> bo cau chenh, KHONG bo bai
            try:
                v2, _ = gia.kiem_lai(muc[1:], chung.bay_gio())
            except Exception as e:
                v2 = [f"loi kiem ban My: {type(e).__name__}"]
            if v2:
                chung.log_loi(f"threads_chu: bo cau chenh Mỹ: {'; '.join(v2)}")
                text, muc = soan_chieu(man, a.ngay, so_my=False)
        if a.loai == "chieu":
            ung_vien = [url_anh(man, a.ngay, dang_nguon), None]
        else:   # sang: bia PS Store cua DUNG game re nhat duoc nhac; khong lay duoc -> bia Release tin-nhanh; Pages hong -> chi chu
            ung_vien = [anh_ps_game(muc[0]), url_anh(man, a.ngay, dang_nguon), None]
        ung_vien = list(dict.fromkeys(u for u in ung_vien if u)) + [None]   # bo ung vien rong/trung, luon con "chi chu" o cuoi
    anh = ung_vien[0]
    if not that:
        print(f"=== BAI THREADS {a.loai} {a.ngay} (nguon {dang_nguon} · so {dang_bai}) ===\n{text}\n"
              f"{'--- POLL ' + ' | '.join(poll.values()) + chr(10) if poll else ''}--- {len(text)} ky tu · topic_tag={TOPIC_TAG} · "
              f"{'anh ' + anh if anh else 'chi chu'}", flush=True)
        return 0
    gio = gio_dang(a.ngay, a.loai)
    nc = chung.NguCanh(a.ngay, dang_bai, a.che_do, gio, man or {}, thu_muc, cong)
    nc.manifest_sha = sha
    tk = chay.tai_token(cong, "threads")
    chay.kiem_danh_tinh("threads", tk, nc, dich if dich is not None else chay.nap_dich(os.environ.get("DICH_JSON")))
    if not cong.giu_dang(a.ngay, dang_bai, "threads", a.che_do, chung.iso(gio), sha):
        chung.log("threads_chu: sg_dang da co dong cho khung nay - khong dang lai")
        return 0

    def luu(**kw):
        try:
            cong.cap_nhat_dang(**chay._khoa(nc, "threads"), **kw)
        except LoiCong as e:   # container chua publish -> khong nguy hiem, chi ghi log
            chung.log_loi(f"threads_chu: khong ghi duoc {kw}: {e}")

    cid = None
    for i, u in enumerate(ung_vien):   # loi o BUOC TAO CONTAINER (chua publish) -> thu ung vien ke tiep (anh PS -> bia Release -> chi chu)
        try:
            cid = threads.tao_container_chu(tk, text, u, TOPIC_TAG, luu, poll)
            chung.ngu(CHO_TRUOC_PUBLISH)
            break
        except Exception as e:   # chua publish -> chac chan chua len Threads
            err = e if isinstance(e, LoiDang) else LoiDang(f"{type(e).__name__}: {chung.cat(e, 300)}")
            if i + 1 < len(ung_vien):
                chung.log_loi(f"threads_chu: container voi anh {u} loi ({err}) - thu ung vien ke tiep")
                continue
            chay._ghi_loi(cong, nc, "threads", err)
            if err is e:
                raise
            raise err from None
    try:
        ket = threads.cong_khai(tk, nc, {"id_container": cid})
    except LoiDang as e:
        chay._ghi_loi(cong, nc, "threads", e)
        raise
    except Exception as e:   # da goi threads_publish: khong chac
        err = LoiDang(f"{type(e).__name__}: {chung.cat(e, 300)}", khong_ro=True)
        chay._ghi_loi(cong, nc, "threads", err)
        raise err from None
    try:
        chay._doi(cong, nc, "threads", "dang_dang", trang_thai="da_dang", id_bai=ket.get("id_bai"), link=ket.get("link"),
                  gio_cong_khai=chung.iso(chung.bay_gio()))
    except LoiCong as e:
        raise LoiDang(f"Threads DA dang ({ket.get('link') or ket.get('id_bai')}) nhung ghi so loi: {e}", khong_ro=True) from None
    if ket.get("canh_bao"):
        ntfy.loi(f"Threads {a.loai} {a.ngay}: canh bao sau khi dang", ket["canh_bao"], uu_tien=3)
    ntfy.tin(f"Da dang Threads {a.loai} {a.ngay}", ket.get("link") or ket.get("id_bai") or "da dang")
    return 0


def main(argv=None, cong=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("--loai", required=True, choices=list(NGUON))
    ap.add_argument("--ngay", required=True)
    ap.add_argument("--che-do", dest="che_do", required=True, choices=["thu", "that"])
    a = ap.parse_args(argv)
    if not re.fullmatch(r"\d{4}-\d{2}-\d{2}", a.ngay):
        ap.error("--ngay phai la YYYY-MM-DD")
    try:
        if a.che_do == "that":
            cong = cong or Cong()
        return chay_loai(a, cong, os.environ.get("DANG_THU_MUC"))
    except LoiCong as e:
        chung.log_loi(str(e))
        return 1
    except Exception as e:
        chung.log_loi(f"threads_chu LOI: {type(e).__name__}: {e}")
        if a.che_do == "that":
            ghi = "KHONG RO - KHONG tu dang lai, kiem tay. " if getattr(e, "khong_ro", False) else ""
            ntfy.loi(f"Threads {a.loai} {a.ngay} loi", f"{ghi}{type(e).__name__}: {e}")
        return 1


if __name__ == "__main__":
    sys.exit(main())
