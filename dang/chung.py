"""Ham dung chung: che bi mat khi in log, ngoai le, thoi gian, ngu."""
import datetime as dt
import hashlib
import re
import sys
import unicodedata
import time

VN = dt.timezone(dt.timedelta(hours=7))
_BI_MAT: set = set()
_TU_KHOA_BI_MAT = ("token", "secret", "khoa", "key", "password")


def dang_ky_bi_mat(*gia_tri):
    """Dang ky chuoi can che (khoa cong, token...). Chuoi ngan hon 6 ky tu bi bo qua (tranh che nham)."""
    for v in gia_tri:
        if isinstance(v, str) and len(v) >= 6:
            _BI_MAT.add(v)


def dang_ky_tu_du_lieu(du_lieu):
    """Duyet dict/list token, dang ky moi gia tri chuoi o truong co ten giong bi mat (token/secret/khoa/key)."""
    if isinstance(du_lieu, dict):
        for k, v in du_lieu.items():
            if isinstance(v, str) and any(t in str(k).lower() for t in _TU_KHOA_BI_MAT):
                dang_ky_bi_mat(v)
            else:
                dang_ky_tu_du_lieu(v)
    elif isinstance(du_lieu, list):
        for v in du_lieu:
            dang_ky_tu_du_lieu(v)


_MAU = [
    re.compile(r"(?i)((?:access_token|refresh_token|client_secret|fb_exchange_token|th_refresh_token|key)=)[^&\s\"']+"),
    re.compile(r"(?i)\b(Bearer|OAuth)\s+[A-Za-z0-9._\-~+/=]{8,}"),
    re.compile(r"(?i)(\"(?:access_token|refresh_token|client_secret|page_token|token|upload_url)\"\s*:\s*\")[^\"]+"),
    re.compile(r"\bEA[A-Za-z0-9]{20,}"),
    re.compile(r"\bya29\.[A-Za-z0-9._\-]+"),
]


def che(s) -> str:
    """Che moi bi mat da dang ky va cac mau token pho bien. Luon dung truoc khi in / dua vao thong bao loi."""
    s = str(s)
    for b in sorted(_BI_MAT, key=len, reverse=True):
        s = s.replace(b, "***")
    s = _MAU[0].sub(r"\1***", s)
    s = _MAU[1].sub(r"\1 ***", s)
    s = _MAU[2].sub(r"\1***", s)
    s = _MAU[3].sub("***", s)
    s = _MAU[4].sub("***", s)
    return s


def cat(x, n=200) -> str:
    """CHE bi mat TRUOC, cat SAU (cat truoc se lam mat chuoi day du nen che khong bat duoc phan dau)."""
    return che(str(x))[:n]


def log(*a):
    print(che(" ".join(str(x) for x in a)), flush=True)


def log_loi(*a):
    print(che(" ".join(str(x) for x in a)), file=sys.stderr, flush=True)


class LoiDang(Exception):
    """Loi khi dang. khong_ro=True: da goi nen tang co tac dung phu ma khong chac ket qua -> KHONG tu thu lai."""

    def __init__(self, ly_do, khong_ro=False, ma_http=None, thong_diep=None):
        super().__init__(che(ly_do))
        self.khong_ro = khong_ro
        self.ma_http = ma_http                                   # HTTP status cua nen tang (neu co)
        self.thong_diep = che(thong_diep) if thong_diep else None  # thong diep loi goc da che bi mat


def bay_gio() -> dt.datetime:
    return dt.datetime.now(dt.timezone.utc)


def ngu(giay):
    time.sleep(giay)


def iso(t: dt.datetime) -> str:
    return t.astimezone(dt.timezone.utc).isoformat().replace("+00:00", "Z")


def sha256_tep(duong) -> str:
    h = hashlib.sha256()
    with open(duong, "rb") as f:
        for khoi in iter(lambda: f.read(1 << 20), b""):
            h.update(khoi)
    return h.hexdigest()


# 13/10: video Sang Game dung giong doc AI -> khai bao nhan "noi dung do AI tao" tren moi nen tang. Tat = khong co, khong dong nhan.
CO_GIONG_AI = True
DONG_NHAN_AI = "Video dùng giọng đọc AI."
GIO_HET_SANG = 10
TIKTOK_TOI_DA = 150
TRAN_HASHTAG = {"ig": 5, "tiktok": 3, "youtube": 3, "x": 2, "fb": 3}
_BO_CO_DINH = ["#PlayStation", "#PS5", "#SănGame", "#GiảmGiá"]
# 27/10 (SG-FB-2, SG-IG-0): bo hashtag co dinh rieng IG/FB (sau tag game). Nen tang khac giu _BO_CO_DINH (YouTube toi luot SG-3).
BO_TAG = {"ig": ["#GiảmGiá", "#PS5", "#SănGame"], "fb": ["#PS5", "#SănGame"]}
_RE_BAN_TIN_SANG = re.compile(r"Bản tin sáng")
_RE_SANG_NAY = re.compile(r"(?i)\bsáng nay\b")
_RE_URL = re.compile(r"(?i)(?<![\w@])(?:https?://|www\.)\S+|(?<![\w@.])sangame\.com\.vn\S*")
# Bo nhan URL RONG (co giao thuc, www., moi ten mien tran dang abc.xyz[/duong]; khong bat email). Dung cho FB va chu dang tay (dang/ngan.py).
_RE_URL_RONG = re.compile(r"(?i)https?://\S+|(?<![\w@.-])www\.\S+|(?<![\w@.-])(?:[a-z0-9][a-z0-9-]*\.)+[a-z]{2,24}(?![\w@-])(?:/\S*)?")
_RE_TAG = re.compile(r"#\w+")
THAY_URL = "web Săn Game (link ở bio)"
THAY_URL_FB = "web Săn Game"   # FB khong co link o bio cho Reel -> khong nhac "link o bio"
TIEU_DE_DU_PHONG = "Săn Game: tin giảm giá PlayStation hôm nay"
_RE_GIA_DONG = re.compile(r"\s-\s(\d{1,3}(?:\.\d{3})+)đ")
_RE_REN_NHAT = re.compile(r"rẻ nhất (.+?),\s*(\d{1,3}(?:\.\d{3})+)đ")
# 13/10: caption Tin nhanh hien "Hogwarts Legacy PS5 Version" -> bo duoi nen tang o CUOI ten (chi caption/hashtag, khong doi video)
_RE_DUOI_NEN_TANG = re.compile(r"(?:\s*[-–:]?\s*(?:PS[45]\s*(?:Version|Edition)|PS[45]\s*&\s*PS[45]|for\s+PS[45]|PS[45]))+\s*$", re.I)


def bo_duoi_nen_tang(ten):
    """'Hogwarts Legacy PS5 Version' -> 'Hogwarts Legacy'; 'It Takes Two PS4 & PS5' -> 'It Takes Two'. Rong sau khi bo -> giu ten cu."""
    t = (ten or "").strip()
    g = _RE_DUOI_NEN_TANG.sub("", t).strip(" -–:")
    return g or t


def _cat_chu(s, n):
    s = (s or "").strip()
    if len(s) <= n:
        return s
    return s[:max(n - 1, 0)].rstrip() + "…"


def bo_url(s, thay=THAY_URL, mau=None):
    """Thay moi URL (http/https/www/ten mien sangame.com.vn, khong phan biet hoa thuong) bang `thay` (mac dinh 'web Săn Game (link ở bio)').
    'Tra gia ...: https://x.vn/a.' -> 'Tra gia ...: web Săn Game (link ở bio).' (giu dau cau cuoi)."""
    def doi(m):
        u = m.group(0)
        dau = re.search(r"[.,;:!?)]+$", u)
        return thay + (dau.group(0) if dau else "")
    return (mau or _RE_URL).sub(doi, s or "").strip()


def tag_co_san(*van_ban):
    """Cac hashtag da nam trong van ban (chu thuong) - tinh vao tran cua nen tang."""
    return [t.lower() for v in van_ban for t in _RE_TAG.findall(v or "")]


def hashtag_game(ten):
    """'NINJA GAIDEN 2 Black' -> '#NinjaGaiden2Black' (khong dau, CamelCase, than <= 25 ky tu); rong -> ''."""
    ten = re.split(r"\s*(?::|\s-\s|–)\s*", (ten or "").strip())[0]
    ten = unicodedata.normalize("NFD", ten.replace("Đ", "D").replace("đ", "d"))
    ten = "".join(c for c in ten if unicodedata.category(c) != "Mn")
    ten = re.sub(r"['’`]", "", ten)   # Marvel's -> Marvels, khong tach thanh Marvel + S
    tu = []
    for w in re.findall(r"[A-Za-z0-9]+", ten):
        if w.isupper() and len(w) > 3:
            w = w.capitalize()
        tu.append(w[0].upper() + w[1:])
    than = "".join(tu)[:25]
    return "#" + than if than else ""


def bo_hashtag(ten, tran, co_san=(), co_dinh=None):
    """[tag game] + bo co dinh (mac dinh #PlayStation #PS5 #SanGame #GiamGia) cat theo tran tung nen tang.
    co_san: hashtag da nam trong van ban cua bai (tinh vao tran, khong them lai tag trung)."""
    tag = hashtag_game(ten)
    con = tran - len(co_san)
    ung = [t for t in (([tag] if tag else []) + (_BO_CO_DINH if co_dinh is None else co_dinh)) if t.lower() not in co_san]
    return ung[:max(con, 0)]


class NguCanh:
    """Moi thu mot lan dang can biet. url_video/url_bia: URL cong khai tren GitHub Pages (IG/Threads)."""

    def __init__(self, ngay, dang, che_do, gio_dang, man, thu_muc, cong, url_video=None, url_bia=None):
        self.ngay, self.dang, self.che_do, self.gio_dang = ngay, dang, che_do, gio_dang
        self.man, self.thu_muc, self.cong = man, thu_muc, cong
        self.url_video, self.url_bia = url_video, url_bia
        self.manifest_sha = None   # sha256 cua CHINH file manifest.json (chay.py dat)
        self.loi_dang = man.get("loi_dang") or {}

    def tep(self, ban, loai="video"):
        import pathlib
        return pathlib.Path(self.thu_muc) / self.man["ban"][ban][loai]

    def _hashtag(self):
        return " ".join(self.loi_dang.get("hashtag") or [])

    def caption_dai(self, toi_da=2200):
        """Ban cu (tieu de + mo ta + link + hashtag cua manifest). Con giu cho tuong thich; cac nen tang dung caption_* rieng."""
        ld = self.loi_dang
        phan = [ld.get("tieu_de", ""), ld.get("mo_ta", ""), ld.get("link", ""), self._hashtag()]
        return "\n\n".join(p for p in phan if p)[:toi_da]

    # ---- caption rieng tung nen tang (05-ke-hoach-caption-nen-tang) ----
    def gio_cong_khai(self):
        """Gio cong khai thuc te: tre hon gio du kien thi lay bay_gio; chuan bi som (container IG) thi lay gio du kien."""
        return max(bay_gio(), self.gio_dang)

    def _nhan(self, s):
        """Sau 10:00 VN thi 'Ban tin sang'/'sang nay' doi thanh 'hom nay'."""
        if self.gio_cong_khai().astimezone(VN).hour < GIO_HET_SANG:
            return s
        return _RE_SANG_NAY.sub("hôm nay", _RE_BAN_TIN_SANG.sub("Bản tin", s))

    def ten_game(self):
        return ten_game_tu_loi_dang(self.dang, self.loi_dang)

    def hook(self):
        return self._nhan(hook_tu_loi_dang(self.dang, self.loi_dang))

    def hook_sach(self):
        """Hook khong URL, khong rong (cho TikTok / YouTube / IG)."""
        return bo_url(self.hook()).strip() or TIEU_DE_DU_PHONG

    def hashtags(self, nen_tang, *co_san):
        """Hashtag them vao: tran nen tang tru so hashtag da co trong van ban (co_san) cua bai."""
        return bo_hashtag(self.ten_game(), TRAN_HASHTAG[nen_tang], tag_co_san(*co_san), BO_TAG.get(nen_tang))

    def tags_youtube(self):
        """Truong tags (khong '#') cua YouTube: GIU bo cu (tag game + #PlayStation #PS5 #SănGame #GiảmGiá), toi da 15,
        doc lap voi BO_TAG cua IG/FB (S3 soi Sol 27/10)."""
        return [h.lstrip("#") for h in bo_hashtag(self.ten_game(), TRAN_HASHTAG["ig"])][:15]

    def _than(self):
        return [self._nhan(c) for c in than_ngan(self.dang, self.loi_dang)]

    def caption_tiktok(self):
        """<= 150 ky tu: hook + 3 hashtag, KHONG URL."""
        hook = self.hook_sach()
        tags = " ".join(self.hashtags("tiktok", hook))
        hook = _cat_chu(hook, TIKTOK_TOI_DA - len(tags) - 1)
        return f"{hook}\n{tags}".strip()

    def tieu_de_youtube(self):
        return _cat_chu(self.hook_sach(), 100) or TIEU_DE_DU_PHONG

    def mo_ta_youtube(self):
        """Hashtag co tag game o dau mo ta (3 hashtag dau hien canh tieu de), KHONG URL, #Shorts o cuoi."""
        thanh = [bo_url(self._nhan(self.loi_dang.get("mo_ta", "")))]
        tags = self.hashtags("youtube", self.hook_sach(), *thanh)
        s = "\n\n".join(p for p in (" ".join(tags), *thanh) if p)
        if "#shorts" not in s.lower():
            s += "\n\n#Shorts"
        return s[:4900]

    def caption_ig(self, toi_da=2200):
        """hook + 1-2 cau + 'Bang gia du vung: link o bio' + <= 5 hashtag (tag game, #GiamGia, #PS5, #SanGame), khong URL."""
        hook, than = self.hook_sach(), " ".join(self._than())
        phan = [hook, than, "Bảng giá đủ vùng: link ở bio.", " ".join(self.hashtags("ig", hook, than))]
        return "\n\n".join(p for p in phan if p)[:toi_da]

    def caption_fb(self, toi_da=2200):
        """Dong dau la hook, giu mo ta day du, KHONG URL/ten mien o bat ky cho nao (SG-FB-2: Reel FB khong link o caption lan binh luan),
        <= 3 hashtag (tag game, #PS5, #SanGame)."""
        mo_ta = bo_url(self._nhan(self.loi_dang.get("mo_ta", "")), THAY_URL_FB, _RE_URL_RONG)
        hook = bo_url(self.hook(), THAY_URL_FB, _RE_URL_RONG)
        tags = " ".join(self.hashtags("fb", hook, mo_ta))
        nhan = DONG_NHAN_AI if CO_GIONG_AI else ""
        phan = [hook, mo_ta, tags]
        # dong nhan o CUOI: cat noi dung truoc, khong cat nhan
        ben = "\n\n".join(p for p in phan if p)
        if not nhan:
            return ben[:toi_da]
        con = toi_da - len(nhan) - 2
        return ben[:max(con, 0)].rstrip() + "\n\n" + nhan

    def text_ngan(self, toi_da=500):
        """Threads: toi da 500 ky tu - tieu de + link, roi them hashtag nao con vua."""
        ld = self.loi_dang
        s = "\n".join(p for p in (ld.get("tieu_de", ""), ld.get("link", "")) if p)[:toi_da]
        dong_tag = ""
        for h in ld.get("hashtag") or []:
            thu = (dong_tag + " " + h).strip()
            if len(s) + 1 + len(thu) <= toi_da:
                dong_tag = thu
        return (s + "\n" + dong_tag).strip() if dong_tag else s


def _gia_so(chuoi):
    return int(chuoi.replace(".", ""))


def _ren_nhat(mo_ta):
    """Trong cac dong 'rẻ nhất <game>, <gia>đ ...' (Tin nhanh) -> (game, gia_chuoi) re nhat, hoac None."""
    ung = [(bo_duoi_nen_tang(m.group(1)), m.group(2)) for m in _RE_REN_NHAT.finditer(mo_ta or "")]
    return min(ung, key=lambda t: _gia_so(t[1])) if ung else None


def ten_game_tu_loi_dang(dang, ld):
    """Tin nhanh: game re nhat; Keo: phan truoc ' giam N%' cua tieu de; Flagship: loi_dang.ten_game; Top 5: khong co (None)."""
    if dang.startswith("tin-nhanh"):
        r = _ren_nhat(ld.get("mo_ta"))
        return r[0] if r else None
    if dang.startswith("keo-thom"):
        m = re.match(r"^(.+?)\s+giảm\s+\d+%", ld.get("tieu_de") or "")
        return m.group(1).strip() if m else None
    if dang == "flagship":
        return (ld.get("ten_game") or "").strip() or None
    return None


def hook_tu_loi_dang(dang, ld):
    """Dong 1 = ten game + con so chinh, chi dung du lieu co san trong manifest; khong dung duoc thi quay ve tieu_de."""
    td = (ld.get("tieu_de") or "").strip()
    if dang.startswith("tin-nhanh"):
        r = _ren_nhat(ld.get("mo_ta"))
        if r:
            n = len(re.findall(r"(?m)^\d+\.\s", ld.get("mo_ta") or ""))
            tin = f"{n} tin" if n else "tin"
            return f"{r[0]} chỉ còn {r[1]}đ — {tin} giảm giá PS hôm nay"
    elif dang.startswith("top5"):
        m = re.search(r"dưới\s+(\d{1,3}(?:\.\d{3})+)đ", td)
        if m:
            return f"Top 5 game PS dưới {m.group(1)}đ hôm nay"
    elif dang == "flagship":
        return td   # tieu de da la hook (tieu de + con so tien Viet) - nhu bai Cyberpunk 21/10
    return td


def than_ngan(dang, ld):
    """1-2 cau cho Instagram, lay tu mo_ta (khong URL, khong lap hook)."""
    mo_ta = bo_url(ld.get("mo_ta") or "")
    dong = [d.strip() for d in mo_ta.split("\n") if d.strip()]
    if dang.startswith("tin-nhanh"):
        return [d for d in dong if "rẻ nhất" in d][:2]
    if dang.startswith("top5"):
        c = []
        hang = [d for d in dong if re.match(r"^\d\.\s", d)]
        gia = [_RE_GIA_DONG.search(d) for d in hang]
        if hang and all(gia):
            # danh sach xep theo hang ban chay, KHONG theo gia: tim game gia nho nhat (hoa -> hang cao hon)
            re_nhat = min(range(len(hang)), key=lambda i: _gia_so(gia[i].group(1)))
            c.append("Rẻ nhất: " + re.sub(r"^\d\.\s*", "", hang[re_nhat]) + ".")
        elif hang:
            c.append("Đứng đầu: " + re.sub(r"^\d\.\s*", "", hang[0]) + ".")
        sm = re.search(r"Deal sớm nhất hết lúc [^.]*?\(giờ VN\)\.", mo_ta)
        if sm:
            c.append(sm.group(0))
        return c[:2]
    if dang == "flagship":
        # 2 cau dau cua mo ta (bo URL): gia + thẻ, khong cat giua so thap phan ("19,99")
        cau = [x.strip() for x in re.split(r"(?<=[.!?])\s+", mo_ta.replace("\n", " ")) if x.strip()]
        return cau[:2]
    cau = [x.strip() for x in re.split(r"(?<=[.!?])\s+", mo_ta.replace("\n", " ")) if x.strip()]
    cau = [x for x in cau[1:] if not x.startswith(("Giá quy đổi", "Xem giá", "Tra giá"))]
    return cau[:2]
