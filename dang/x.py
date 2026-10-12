"""Dang X (@sangamecomvn) qua Buffer (GraphQL https://api.buffer.com). Buffer Free: 100 lenh/15 phut, 250/ngay.
Quy uoc loi (giong zernio.py):
  LoiDang(khong_ro=False) = CHAC CHAN chua co bai tren X.
  LoiDang(khong_ro=True)  = co the da dang / khong biet -> KHONG dang lai.
Buffer khong co Idempotency-Key -> chay.py giu quyen bang cong.giu_dang TRUOC moi goi mang; o day createPost chi goi DUNG MOT LAN.
Khoa Buffer duoc dang ky bi mat (chung.dang_ky_bi_mat) -> khong vao log / ngoai le.
"""
import json
import os
import re
import unicodedata

from . import chung, http, manifest, site

URL = "https://api.buffer.com"
KENH_MAC_DINH = "6acca131778b240e2fe466f3"   # kenh X sangamecomvn trong Buffer
TRAN_X = 275                                    # X cho 280; chua 5 ky tu phong khi dem lech
URL_X = 23                                      # X tinh moi URL = 23 ky tu
NHIP_HOI = 15
SO_LAN_HOI = 40                                 # 40 x 15 s = 10 phut
DANG_CHO = ("sending", "scheduled", "draft", "needs_approval")
# URL co giao thuc, hoac ten mien tran (vd t.co, sangame.com.vn) - X tinh ca hai = 23 (GPT soi 12/10 P2)
_URL = re.compile(r"https?://\S+|\b(?:[a-z0-9-]+\.)+[a-z]{2,24}(?:/\S*)?", re.I)


def co_khoa():
    return bool(os.environ.get("BUFFER_KHOA", "").strip())


def _kenh():
    return os.environ.get("BUFFER_X_KENH", "").strip() or KENH_MAC_DINH


def _chua(ly_do):
    return chung.LoiDang(f"Buffer: {ly_do} (chua tao bai)")


def _khong_ro(ly_do):
    return chung.LoiDang(f"Buffer: {ly_do} - khong ro da dang chua", khong_ro=True)


# ---------------------------------------------------------------- text X
def _trong_so(c):
    n = ord(c)
    if n <= 0x10FF or 0x2000 <= n <= 0x200D or 0x2010 <= n <= 0x201F or 0x2032 <= n <= 0x2037:
        return 1
    return 2


def do_dai_x(s):
    """Do dai theo X: moi URL = 23; ky tu codepoint <= U+10FF (va vai khoang dau cau) = 1, con lai (tieng Viet dung san U+1EA0..) = 2."""
    s = unicodedata.normalize("NFC", s or "")
    tong, vi_tri = 0, 0
    for m in _URL.finditer(s):
        tong += sum(_trong_so(c) for c in s[vi_tri:m.start()]) + URL_X
        vi_tri = m.end()
    return tong + sum(_trong_so(c) for c in s[vi_tri:])


def _cau_han(mo_ta):
    """Cau dau tien bat dau 'Het giam' trong mo_ta (nguyen cau), khong co -> ''."""
    for cau in re.split(r"(?<=[.!?])\s+", mo_ta or ""):
        cau = cau.strip()
        if cau.startswith("Hết giảm"):
            return cau
    return ""


def _link_game(ld):
    m = re.search(r"https://sangame\.com\.vn/\S*", ld.get("mo_ta") or "")
    if m:
        return m.group(0).rstrip(".,;:!?)")
    return ld.get("link") or ""


def _ghep(tieu_de, han, link, tags):
    dong = [p for p in (tieu_de, han, link, " ".join(tags)) if p]
    return "\n".join(dong)


def text_x(nc):
    """tieu_de + cau han + link game + hashtag, <= 280 theo do_dai_x. Thieu cho: bo cau han -> bot hashtag (tu cuoi) -> cat tieu de kem '…'."""
    ld = nc.loi_dang
    tieu_de, han, link = (ld.get("tieu_de") or "").strip(), _cau_han(ld.get("mo_ta")), _link_game(ld)
    tags = nc.hashtags("x")   # <= 2: tag game + #PlayStation
    # thu tu bo: cau han truoc, roi hashtag (tu cuoi), cuoi cung cat tieu de
    ung_vien = [(han, len(tags))] + [("", n) for n in range(len(tags), -1, -1)]
    for h, n in ung_vien:
        s = _ghep(tieu_de, h, link, tags[:n])
        if do_dai_x(s) <= TRAN_X:
            return s
    # van qua dai: cat tieu de
    con = TRAN_X - do_dai_x(_ghep("", "", link, []) + "\n")
    cat = tieu_de
    while cat and do_dai_x(cat + "…") > con:
        cat = cat[:-1]
    return _ghep(cat.rstrip() + "…", "", link, [])


# ---------------------------------------------------------------- video
def url_video(nc):
    """URL Pages cua ban reels (kiem 200 + video/mp4); hong thi URL Release GitHub."""
    u = nc.url_video
    if not u:
        goc = os.environ.get("PAGES_URL") or "https://{}.github.io/{}".format(*manifest.REPO.split("/"))
        u = site.url_cong_khai(goc, nc.ngay, nc.dang, nc.man)[0]
    try:
        site.kiem_url(u, "video/mp4", lan=3, nghi=5)
        return u
    except chung.LoiDang as e:
        chung.log(f"x: URL Pages khong dat, dung URL Release: {e}")
        return f"https://github.com/{manifest.REPO}/releases/download/{manifest.tag(nc.ngay, nc.dang, nc.che_do)}/{nc.man['ban']['reels']['video']}"


# ---------------------------------------------------------------- Buffer
def _goi(khoa, query, timeout):
    return http.gui("POST", URL, headers={"Authorization": "Bearer " + khoa}, json_body={"query": query}, timeout=timeout)


def tao_bai(khoa, nc, text, video):
    """createPost DUNG MOT LAN. -> id bai. Loi mang/timeout/5xx = khong_ro; 4xx/errors/MutationError = chua tao."""
    q = ('mutation { createPost(input: {text: %s, channelId: %s, schedulingType: automatic, mode: shareNow, '
         'assets: [{video: {url: %s}}]}) { __typename ... on PostActionSuccess { post { id status } } '
         '... on MutationError { message } } }') % (json.dumps(text, ensure_ascii=False), json.dumps(_kenh()), json.dumps(video))
    try:
        r = _goi(khoa, q, 60)
    except http.LoiMang as e:
        raise _khong_ro(f"createPost loi mang ({e})") from None
    if r.status >= 500:
        raise _khong_ro(f"createPost HTTP {r.status}")
    j = r.json()
    if 400 <= r.status < 500:
        raise _chua(f"createPost HTTP {r.status} {chung.cat(j, 150)}")
    if r.status != 200:
        raise _khong_ro(f"createPost HTTP {r.status} la")
    kq = ((j.get("data") or {}).get("createPost") or {}) if isinstance(j, dict) else {}
    post = kq.get("post") if isinstance(kq.get("post"), dict) else {}
    if isinstance(j, dict) and j.get("errors") and not post.get("id"):
        # GraphQL: loi truoc khi thuc thi (xac thuc/cu phap) -> KHONG co khoa "data" -> chac chan chua tao.
        # Co "data" (ke ca null) = loi trong luc thuc thi -> co the da tao (GPT soi 12/10 P1) -> khong_ro.
        if "data" not in j:
            raise _chua(f"createPost errors {chung.cat(j['errors'], 200)}")
        raise _khong_ro(f"createPost errors luc thuc thi {chung.cat(j['errors'], 200)}")
    if post.get("id"):   # co id thi di tiep ke ca kem errors[] (Buffer: mutation thanh cong van co the kem errors)
        if str(post.get("status")) == "error":
            raise _chua("bai tao xong nhung status error")
        return str(post["id"])
    if kq.get("message"):
        raise _chua(f"MutationError {chung.cat(kq['message'], 200)}")
    raise _khong_ro("createPost tra ket qua la, khong co id bai")


def hoi_den_xong(khoa, post_id):
    """Hoi post(input:{id}) moi 15 s, toi da 10 phut."""
    q = 'query { post(input: {id: %s}) { id status externalLink error { message } } }' % json.dumps(post_id)
    for _ in range(SO_LAN_HOI):
        chung.ngu(NHIP_HOI)
        try:
            r = _goi(khoa, q, 30)
        except http.LoiMang:
            continue
        j = r.json()
        if r.status != 200 or not isinstance(j, dict) or j.get("errors"):
            continue
        p = (j.get("data") or {}).get("post") or {}
        st = str(p.get("status") or "").lower()
        if st == "sent":
            return {"id_bai": post_id, "link": p.get("externalLink"), "kieu": "buffer"}
        if st == "error":
            raise chung.LoiDang(f"Buffer: bai loi, chua len X ({chung.cat((p.get('error') or {}).get('message') or '', 200)})")
        # sending / scheduled / khac: cho tiep
    raise _khong_ro(f"het 10 phut cho bai {post_id} van chua sent")


def cong_khai(nc):
    """Dang cong khai len X qua Buffer. Tra {"id_bai","link","kieu"}. Xem quy uoc loi o dau file."""
    khoa = os.environ.get("BUFFER_KHOA", "").strip()
    if not khoa:
        raise _chua("thieu BUFFER_KHOA")
    chung.dang_ky_bi_mat(khoa)
    text = text_x(nc)
    video = url_video(nc)
    post_id = tao_bai(khoa, nc, text, video)
    # Tu day bai CO THE da len X: moi loi khac 'error' ro rang la khong_ro.
    return hoi_den_xong(khoa, post_id)
