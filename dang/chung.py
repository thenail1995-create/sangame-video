"""Ham dung chung: che bi mat khi in log, ngoai le, thoi gian, ngu."""
import datetime as dt
import hashlib
import re
import sys
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


def log(*a):
    print(che(" ".join(str(x) for x in a)), flush=True)


def log_loi(*a):
    print(che(" ".join(str(x) for x in a)), file=sys.stderr, flush=True)


class LoiDang(Exception):
    """Loi khi dang. khong_ro=True: da goi nen tang co tac dung phu ma khong chac ket qua -> KHONG tu thu lai."""

    def __init__(self, ly_do, khong_ro=False):
        super().__init__(che(ly_do))
        self.khong_ro = khong_ro


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


class NguCanh:
    """Moi thu mot lan dang can biet. url_video/url_bia: URL cong khai tren GitHub Pages (IG/Threads)."""

    def __init__(self, ngay, dang, che_do, gio_dang, man, thu_muc, cong, url_video=None, url_bia=None):
        self.ngay, self.dang, self.che_do, self.gio_dang = ngay, dang, che_do, gio_dang
        self.man, self.thu_muc, self.cong = man, thu_muc, cong
        self.url_video, self.url_bia = url_video, url_bia
        self.loi_dang = man.get("loi_dang") or {}

    def tep(self, ban, loai="video"):
        import pathlib
        return pathlib.Path(self.thu_muc) / self.man["ban"][ban][loai]

    def _hashtag(self):
        return " ".join(self.loi_dang.get("hashtag") or [])

    def caption_dai(self, toi_da=2200):
        """FB / IG: tieu de, mo ta, link, hashtag."""
        ld = self.loi_dang
        phan = [ld.get("tieu_de", ""), ld.get("mo_ta", ""), ld.get("link", ""), self._hashtag()]
        return "\n\n".join(p for p in phan if p)[:toi_da]

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

    def mo_ta_youtube(self):
        ld = self.loi_dang
        phan = [ld.get("mo_ta", ""), ld.get("link", ""), self._hashtag()]
        s = "\n\n".join(p for p in phan if p)
        if "#shorts" not in s.lower():
            s += "\n#Shorts"
        return s[:4900]
