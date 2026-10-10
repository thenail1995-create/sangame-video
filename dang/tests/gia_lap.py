"""Do gia lap dung chung: mang gia (thay http.gui), cong gia (thay so.Cong), ngu canh gia."""
import datetime as dt
import hashlib
import json
import pathlib
import tempfile

from dang import chung, http

NGAY, DANG = "2026-10-12", "top5"
GIO_DANG = dt.datetime(2026, 10, 12, 12, 0, tzinfo=chung.VN)


def P(status=200, body=None, headers=None, raw=None):
    b = raw if raw is not None else json.dumps(body if body is not None else {}).encode()
    return http.Phan(status, headers or {}, b)


class Mang:
    """mang.them('POST', 'video_reels', P(...)) hoac list (lan luot) hoac ham f(method,url,kw)->Phan.
    Luat khop dau tien theo (method, chuoi con trong url). Khong co luat -> AssertionError (test hong ro rang)."""

    def __init__(self):
        self.luat, self.goi = [], []

    def them(self, method, mau, tra):
        self.luat.append([method, mau, tra])
        return self

    def __call__(self, method, url, **kw):
        self.goi.append((method, url, kw))
        for l in self.luat:
            if l[0] == method and l[1] in url:
                tra = l[2]
                if callable(tra):
                    r = tra(method, url, kw)
                elif isinstance(tra, list):
                    r = tra.pop(0) if len(tra) > 1 else tra[0]
                else:
                    r = tra
                if isinstance(r, Exception):
                    raise r
                return r
        raise AssertionError(f"khong co luat gia lap cho {method} {url}")

    def dem(self, method, mau):
        return sum(1 for m, u, _ in self.goi if m == method and mau in u)

    def thu_tu(self):
        return [(m, u) for m, u, _ in self.goi]

    def tat_ca_text(self):
        return json.dumps([(m, u, {k: str(v)[:80] for k, v in kw.items()}) for m, u, kw in self.goi])


class CongGia:
    """Giong sg_dang that: giu_dang chi True khi chua co dong hoac dong dang o that_bai."""

    def __init__(self):
        self.dong, self.token, self.ghi = {}, {}, []
        self.cap_nhat = []

    def giu_dang(self, ngay, dang, kenh, che_do, gio_du_kien=None, manifest_sha=None):
        k = (ngay, dang, kenh, che_do)
        if k not in self.dong or self.dong[k]["trang_thai"] == "that_bai":
            self.dong[k] = dict(ngay=ngay, dang=dang, kenh=kenh, che_do=che_do, trang_thai="dang_dang", gio_du_kien=gio_du_kien,
                                manifest_sha=manifest_sha)
            return True
        return False

    def cap_nhat_dang(self, ngay, dang, kenh, che_do, neu_trang_thai=None, **truong):
        """Giong cong v2: neu_trang_thai khop moi sua, tra so_dong 0/1; khong co thi 0 dong la loi (nhu so.Cong)."""
        d = self.dong.get((ngay, dang, kenh, che_do))
        if neu_trang_thai is not None:
            if d is None or d["trang_thai"] != neu_trang_thai:
                return 0
        elif d is None:
            raise AssertionError("cap_nhat_dang khong co dong")
        self.hong_ghi_sau = getattr(self, "hong_ghi_sau", None)
        if self.hong_ghi_sau and self.hong_ghi_sau(kenh, truong):
            from dang.so import LoiCong
            raise LoiCong("gia lap loi ghi so")
        d.update(truong)
        self.cap_nhat.append((kenh, truong))
        return 1

    def doc_dang(self, tu, den=None, che_do=None):
        return [dict(v) for v in self.dong.values() if (not che_do or v["che_do"] == che_do) and tu <= v["ngay"] <= (den or tu)]

    def doc_token(self, kenh):
        return self.token.get(kenh)

    def ghi_token(self, kenh, du_lieu, het_han=None):
        self.token[kenh] = {"du_lieu": du_lieu, "het_han": het_han, "cap_nhat": "x"}
        self.ghi.append(kenh)

    def trang_thai(self, kenh, che_do="that"):
        return self.dong[(NGAY, DANG, kenh, che_do)]["trang_thai"]


TOKEN_GIA = {
    "fb": {"page_id": "PAGE1", "page_token": "EAAFBTOKENGIA1234567890abcdef"},
    "ig": {"ig_user_id": "IGU1", "page_token": "EAAIGTOKENGIA1234567890abcdef"},
    "threads": {"threads_user_id": "THU1", "token": "THTOKENGIA1234567890abcdef", "cap_luc": 1},
    "youtube": {"channel_id": "UCYT1", "client_id": "cid", "client_secret": "YTSECRETGIA123456", "refresh_token": "YTREFRESHGIA123456"},  # gitleaks:allow (token gia cho test)
    "tiktok": {"open_id": "TTO1", "client_key": "ck", "client_secret": "TTSECRETGIA123456", "access_token": "TTACCESSGIA123456",  # gitleaks:allow (token gia cho test)
               "access_het_han": 4102444800, "refresh_token": "TTREFRESHGIA123456", "refresh_het_han": 4102444800},
}
DICH_DU = {"fb": {"page_id": "PAGE1"}, "ig": {"ig_user_id": "IGU1"}, "threads": {"threads_user_id": "THU1"},
           "youtube": {"channel_id": "UCYT1"}, "tiktok": {"open_id": "TTO1"}}


def cong_day_du():
    c = CongGia()
    for k, v in TOKEN_GIA.items():
        c.token[k] = {"du_lieu": dict(v), "het_han": None, "cap_nhat": "x"}
    return c


def tao_manifest(thu_muc, che_do="that", ngay=NGAY, dang=DANG, dat=True, kiem_lai=None):
    thu_muc = pathlib.Path(thu_muc)
    ban = {}
    for b in ("tiktok", "reels", "shorts"):
        v, a = f"video-{b}.mp4", f"bia-{b}.jpg"
        (thu_muc / v).write_bytes(b"VIDEO-" + b.encode() * 100)
        (thu_muc / a).write_bytes(b"JPG-" + b.encode() * 10)
        ban[b] = {"video": v, "sha256": hashlib.sha256((thu_muc / v).read_bytes()).hexdigest(), "bia": a,
                  "bia_sha256": hashlib.sha256((thu_muc / a).read_bytes()).hexdigest(), "giay": 30.1,
                  "kiem": {"dat": dat, "phep": [{"ten": "x", "dat": dat, "so_do": "1"}]}}
    man = {"phien_ban": 1, "ngay_dang": ngay, "dang": dang, "gio_dang": f"{ngay}T12:00:00+07:00", "che_do": che_do,
           "sha_code": "abc", "sha_du_lieu": "def", "tao_luc": f"{ngay}T10:00:00+07:00", "ban": ban,
           "loi_dang": {"tieu_de": "Top 5 game PS5 duoi 200.000d hom nay", "mo_ta": "Mo ta.", "hashtag": ["#SanGame", "#PS5"],
                        "link": "https://sangame.com.vn/"},
           "kiem_lai": kiem_lai or []}
    (thu_muc / "manifest.json").write_text(json.dumps(man))
    return man


def tao_nc(che_do="that", cong=None, url=True):
    thu_muc = tempfile.mkdtemp(prefix="sg-test-")
    man = tao_manifest(thu_muc, che_do)
    nc = chung.NguCanh(NGAY, DANG, che_do, GIO_DANG, man, thu_muc, cong or cong_day_du(),
                       "https://x.github.io/sangame-video/v/a.mp4" if url else None,
                       "https://x.github.io/sangame-video/v/a.jpg" if url else None)
    return nc
