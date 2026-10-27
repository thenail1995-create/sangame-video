"""Bo dang TAY cho video ngan (TikTok / YouTube Shorts / Instagram Reels / Facebook Reels) khong di qua may tu dong.
Thay cho cac script rieng tung video (video-ngan-0X/bai/dang-video.py): script moi chi con ~15 dong goi main().

  python -m dang.ngan <thu-muc-bai> kiem|yt|hen-yt|tiktok|hen-tiktok|ig|fb|hen-fb|binh-luan

Thu muc bai co:
  bai.json       {"ten": "...", "ngay": "YYYY-MM-DD", "video": "duong/dan.mp4", "game": "Ten game", "gio_hen": "ISO co mui gio" (hen-*), "tags": [...] (YT)}
  chu-video.md   khoi "## YouTube · tiêu đề", "## YouTube · mô tả", "## TikTok", "## Instagram", "## Facebook", "## Bình luận" (tuy chon),
                 moi khoi la mot hang rao ``` ... ``` (nhu script cu)
  ra/            ket qua: ra/<kenh>.json  trang_thai dang_lam -> xong (chong dang trung)

Luat Hao 27/10: video giong AI phai co nhan AI tren moi kenh, cong cu khong gan duoc thi KHONG dung -> moi lenh dang di qua
yt.xac_nhan_ai / fb.tham_finish / ig.tham_container / body TikTok video_made_with_ai; khong co duong lui "dang khong nhan".
Moi lenh dang chay cac phep kiem chu (kiem_chu / kiem_tieu_de_yt / cach_gio_tiktok qua Zernio) TRUOC moi goi mang co tac dung.
"""
import contextlib
import datetime as dt
import hashlib
import json
import os
import pathlib
import re
import subprocess
import sys
import time
import unicodedata

from . import chay, chung, fb, http, ig, meta, so, yt, zernio
from .chung import LoiDang, VN

_RE_URL_RONG = chung._RE_URL_RONG   # bo nhan URL rong dung chung voi caption_fb
TRAN_TAG = {"ig": 5, "fb": 3, "tiktok": 3}
TIKTOK_TOI_DA = 150
YT_TIEU_DE_TOI_DA = 100
CACH_TIKTOK = dt.timedelta(hours=3)
HEN_TIKTOK_TOI_DA = dt.timedelta(days=6)
LENH = ("kiem", "yt", "hen-yt", "tiktok", "hen-tiktok", "ig", "fb", "hen-fb", "binh-luan")
TRANG_THAI_BO = {"cancelled", "canceled", "failed", "draft"}
KHOA_CONG_TEP = pathlib.Path("~/.claude/tools/sangame-sg-cong-khoa").expanduser()


# ---------------------------------------------------------------- phep kiem thuan
def kiem_chu(kenh, s):
    """kenh: fb|ig|tiktok|youtube_tieu_de. fb/ig/tiktok: khong URL/ten mien; tran hashtag ig 5, fb 3, tiktok 3; tiktok <= 150 ky tu;
    tieu de YouTube <= 100. Tra list loi (rong = dat)."""
    s = s or ""
    loi = []
    if not s.strip():
        return [f"{kenh}: chữ rỗng"]
    if kenh in ("fb", "ig", "tiktok"):
        thay = []
        for m in _RE_URL_RONG.finditer(s):
            if m.group(0) not in thay:
                thay.append(m.group(0))
        for u in thay:
            loi.append(f"{kenh}: có URL/tên miền {u[:60]!r} (luật 27/10: không link trong chữ đăng)")
    if kenh in TRAN_TAG:
        n = len(chung._RE_TAG.findall(s))
        if n > TRAN_TAG[kenh]:
            loi.append(f"{kenh}: {n} hashtag, trần {TRAN_TAG[kenh]}")
    if kenh == "tiktok" and len(s) > TIKTOK_TOI_DA:
        loi.append(f"tiktok: {len(s)} ký tự, trần {TIKTOK_TOI_DA}")
    if kenh == "youtube_tieu_de" and len(s) > YT_TIEU_DE_TOI_DA:
        loi.append(f"youtube_tieu_de: {len(s)} ký tự, trần {YT_TIEU_DE_TOI_DA}")
    return loi


def _khong_dau(s):
    s = unicodedata.normalize("NFD", (s or "").replace("Đ", "D").replace("đ", "d"))
    s = re.sub(r"['’`]", "", "".join(c for c in s if unicodedata.category(c) != "Mn").lower())   # Marvel's -> marvels
    return re.sub(r"[^a-z0-9]+", " ", s).strip()


def kiem_tieu_de_yt(tieu_de, ten_game):
    """Tieu de YouTube phai MO bang ten game (so khong dau, khong phan biet hoa thuong, bo dau cau dau) va khong viet hoa ca cau."""
    loi = []
    g, t = _khong_dau(ten_game), _khong_dau(tieu_de)
    if not g:
        loi.append("youtube_tieu_de: thiếu tên game (bai.json 'game') để kiểm tiêu đề mở bằng tên game")
    elif not (t == g or t.startswith(g + " ")):
        loi.append(f"youtube_tieu_de: phải MỞ bằng tên game {ten_game!r}")
    chu_cai = [c for c in (tieu_de or "") if c.isalpha()]
    if len(chu_cai) > 3 and all(c.isupper() for c in chu_cai):
        loi.append("youtube_tieu_de: viết hoa cả câu")
    return loi


def cach_gio_tiktok(gio, cac_gio_khac, toi_thieu=CACH_TIKTOK):
    """SG-TT-1: bai TikTok cach bai TikTok khac cung ngay >= 3 gio. Thuan; gio la datetime co mui gio."""
    loi = []
    for k in cac_gio_khac:
        cach = abs(gio - k)
        if cach < toi_thieu:
            loi.append(f"tiktok: giờ {gio.astimezone(VN):%d/%m %H:%M} cách bài TikTok khác {k.astimezone(VN):%d/%m %H:%M} "
                       f"chỉ {int(cach.total_seconds() // 60)} phút (cần >= {int(toi_thieu.total_seconds() // 3600)} giờ)")
    return loi


def chan(loi):
    """Co loi -> in tung dong va thoat (script tay khong dang mu)."""
    if loi:
        sys.exit("DỪNG, không đăng:\n  " + "\n  ".join(loi))


def trang_thai_yt(privacy, hen_utc=None):
    """Khoi status cua YouTube: du co (kem co AI); hen_utc ('YYYY-MM-DDTHH:MM:SSZ') them publishAt (chi hop le khi private)."""
    st = yt.trang_thai(privacy)
    if hen_utc:
        st["publishAt"] = hen_utc
    return st


def tham_yt(tieu_de, mo_ta, tags, privacy, hen_utc=None):
    """Body videos.insert / update cho video ngan. Dung yt.trang_thai (du co AI) + publishAt khi hen."""
    return {"snippet": {"title": tieu_de, "description": mo_ta, "categoryId": "20", "tags": list(tags or []),
                        "defaultLanguage": "vi", "defaultAudioLanguage": "vi"},
            "status": trang_thai_yt(privacy, hen_utc)}


def _dt(chuoi):
    t = dt.datetime.fromisoformat(str(chuoi).replace("Z", "+00:00"))
    return t if t.tzinfo else t.replace(tzinfo=dt.timezone.utc)


def _doc_trang(khoa, tham_co_ban, nguon, phan_trang):
    """Doc het cac trang GET /posts (chi doc). nguon zernio: phan trang bang cursor/pagination.nextCursor.
    nguon external: cursor KHONG dung duoc (docs) -> page/limit, dung khi trang het bai (< limit) hoac rong. Tra list post."""
    ra, cursor = [], None
    for trang in range(1, 41):
        tham = dict(tham_co_ban)
        if nguon == "external":
            tham.update({"source": "external", "page": trang})
        elif cursor:
            tham["cursor"] = cursor
        try:
            r = http.gui("GET", f"{zernio.GOC}/posts", headers=zernio._hdr(khoa), params=tham, timeout=60)
        except http.LoiMang as e:
            raise LoiDang(f"Zernio GET /posts ({nguon}): {e}") from None
        j = r.json()
        if r.status != 200 or not isinstance(j, dict) or not isinstance(j.get("posts"), list):
            raise LoiDang(f"Zernio GET /posts ({nguon}) HTTP {r.status} {chung.cat(j, 150)} — không kiểm được giờ TikTok, dừng")
        ra += [p for p in j["posts"] if isinstance(p, dict)]
        if nguon == "external":
            if len(j["posts"]) < tham["limit"]:
                return ra
        else:
            cursor = (j.get("pagination") or {}).get("nextCursor") if isinstance(j.get("pagination"), dict) else None
            if not cursor:
                return ra
    raise LoiDang(f"Zernio GET /posts ({nguon}): quá 40 trang — dừng")


def gio_tiktok_zernio(khoa, acc, ngay):
    """Gio cac bai TikTok (da dang / da hen) cua tai khoan `acc` trong NGAY VN `ngay` (date) tu Zernio GET /posts (chi doc).
    Hai nguon: mac dinh (bai tao qua Zernio) + source=external (bai dang thang tren TikTok, Zernio dong bo ve) - hop nhat, khu trung theo id.
    Loc fromDate/toDate rong 1 ngay moi ben roi loc lai theo ngay VN. Khong khoa / loi mang / phan hoi la -> LoiDang (dung, khong dang mu)."""
    if not khoa:
        raise LoiDang("Zernio: thiếu khoá — không kiểm được giờ TikTok các bài khác, dừng")
    chung.dang_ky_bi_mat(khoa)
    co_ban = {"platform": "tiktok", "accountId": acc, "fromDate": (ngay - dt.timedelta(days=1)).isoformat(),
              "toDate": (ngay + dt.timedelta(days=1)).isoformat(), "limit": 50}
    bai = _doc_trang(khoa, co_ban, "zernio", True) + _doc_trang(khoa, co_ban, "external", True)
    cac, da_thay = [], set()
    for p in bai:
        if str(p.get("status") or "").lower() in TRANG_THAI_BO:
            continue
        for pl in (p.get("platforms") if isinstance(p.get("platforms"), list) else [{}]):
            if not isinstance(pl, dict):
                continue
            if pl.get("platform") not in (None, "tiktok") or str(pl.get("status") or "").lower() in TRANG_THAI_BO:
                continue
            a = pl.get("accountId") if pl.get("accountId") is not None else p.get("accountId")
            a = a.get("_id") if isinstance(a, dict) else a
            if a is not None and str(a) != str(acc):
                continue
            ids = {str(x) for x in (p.get("_id"), p.get("id"), p.get("platformPostId"), pl.get("platformPostId")) if x}
            if ids & da_thay:
                continue
            moc = pl.get("publishedAt") or pl.get("scheduledFor") or p.get("publishedAt") or p.get("scheduledFor")
            if not moc:
                continue
            try:
                t = _dt(moc).astimezone(VN)
            except ValueError:
                continue
            if t.date() == ngay:
                cac.append(t)
                da_thay |= ids
    return cac


# ---------------------------------------------------------------- bai tay
class Bai:
    """Doc thu muc bai. Dong vai 'nc' toi thieu cho fb._bat_dau_upload (tep) va zernio (ngay/dang/manifest_sha)."""

    def __init__(self, thu_muc):
        self.thu_muc = pathlib.Path(thu_muc).resolve()
        try:
            j = json.loads((self.thu_muc / "bai.json").read_text("utf-8"))
        except (OSError, ValueError) as e:
            raise LoiDang(f"không đọc được bai.json ở {self.thu_muc}: {type(e).__name__}") from None
        try:
            self.ten, self.ngay = str(j["ten"]), str(j["ngay"])
            v = pathlib.Path(j["video"])
        except KeyError as e:
            raise LoiDang(f"bai.json thiếu khoá {e}") from None
        self.video = v if v.is_absolute() else (self.thu_muc / v).resolve()
        self.game = j.get("game") or ""
        self.tags = list(j.get("tags") or [])
        self.gio_hen = None
        if j.get("gio_hen"):
            try:
                t = dt.datetime.fromisoformat(str(j["gio_hen"]).replace("Z", "+00:00"))
            except ValueError:
                raise LoiDang(f"bai.json gio_hen sai dạng ISO: {j.get('gio_hen')!r}") from None
            if t.tzinfo is None:
                raise LoiDang("gio_hen phải có múi giờ, vd +07:00 (bai.json gio_hen=%r)" % j["gio_hen"])
            self.gio_hen = t
        self.ra = self.thu_muc / "ra"
        self.dang = self.ten
        self.manifest_sha = self.ten

    def tep(self, ban, loai="video"):
        return self.video

    def khoi(self, ten, bat_buoc=True):
        try:
            s = (self.thu_muc / "chu-video.md").read_text("utf-8")
        except OSError:
            raise LoiDang("không đọc được chu-video.md") from None
        for k in re.split(r"(?m)^## ", s)[1:]:
            dau, _, than = k.partition("\n")
            m = re.search(r"```\n(.*?)\n```", than, flags=re.S)
            if dau.strip() == ten and m:
                return m.group(1)
        if bat_buoc:
            raise LoiDang(f'không thấy khối "{ten}" trong chu-video.md')
        return None

    def mo_ta_yt(self):
        s = self.khoi("YouTube · mô tả")
        return s + "\n\n" + chung.DONG_NHAN_AI if chung.CO_GIONG_AI and chung.DONG_NHAN_AI not in s else s

    def mo_ta_fb(self):
        s = self.khoi("Facebook")
        return s + "\n\n" + chung.DONG_NHAN_AI if chung.CO_GIONG_AI and chung.DONG_NHAN_AI not in s else s

    def caption_tiktok(self):
        return self.khoi("TikTok")


# ---------------------------------------------------------------- trang thai chong trung (ra/<kenh>.json)
_KHOA_TT = {"kenh", "trang_thai", "lenh", "luc"}


def _doc(bai, kenh):
    f = bai.ra / f"{kenh}.json"
    try:
        return json.loads(f.read_text("utf-8")) if f.exists() else None
    except ValueError:
        return {"trang_thai": "dang_lam", "loi_doc": "ra/%s.json hỏng" % kenh}


def _ghi(bai, kenh, **kw):
    bai.ra.mkdir(parents=True, exist_ok=True)
    cu = _doc(bai, kenh) or {}
    cu.update({"kenh": kenh, "luc": time.strftime("%Y-%m-%d %H:%M:%S"), **kw})
    dich = bai.ra / f"{kenh}.json"
    tam = bai.ra / f"{kenh}.json.tmp"
    tam.write_text(json.dumps(cu, ensure_ascii=False, indent=1), "utf-8")
    os.replace(tam, dich)    # nguyen tu: khong bao gio de lai file ghi do
    return cu


@contextlib.contextmanager
def _khoa_doc_quyen(bai, kenh):
    """Khoa doc quyen theo (thu muc bai, kenh): ra/<kenh>.lock tao bang O_CREAT|O_EXCL, giu suot lenh, xoa trong finally.
    Da co lock (lenh khac dang chay / lan truoc chet giua chung) -> dung, khong xoa tu dong."""
    bai.ra.mkdir(parents=True, exist_ok=True)
    f = bai.ra / f"{kenh}.lock"
    try:
        fd = os.open(f, os.O_CREAT | os.O_EXCL | os.O_WRONLY, 0o600)
    except FileExistsError:
        sys.exit(f"DỪNG {kenh}: lệnh khác đang chạy / lần trước chết giữa chừng — kiểm tay rồi xoá ra/{kenh}.lock")
    try:
        os.write(fd, str(os.getpid()).encode())
        os.close(fd)
        yield
    finally:
        try:
            f.unlink()
        except OSError:
            pass


def _co_id(d):
    return any(k not in _KHOA_TT and v for k, v in (d or {}).items())


def _xet_trang_thai(bai, kenh):
    """Chi DOC. True = chua co gi, duoc lam. Da 'xong' -> in bo qua, False. Dang 'dang_lam' (lan truoc do dang, co the da dang) -> dung."""
    d = _doc(bai, kenh)
    if d is None:
        return True
    if d.get("trang_thai") == "xong":
        print(f"BỎ QUA {kenh}: ra/{kenh}.json đã xong ({d.get('link') or d.get('video_id') or d.get('id') or ''})")
        return False
    ids = {k: v for k, v in d.items() if k not in _KHOA_TT}
    sys.exit(f"DỪNG {kenh}: lần trước đang làm dở (dang_lam), có thể ĐÃ đăng — kiểm tay id {ids or '(chưa ghi id)'} "
             f"rồi sửa/xoá ra/{kenh}.json; KHÔNG tạo bài mới.")


def _that_bai(bai, kenh, e):
    """Loi chac chan chua dang + chua co id nao -> go dau dang_lam de chay lai duoc. Con lai giu nguyen (kiem tay)."""
    d = _doc(bai, kenh)
    if isinstance(e, LoiDang) and not e.khong_ro and d and d.get("trang_thai") == "dang_lam" and not _co_id(d):
        try:
            (bai.ra / f"{kenh}.json").unlink()
        except OSError:
            pass


# ---------------------------------------------------------------- khoa, token, video len kho
def _khoa_zernio():
    k = os.environ.get("ZERNIO_KHOA", "").strip()
    if not k:
        try:
            k = subprocess.check_output(["security", "find-generic-password", "-s", "zernio-san-game", "-w"],
                                        stderr=subprocess.DEVNULL).decode().strip()
        except (OSError, subprocess.CalledProcessError):
            k = ""
    if k:
        chung.dang_ky_bi_mat(k)
    return k


def _tk(kenh):
    """Token + kiem danh tinh khop dich.json (nhu may tu dong)."""
    if not os.environ.get("SG_CONG_KHOA") and KHOA_CONG_TEP.exists():
        os.environ["SG_CONG_KHOA"] = KHOA_CONG_TEP.read_text().strip()
    try:
        cong = so.Cong()
    except so.LoiCong as e:
        raise LoiDang(str(e)) from None
    tk = chay.tai_token(cong, kenh)
    chay.kiem_danh_tinh(kenh, tk, None, chay.nap_dich())
    return tk


def _url_cong_khai(khoa, tep, ten):
    """Tai video len kho Zernio (presign) -> publicUrl truc tiep (IG / TikTok can URL). Loi truoc khi tao bai -> LoiDang chac chan."""
    du = pathlib.Path(tep).read_bytes()
    try:
        r = http.gui("POST", f"{zernio.GOC}/media/presign", headers=zernio._hdr(khoa), timeout=60,
                     json_body={"filename": ten, "contentType": "video/mp4", "size": len(du)})
        j = r.json()
        if r.status not in (200, 201) or not j.get("uploadUrl") or not j.get("publicUrl"):
            raise LoiDang(f"Zernio presign HTTP {r.status} (chưa tạo bài)")
        chung.dang_ky_bi_mat(j["uploadUrl"])
        u = http.gui("PUT", j["uploadUrl"], data=du, headers={"Content-Type": "video/mp4"}, timeout=900)
    except http.LoiMang as e:
        raise LoiDang(f"Zernio tải video: {e} (chưa tạo bài)") from None
    if u.status != 200:
        raise LoiDang(f"Zernio PUT video HTTP {u.status} (chưa tạo bài)")
    return j["publicUrl"]


# ---------------------------------------------------------------- kiem truoc (khong tac dung)
def _gio_dang(bai, hen):
    """Gio dang du kien cua lenh: hen-* = gio_hen (phai cach bay gio >= 10 phut); lenh dang ngay = bay gio."""
    if not hen:
        return chung.bay_gio()
    if bai.gio_hen is None:
        raise LoiDang("bai.json thiếu gio_hen cho lệnh hen-*")
    if bai.gio_hen < chung.bay_gio() + dt.timedelta(minutes=10):
        raise LoiDang(f"gio_hen {bai.gio_hen.astimezone(VN):%d/%m %H:%M} phải cách bây giờ >= 10 phút")
    return bai.gio_hen


def kiem_truoc(bai, lenh):
    """Moi phep kiem chu / gio TRUOC moi goi mang co tac dung. Tra list loi."""
    hen = lenh.startswith("hen-")
    kenh = lenh.replace("hen-", "")
    loi = []
    try:
        if not bai.video.exists():
            loi.append(f"không thấy video {bai.video}")
        if kenh == "yt":
            td = bai.khoi("YouTube · tiêu đề").strip()
            bai.khoi("YouTube · mô tả")
            loi += kiem_chu("youtube_tieu_de", td) + kiem_tieu_de_yt(td, bai.game)
        elif kenh == "tiktok":
            loi += kiem_chu("tiktok", bai.caption_tiktok())
            gio = _gio_dang(bai, hen)
            if hen and gio > chung.bay_gio() + HEN_TIKTOK_TOI_DA:
                loi.append("hen-tiktok: gio_hen tối đa 6 ngày kể từ bây giờ (link media presign Zernio tạm hết hạn sau 7 ngày)")
            loi += cach_gio_tiktok(gio, gio_tiktok_zernio(_khoa_zernio(), zernio._acc(), gio.astimezone(VN).date()))
        elif kenh == "ig":
            loi += kiem_chu("ig", bai.khoi("Instagram"))
        elif kenh == "fb":
            loi += kiem_chu("fb", bai.khoi("Facebook"))
            if hen:
                gio = _gio_dang(bai, hen)
                if gio > chung.bay_gio() + dt.timedelta(days=29):
                    loi.append("hen-fb: Facebook chỉ hẹn tối đa 29 ngày")
        if hen and kenh != "tiktok":
            _gio_dang(bai, hen)
    except LoiDang as e:
        loi.append(str(e))
    return loi


def _binh_luan_fb(bai):
    return bai.khoi("Bình luận", bat_buoc=False)


# ---------------------------------------------------------------- cac lenh dang
def lam_yt(bai, hen=False):
    """Tai len PRIVATE khong publishAt -> xac nhan co AI -> roi moi public (yt) hoac private+publishAt (hen-yt)."""
    tk = _tk("youtube")
    tieu_de, mo_ta = bai.khoi("YouTube · tiêu đề").strip(), bai.mo_ta_yt()
    du = bai.video.read_bytes()
    body = tham_yt(tieu_de, mo_ta, bai.tags, "private")
    try:
        r = http.gui("POST", yt.UPLOAD, timeout=60, params={"uploadType": "resumable", "part": "snippet,status"}, json_body=body,
                     headers={**yt._hdr(tk), "X-Upload-Content-Length": str(len(du)), "X-Upload-Content-Type": "video/mp4"})
    except http.LoiMang as e:
        raise LoiDang(f"YouTube khởi tạo tải lên: {e}") from None
    url = r.headers.get("location")
    if r.status != 200 or not url:
        raise LoiDang(f"YouTube khởi tạo tải lên thất bại: HTTP {r.status} {chung.cat(r.json())}")
    chung.dang_ky_bi_mat(url)
    res = yt.tai_len(url, du, tk)
    vid = str(res.get("id") or "")
    if not vid:
        raise LoiDang("YouTube tải xong nhưng không trả video id", khong_ro=True)
    _ghi(bai, "youtube", video_id=vid, link=f"https://www.youtube.com/shorts/{vid}")
    xn = yt.xac_nhan_ai(tk, vid, res)     # khong xac nhan duoc -> LoiDang khong_ro, video de rieng tu
    if not hen:
        yt.cong_khai(tk, None, {"id_tai": vid})     # PUT public, doc co AI trong phan hoi, thieu -> keo ve private + loi
        hen_utc = None
    else:
        hen_utc = bai.gio_hen.astimezone(dt.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
        st = tham_yt(tieu_de, mo_ta, bai.tags, "private", hen_utc)["status"]
        q = _put_status(tk, vid, st)
        if q is None or q.status != 200 or (chung.CO_GIONG_AI and yt.doc_co_ai(q.json()) is not True):
            # khong hen duoc / hen ma khong thay co AI -> go publishAt (private tron) de khong tu cong khai thieu nhan
            rb = _put_status(tk, vid, trang_thai_yt("private"))
            if rb is None or rb.status != 200:
                raise LoiDang(f"YouTube hẹn giờ không đạt VÀ gỡ publishAt THẤT BẠI — video {vid} CÓ THỂ VẪN HẸN publishAt "
                              f"(không xác nhận nhãn AI): gỡ tay trong YouTube Studio ngay", khong_ro=True)
            raise LoiDang(f"YouTube hẹn giờ không đạt (HTTP {q.status if q is not None else 'mạng'}) hoặc không xác nhận nhãn AI "
                          f"— video {vid} để riêng tư, đã gỡ publishAt", khong_ro=True)
    _ghi(bai, "youtube", trang_thai="xong", hen=hen_utc, **{k: v for k, v in xn.items() if k == "nhan_ai"})
    print("youtube xong:", f"https://www.youtube.com/shorts/{vid}", "hẹn" if hen else "công khai", xn)


def _put_status(tk, vid, st):
    """videos.update part=status; tra Phan hoac None khi loi mang."""
    try:
        return http.gui("PUT", f"{yt.API}/videos", headers=yt._hdr(tk), params={"part": "status"}, json_body={"id": vid, "status": st}, timeout=30)
    except http.LoiMang:
        return None


def _body_tiktok(caption, acc, url, hen=None):
    tt = {"privacy_level": zernio.PUBLIC, "allow_comment": True, "allow_duet": True, "allow_stitch": True,
          "content_preview_confirmed": True, "express_consent_given": True}
    if chung.CO_GIONG_AI:
        tt["video_made_with_ai"] = True
    body = {"content": caption, "mediaItems": [{"type": "video", "url": url}],
            "platforms": [{"platform": "tiktok", "accountId": acc}], "tiktokSettings": tt}
    if hen is not None:
        body["scheduledFor"] = hen.astimezone(VN).isoformat()
    else:
        body["publishNow"] = True
    return body


def lam_tiktok(bai, hen=False):
    khoa = _khoa_zernio()
    acc = zernio._acc()
    zernio.kiem_truoc(khoa, acc)
    url = _url_cong_khai(khoa, bai.video, f"{bai.ten}-tiktok.mp4")
    body = _body_tiktok(bai.caption_tiktok(), acc, url, bai.gio_hen if hen else None)
    idem = hashlib.sha256(f"ngan|{bai.ten}|{bai.ngay}|tiktok|{'hen' if hen else 'ngay'}".encode()).hexdigest()
    try:
        r = http.gui("POST", f"{zernio.GOC}/posts", headers=zernio._hdr(khoa, **{"Idempotency-Key": idem}), json_body=body, timeout=120)
    except http.LoiMang as e:
        raise LoiDang(f"Zernio tạo bài: {e} — không rõ đã tạo chưa", khong_ro=True) from None
    j = r.json()
    if r.status == 409 or r.status >= 500:
        raise LoiDang(f"Zernio tạo bài HTTP {r.status} — không rõ đã tạo chưa (existingPostId={j.get('existingPostId')})", khong_ro=True)
    if 400 <= r.status < 500:
        raise LoiDang(f"Zernio tạo bài HTTP {r.status} {chung.cat(j.get('error') or j.get('message') or '', 120)} (chưa tạo bài)")
    post = j.get("post") if isinstance(j.get("post"), dict) else j
    pid = str(post.get("_id") or post.get("id") or "")
    if not pid:
        raise LoiDang(f"Zernio HTTP {r.status} không trả id bài", khong_ro=True)
    _ghi(bai, "tiktok", id_bai=pid)
    if hen:
        _ghi(bai, "tiktok", trang_thai="xong", hen=body["scheduledFor"], trang_thai_zernio=post.get("status"))
        print("tiktok hẹn xong:", pid, post.get("status"))
        return
    kq, ket = zernio._xet(post, r.status)
    if kq != "xong":
        ket = zernio.hoi_den_xong(khoa, pid)
    _ghi(bai, "tiktok", trang_thai="xong", link=ket.get("link"))
    print("tiktok xong:", ket.get("link") or pid)


def lam_ig(bai):
    tk = _tk("ig")
    khoa = _khoa_zernio()
    url = _url_cong_khai(khoa, bai.video, f"{bai.ten}-ig.mp4")
    c = ig.tao_container(tk, ig.tham_container(url, None, bai.khoi("Instagram")))
    cid = str(c.get("id") or "")
    if not cid:
        raise LoiDang("IG không trả container id")
    _ghi(bai, "ig", id_container=cid)
    meta.cho_trang_thai(lambda: ig._status(tk, cid), {"FINISHED"}, {"ERROR", "EXPIRED"}, toi_da=60, ten="IG reel")
    ket = ig.cong_khai(tk, None, {"id_container": cid})
    _ghi(bai, "ig", trang_thai="xong", id=ket.get("id_bai"), link=ket.get("link"))
    print("ig xong:", ket)


def lam_fb(bai, hen=False):
    tk = _tk("fb")
    page = tk["page_id"]
    mo_ta = bai.mo_ta_fb()
    vid = fb._bat_dau_upload(tk, bai, page, lambda **kw: _ghi(bai, "fb", video_id=kw["id_tai"]))
    if hen:
        tham = fb.tham_finish(vid, mo_ta, "SCHEDULED", int(bai.gio_hen.timestamp()))
    else:
        tham = fb.tham_finish(vid, mo_ta, "PUBLISHED")
    f = fb.finish(tk, page, tham)
    if f.get("success") is not True:
        raise LoiDang(f"FB finish không trả success: {chung.cat(f)}", khong_ro=True)
    _ghi(bai, "fb", trang_thai="xong", link=f"https://www.facebook.com/reel/{vid}/", hen=tham.get("scheduled_publish_time"))
    print("fb xong:", vid, "hẹn" if hen else "công khai")


def lam_binh_luan(bai, nd):
    """Chi FB/IG, noi dung tu khoi 'Binh luan' (da kiem khong URL). Theo doi RIENG tung dich trong ra/binh-luan.json:
    ra/binh-luan.json[fb|ig] = id binh luan; <dich>_dang_lam = da gui ma chua ghi id (chay lai -> dung kiem tay, khong binh luan trung).
    Dich chua dang (khong co ra/<dich>.json trang_thai xong) hoac FB bai hen chua cong khai -> bo qua lan nay.
    trang_thai 'xong' chi khi MOI dich co ra/<dich>.json deu da binh luan."""
    dich = (("fb", "video_id", fb.G), ("ig", "id", ig.G))
    for k, khoa_id, goc in dich:
        f = _doc(bai, k)
        st = _doc(bai, "binh-luan") or {}
        if not f or f.get("trang_thai") != "xong" or not f.get(khoa_id):
            print(f"{k}: chưa đăng xong — bỏ qua bình luận lần này")
            continue
        if st.get(k):
            print(f"{k}: đã bình luận ({st[k]})")
            continue
        if st.get(k + "_dang_lam"):
            sys.exit(f"DỪNG binh-luan {k}: lần trước đã gửi bình luận mà chưa ghi id — kiểm tay trên {k.upper()} rồi sửa ra/binh-luan.json")
        tk = _tk(k)
        if k == "fb" and f.get("hen"):
            try:
                da = fb._da_cong_khai(tk, f[khoa_id])
            except LoiDang:
                da = False
            if not da:
                print("fb: Reel hẹn giờ chưa công khai — bỏ qua bình luận lần này")
                continue
        _ghi(bai, "binh-luan", **{k + "_dang_lam": True})
        cid = meta.goi(goc, "POST", f"/{f[khoa_id]}/comments", token=tk["page_token"], co_tac_dung=True, tham_so={"message": nd})["id"]
        _ghi(bai, "binh-luan", **{k: cid, k + "_dang_lam": False})
        print(f"{k}: đã bình luận ({cid})")
    st = _doc(bai, "binh-luan") or {}
    co = [k for k, _, _ in dich if _doc(bai, k)]
    if co and all(st.get(k) for k in co):
        _ghi(bai, "binh-luan", trang_thai="xong")
        print("bình luận xong:", {k: st.get(k) for k in co})
    else:
        print("bình luận chưa đủ đích — chạy lại sau khi các đích còn lại đã đăng/công khai")


def _loi_tiktok_chu(bai):
    try:
        return kiem_chu("tiktok", bai.caption_tiktok())
    except LoiDang as e:
        return [str(e)]


def _kiem_binh_luan(bai):
    """Binh luan FB lan IG deu cam URL/ten mien (SG-FB-2; IG khong bam duoc link)."""
    nd = _binh_luan_fb(bai)
    if nd and _RE_URL_RONG.search(nd):
        return ["binh-luan: bình luận có URL/tên miền (SG-FB-2: không link ở bình luận Reel FB/IG)"]
    return []


def lam_kiem(bai):
    """Kiem het (doc / khong tac dung): file, chu, token+danh tinh, khoa Zernio, gio TikTok neu co gio_hen."""
    loi = []
    for lenh in ("yt", "ig", "fb"):
        loi += kiem_truoc(bai, lenh)
    loi += kiem_truoc(bai, "hen-tiktok") if bai.gio_hen else _loi_tiktok_chu(bai)
    loi += _kiem_binh_luan(bai)
    for kenh in ("youtube", "fb", "ig"):
        try:
            _tk(kenh)
            print(kenh, "danh tính OK")
        except (LoiDang, SystemExit, KeyError) as e:
            loi.append(f"{kenh}: {e}")
    print("zernio khoá:", bool(_khoa_zernio()), "· video:", bai.video, bai.video.exists())
    chan(loi)
    print("KIỂM ĐẠT")


def main(argv=None):
    a = list(sys.argv[1:] if argv is None else argv)
    if len(a) != 2 or a[1] not in LENH:
        sys.exit("python -m dang.ngan <thu-muc-bai> " + "|".join(LENH))
    thu_muc, lenh = a
    try:
        bai = Bai(thu_muc)
        if lenh == "kiem":
            return lam_kiem(bai)
        if lenh == "binh-luan":
            nd = _binh_luan_fb(bai)
            if not nd:      # kiem TRUOC khoa/trang thai: khong co khoi thi khong de lai dau vet
                print("Không có khối 'Bình luận' trong chu-video.md — không bình luận.")
                return
            chan(_kiem_binh_luan(bai))
            with _khoa_doc_quyen(bai, "binh-luan"):
                return lam_binh_luan(bai, nd)
        kenh = {"yt": "youtube", "hen-yt": "youtube", "tiktok": "tiktok", "hen-tiktok": "tiktok", "ig": "ig", "fb": "fb", "hen-fb": "fb"}[lenh]
        with _khoa_doc_quyen(bai, kenh):
            if not _xet_trang_thai(bai, kenh):
                return
            chan(kiem_truoc(bai, lenh))
            _ghi(bai, kenh, trang_thai="dang_lam", lenh=lenh)    # TRUOC moi goi mang co tac dung
            try:
                if lenh in ("yt", "hen-yt"):
                    lam_yt(bai, lenh == "hen-yt")
                elif lenh in ("tiktok", "hen-tiktok"):
                    lam_tiktok(bai, lenh == "hen-tiktok")
                elif lenh == "ig":
                    lam_ig(bai)
                else:
                    lam_fb(bai, lenh == "hen-fb")
            except Exception as e:
                _that_bai(bai, kenh, e)
                raise
    except LoiDang as e:
        sys.exit(("KHÔNG RÕ — KIỂM TAY, KHÔNG chạy lại: " if e.khong_ro else "LỖI: ") + str(e))


if __name__ == "__main__":
    main()
