"""Chu dang + cong "tin gia" cho 3 khuon FB Reel / IG Reel / Threads anh+chu (THUAN: khong mang, khong tep).
(khuon/tin-gia-mxh/KE-HOACH.md muc 4.3 + BO SUNG OPUS 4, 5, 12 + SUA SAU SOI SOL S6, S9, S11, S14; muc sau DE len muc truoc)

  dung_chu(kenh, su_that, ngay=None, mo_da_dung=())  ->  {"text", "alt" (threads), "ma_bien_the" (threads)} hoac None (chu khong vua)
  cong(kenh, text, su_that)                          ->  [ly do truot] ([] = dat) - FAIL-CLOSED, khop kiem-khuon.py cua dieu phoi.

`su_that` do dang/tin_gia_chon.py dung: moi so tien o day la so DA KIEM TRANG; chu chi duoc dung nhung so do.
"""
import datetime as dt
import re

from . import chung
from .chay import tien_vnd
from .tin_gia_chon import han_cau, hien_tien, nghin_dung as _nghin, so_vn
from .x_goc import _RE_BAN, ten_dep

NIEM_YET = "Giá niêm yết, chưa gồm thuế nếu có."
LOAI = {"fb": "sg-fb-gia", "ig": "sg-ig-gia", "threads": "sg-threads-gia"}     # --loai cua kiem-khuon.py
TRAN_CHU = {"fb": 600, "ig": 2200}
TRAN_TAG = {"fb": 3, "ig": 5, "threads": 0}
THREADS_KY_TU, THREADS_BYTE, ALT_TOI_DA = 450, 500, 1000
NGAY_MOC = dt.date(2026, 11, 1)
TOPIC_TAG = "PlayStation"

# Threads: 8 cau mo x 4 cau ket (S14). {N} = "460 nghìn", {A} {B} = ten game.
MO = (
    "Có {N}, anh em chọn {A} hay {B}?",
    "{N} trong túi: {A} hay {B}, chọn game nào?",
    "Cùng {N}, mua {A} hay {B}?",
    "Ngân sách {N} thì nên lấy {A} hay {B}?",
    "Hai game cùng {N}: {A} và {B}. Bạn chọn bên nào?",
    "Túi còn {N}, chọn {A} hay {B} cho tuần này?",
    "{N} mua được một game: {A} hay {B}?",
    "Đang phân vân giữa {A} và {B}, cùng giá {N}, bạn chọn gì?",
)
KET = (
    "Bạn chọn bản nào, vì sao?",
    "Anh em nghiêng về bên nào?",
    "Nếu là bạn thì lấy game nào trước?",
    "Ai chơi rồi thấy game nào đáng tiền hơn?",
)

LA_MA = frozenset("II III IV V VI VII VIII IX X XI XII XIII XIV XV XVI XVII XVIII XIX XX".split())
TU_NHO = frozenset("OF AND FOR IN TO OR ON AT AN".split())   # Opus 02/11: bo THE (ten game hay mo phu de bang "The": "Final Fantasy XII The Zodiac Age")
# tu thong thuong 3 chu cai: chi viet Hoa Chu Dau khi CA TEN deu HOA (ten HOA toan bo nhu 'ZODIAC AGE'); ten tron lan giu nguyen (NBA, GTA...)
TU_PHO_THONG = frozenset("THE AGE WAR ONE DAY END NEW OLD SKY SUN MAN RED SEA ICE KEY ALL ART AIR BAD BIG CAT DOG EYE FAR FUN HOT JOY LAW LOW MAD OUR OUT RUN SIX TEN TWO WAY WIN YOU BOY".split())
# khop CAM_SG + URL + ten mien cua kiem-khuon.py (dieu phoi)
CAM_SG = re.compile(r"bình luận|comment|cmt|(?<!#)\btag\b|share|chia sẻ|(?<!#)\blike\b|thả tim|follow|theo dõi|giveaway|tặng|giọng đọc ai", re.I)
URL = re.compile(r"https?://|www\.", re.I)
TEN_MIEN = re.compile(r"\b[\w-]+\.(?:com|vn|net)\b", re.I)
TAG = re.compile(r"#\w+")
KIEU_K = re.compile(r"\d+\s*[kK]\b")
RE_NGOAI_TE = re.compile(r"(?:HK\$|US\$|S\$|\$|SGD\s?|THB\s?|IDR\s?|Rp\s?|฿)\d[\d.,]*")
RE_PHAN_TRAM = re.compile(r"(\d+(?:[.,]\d+)?)\s*%")      # bat ca so thap phan: 88,99% != 88%


# ---------------------------------------------------------------- ten doc duoc (BO SUNG 4)
def _tu(w, i, toan_hoa=False):
    chu = re.sub(r"[^\w]", "", w)
    if not chu or not w.isupper():
        return w
    if chu in LA_MA:
        return w
    if chu in TU_NHO and i > 0:
        return w.lower()
    if len(chu) <= 3 and not (toan_hoa and chu in TU_PHO_THONG):
        return w
    return "-".join(p if re.search(r"\d", p) else p.capitalize() for p in w.split("-"))      # 2K24 giu nguyen, TYPE-0 -> Type-0


def ten_chu(ten):
    """'FINAL FANTASY VII REBIRTH' -> 'Final Fantasy VII Rebirth'. Tu HOA dai > 3 ky tu -> Viet Hoa Chu Dau; giu so La Ma va tu <= 3 ky tu
    (HD, PS4, RE); bo ™®©, ngoac ngon ngu, duoi nen tang. Ten da viet thuong giu nguyen. (Chi cho CHU DANG; video/anh giu ten HOA.)"""
    tu = ten_dep(ten).split()
    toan_hoa = all(w.isupper() for w in tu if re.search(r"[^\W\d_]", w))
    return " ".join(_tu(w, i, toan_hoa) for i, w in enumerate(tu))


def ten_chu_ngan(ten):
    """ten_chu + bo duoi edition chuan o cuoi (Complete/Definitive/Deluxe... Edition) khi can rut."""
    day_du = ten_chu(ten)
    return _RE_BAN.sub("", day_du).strip(" -–:") or day_du


def _vung_cau(sv):
    return sv["vung"]


# ---------------------------------------------------------------- FB
def chu_fb(sv):
    ten = ten_chu(sv["ten_goc"])
    rh = sv["re_hon"]
    d1 = f"{ten} còn {_nghin(sv['gia_vnd'])} ở Store {sv['vung']}: {sv['the_chu']} vừa khít với giá niêm yết {sv['gia_game']}."
    d2 = (f"Rẻ hơn Store {rh['ten']} {_nghin(rh['vnd'])}. Giảm {sv['giam']}% (gốc {sv['goc']}) tới {han_cau(sv['han'])}. "
          "Thẻ nạp phải cùng vùng tài khoản PSN.")
    tags = " ".join(chung.bo_hashtag(ten, TRAN_TAG["fb"], (), chung.BO_TAG["fb"]))
    sv["ten_dung"] = [ten]
    return "\n\n".join(p for p in (d1, d2, NIEM_YET, tags) if p)


# ---------------------------------------------------------------- IG
def chu_ig(sv):
    games = sv["game"]                       # dat -> re
    n = len(games)
    ip = sv["ip"].title() if sv.get("ip") else "PS"
    gt = "giảm sớm nhất tới" if sv.get("han_khac") else "giảm tới"
    vc = sv.get("vung_chung")
    d1 = f"{n} game {ip} từ {_nghin(games[-1]['gia_vnd'])}, {gt} {han_cau(sv['han'])}" + (f" ở PS Store {vc}" if vc else "") + "."
    ten_ds = [ten_chu(g["ten_goc"]) for g in games]
    cap = [f"{t} – {_nghin(g['gia_vnd'])}" + ("" if vc else f" (Store {g['vung']})") for t, g in zip(reversed(ten_ds), reversed(games))]
    d2 = "; ".join(cap) + "."
    d3 = f"Cần tài khoản PSN {vc}, thẻ nạp phải cùng vùng." if vc else "Cần tài khoản PSN đúng vùng của từng game, thẻ nạp phải cùng vùng."
    tags = " ".join(chung.bo_hashtag(ip if sv.get("ip") else "", TRAN_TAG["ig"], (), chung.BO_TAG["ig"]))
    sv["ten_dung"] = ten_ds
    return "\n\n".join(p for p in (d1, d2, d3, "Bảng giá đủ vùng: link ở bio.", NIEM_YET, tags) if p)


# ---------------------------------------------------------------- Threads
def _sao(d):
    return f"{d['tb']:.2f}".replace(".", ",")


def _ghep_threads(sv, m, k, cap):
    """Ghep 1 bai Threads theo cau mo m, cau ket k, muc rut cap (0 day du, 1 ten ngan, 2 bo 'khoang N' + nhan xet PS5, 3 bo '(giam g%)')."""
    ten = ten_chu_ngan if cap >= 1 else ten_chu
    a, b, x, y = ten(sv["a"]), ten(sv["b"]), ten(sv["chon_ten"]), ten(sv["khac_ten"])
    n = _nghin(sv["gia_vnd"])
    p1 = MO[m].format(N=n, A=a, B=b)
    than = f"Cả hai đang {sv['gia_hien']} ở PS Store {sv['vung']}"
    if sv.get("giam") and cap < 3:
        than += f" (giảm {sv['giam']}%)"
    than += f" tới {han_cau(sv['han'])}, {sv['the_chu']} vừa khít với giá niêm yết"
    if cap < 2:
        than += f", khoảng {n}"
    than += "."
    d, dk = sv["chon_diem"], sv["khac_diem"]
    if sv["ly_chon"] == "luot":
        chon = f"Mình chọn {x}: {so_vn(d['so_luot'])} người chấm, trung bình {_sao(d)} sao"
        if sv.get("chon_la_ps5") and cap < 2:
            chon += ", lại là bản PS5 còn bên kia là bản PS4"
        chon += "."
    else:
        chon = f"Mình chọn {x}: {_sao(d)} sao so với {_sao(dk)} của {y}."
    p3 = f"Mua ở Store {sv['vung']} cần tài khoản PSN {sv['vung']}. {NIEM_YET} {KET[k]}"
    return "\n\n".join([p1, f"{than} {chon}", p3]), [a, b]


def alt_threads(sv):
    a, b = ten_chu(sv["a"]), ten_chu(sv["b"])
    return (f"Ảnh so sánh hai game {a} và {b}, cùng giá {_nghin(sv['gia_vnd'])} tại PS Store {sv['vung']}, "
            "kèm điểm đánh giá của người chơi trên PS Store.")[:ALT_TOI_DA]


def vua_threads(text):
    return len(text) <= THREADS_KY_TU and len(text.encode("utf-8")) <= THREADS_BYTE


def mo_da_dung_tu_dong(cac_dong):
    """Cac dong sg_dang `threads-gia` (7 ngay, khac that_bai/bo) -> set cau mo da dung {'m0', 'm3'}; id_container dang 'm<i>-k<j>'."""
    ra = set()
    for r in cac_dong:
        if r.get("dang") != "threads-gia" or r.get("trang_thai") in ("that_bai", "bo"):
            continue
        mm = re.match(r"(m\d+)-k\d+$", str(r.get("id_container") or ""))
        if mm:
            ra.add(mm.group(1))
    return ra


def chu_threads(sv, ngay, mo_da_dung=()):
    """-> (text, ma_bien_the 'm<i>-k<j>') hoac None (het cau mo trong 7 ngay / khong vua 450 ky tu + 500 byte)."""
    i0 = (ngay - NGAY_MOC).days
    nm, nk = len(MO), len(KET)
    for dm in range(nm):
        m = (i0 + dm) % nm
        if f"m{m}" in mo_da_dung:
            continue
        for cap in range(4):
            for dk in range(nk):
                k = (i0 + dk) % nk
                text, ten = _ghep_threads(sv, m, k, cap)
                if vua_threads(text):
                    sv["ten_dung"] = ten
                    return text, f"m{m}-k{k}"
    return None


def dung_chu(kenh, sv, ngay=None, mo_da_dung=()):
    """-> dict(text, alt?, ma_bien_the?) hoac None."""
    if kenh == "fb":
        return {"text": chu_fb(sv)}
    if kenh == "ig":
        return {"text": chu_ig(sv)}
    kq = chu_threads(sv, ngay, mo_da_dung)
    if kq is None:
        return None
    return {"text": kq[0], "ma_bien_the": kq[1], "alt": alt_threads(sv)}


# ---------------------------------------------------------------- cong tin gia (FAIL-CLOSED)
def _chuan_tien(s):
    return re.sub(r"\s+", "", s).rstrip(".,")


def tap_ngoai_te(sv):
    """Cac chuoi tien ngoai te CHI duoc xuat hien trong chu: gia game, gia goc, menh gia the (da kiem trang)."""
    ra = {_chuan_tien(sv[k]) for k in ("gia_game", "goc", "du", "gia_hien") if sv.get(k)}
    ra |= {_chuan_tien(hien_tien(t[0], sv["tien"])) for t in sv.get("the") or [] if sv.get("tien")}
    return ra


def tap_phan_tram(sv):
    ra = {str(sv["giam"])} if sv.get("giam") else set()
    return ra | {str(g["giam"]) for g in sv.get("game") or [] if g.get("giam")}


def _cum_vai_tro(kenh, text, sv):
    """Cong theo VAI TRO: caption BAT BUOC chua dung cac cum sinh tu su_that (doi gia ban <-> gia goc, doi menh gia the, doi so tam, doi %...
    deu lam mat cum -> truot)."""
    can = []
    if kenh == "fb":
        t = sv["ten_goc"] and ten_chu(sv["ten_goc"])
        can = [f"{t} còn {_nghin(sv['gia_vnd'])} ở Store {sv['vung']}", f"{sv['the_chu']} vừa khít với giá niêm yết {sv['gia_game']}.",
               f"gốc {sv['goc']})", f"Giảm {sv['giam']}% ", f"tới {han_cau(sv['han'])}"]
    elif kenh == "ig":
        gt = "giảm sớm nhất tới" if sv.get("han_khac") else "giảm tới"
        can = [f"{gt} {han_cau(sv['han'])}"]
    else:
        can = [f"Cả hai đang {sv['gia_hien']}", f"{sv['the_chu']} vừa khít với giá niêm yết"]
    return [f'thieu cum bat buoc "{c}"' for c in can if c not in text]


def cong(kenh, text, sv):
    """Moi dieu kien khong chung minh duoc = truot. -> list ly do (rong = dat)."""
    loi = []
    dong = [d.strip() for d in (text or "").strip().split("\n") if d.strip()]
    if not dong:
        return ["chu rong"]
    gia_mua, da_kiem = set(sv.get("gia_mua") or ()), set(sv.get("gia_da_kiem") or ())
    if not gia_mua:
        return ["su_that thieu gia_mua (khong chung minh duoc gia)"]
    d1 = tien_vnd(dong[0])
    if not d1:
        loi.append("dong 1 khong co so tien VND")
    elif not set(d1) <= gia_mua:
        loi.append(f"dong 1 co tien VND {sorted(set(d1))} ngoai gia mua da kiem {sorted(gia_mua)}")
    cho_phep = set(gia_mua)
    rh = sv.get("re_hon")
    if rh:
        hieu = {a - b for a in da_kiem for b in da_kiem if a > b}
        if rh["vnd"] not in hieu:
            loi.append(f"re_hon {rh['vnd']} khong la hieu hai gia da kiem {sorted(da_kiem)}")
        else:
            cho_phep.add(rh["vnd"])
    la = sorted(set(tien_vnd(text)) - cho_phep)
    if la:
        loi.append(f"co tien VND {la} ngoai tap cho phep {sorted(cho_phep)}")
    la_nt = sorted({_chuan_tien(m) for m in RE_NGOAI_TE.findall(text)} - tap_ngoai_te(sv))
    if la_nt:
        loi.append(f"co tien ngoai te {la_nt} ngoai gia da kiem (gia game/gia goc/menh gia the)")
    la_pt = sorted(set(RE_PHAN_TRAM.findall(text)) - tap_phan_tram(sv))
    if la_pt:
        loi.append(f"co phan tram {la_pt}% ngoai % giam da kiem {sorted(tap_phan_tram(sv))}")
    loi += _cum_vai_tro(kenh, text, sv)
    if KIEU_K.search(text):
        loi.append('co so dang "N K" (chi duoc nghìn/triệu)')
    if NIEM_YET not in text:
        loi.append("thieu cau 'Giá niêm yết, chưa gồm thuế nếu có.'")
    if "là đủ" in text:
        loi.append('co cum "là đủ" (thue)')
    if URL.search(text) or TEN_MIEN.search(text):
        loi.append("co URL / ten mien")
    loi += [f'xin tuong tac / nhan AI: "{m}"' for m in sorted({x.lower() for x in CAM_SG.findall(text)})]
    if "!!!" in text:
        loi.append("co '!!!'")
    n_tag = len(TAG.findall(text))
    if n_tag > TRAN_TAG[kenh]:
        loi.append(f"{n_tag} hashtag > {TRAN_TAG[kenh]}")
    if kenh in TRAN_CHU and len(text) > TRAN_CHU[kenh]:
        loi.append(f"dai {len(text)} > {TRAN_CHU[kenh]}")
    ten = [t for t in sv.get("ten_dung") or [] if t]
    if not ten:
        loi.append("chua biet ten game dung trong chu")
    loi += [f'ten "{t}" khong co trong chu' for t in ten if t not in text]
    if kenh == "fb":
        t = ten[0] if ten else ""
        if f"{t} còn {_nghin(sv['gia_vnd'])}" not in text:
            loi.append("khong co cap 'ten game con N nghìn'")
    elif kenh == "ig":
        for g in sv.get("game") or []:
            t = ten_chu(g["ten_goc"])
            dung = _nghin(g["gia_vnd"])
            gap = re.findall(re.escape(t) + r" – (\d[\d.]*(?: nghìn|đ))", text)
            if not gap:
                loi.append(f'khong co cap "{t} – {dung}"')
            loi += [f'cap "{t} – {x}" sai gia (dung {dung})' for x in gap if x != dung]
    else:
        if len(text) > THREADS_KY_TU or len(text.encode("utf-8")) > THREADS_BYTE:
            loi.append(f"dai {len(text)} ky tu / {len(text.encode('utf-8'))} byte (> {THREADS_KY_TU} / {THREADS_BYTE})")
        if not dong[0].endswith("?"):
            loi.append("dong 1 khong phai cau hoi")
        if not dong[-1].endswith("?"):
            loi.append("khong ket bang cau hoi")
    return loi
