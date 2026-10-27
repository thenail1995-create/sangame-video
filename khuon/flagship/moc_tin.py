# Moc thoi su (3.3) cho Flagship: bang tu khoa CO DINH, khong doan. Chi stdlib.
#   xet_tieu_de(tieu_de, khoa_game_tokens) -> dict(cau,chu) | None   (tieu de PHAI bat dau bang ten dong game, roi moi xet tu khoa)
#   chon_moc(ten_goc, nong_mau, thap_nhat) -> dict(loai tin|thap_nhat|khong, cau, chu, nguon, goc)
import pathlib,re,sys
T=pathlib.Path(__file__).resolve().parent
sys.path.insert(0,str(T)); sys.path.insert(0,str(T.parent.parent/'cong-cu'))
import doc_tien as dt
import da_noi_bat as DNB
_TOKEN_BO=DNB._BO|DNB._LA_MA
RE_FREE=re.compile(r'\bfree\s+update\b',re.I)
RE_ANNIV=re.compile(r'\b(\d+)(?:st|nd|rd|th)\s+anniversary\b',re.I)
RE_DLC=re.compile(r'\b(dlc|expansion)\b',re.I); RE_TRAILER=re.compile(r'\b(trailer|announce\w*)\b',re.I)
RE_UPDATE=re.compile(r'\bupdate\s+(\d+(?:\.\d+)?)\b',re.I)
# Sau ten game, phan con lai cua tieu de chi duoc la tu khoa tin (khong phai ten phan/spin-off khac: 'Tomb Raider: Legacy of Atlantis' != 'Tomb Raider')
RE_TIEP=re.compile(r'^(?:(?:free|official|new|\d+(?:st|nd|rd|th))\s+)*(?:update|dlc|expansion|anniversary|trailer|announce)',re.I)
def _tokens(s):
    return re.sub(r'[^\w\s]',' ',re.sub(r'[®™©]','',s or '').lower().replace('’',"'")).split()
def bat_dau_bang_game(tieu_de,ten_goc):
    """True neu tieu de bat dau bang ten dong game va phan con lai (sau so phan/ban edition) chi la tu khoa tin."""
    g=DNB.dong_game(ten_goc).split(); t=_tokens(tieu_de)
    if not g or t[:len(g)]!=g: return False
    r=t[len(g):]
    while r and (r[0].isdigit() or r[0] in _TOKEN_BO): r=r[1:]
    return not r or bool(RE_TIEP.match(' '.join(r)))
def xet_tieu_de(tieu_de,ten_goc):
    if not bat_dau_bang_game(tieu_de,ten_goc): return None
    free=RE_FREE.search(tieu_de); an=RE_ANNIV.search(tieu_de); up=RE_UPDATE.search(tieu_de)
    if free:
        if up: return dict(cau=f'Mà game vừa có bản cập nhật {dt.doc_phien_ban(up.group(1))} miễn phí.',chu=f'UPDATE {up.group(1)} MIỄN PHÍ')
        if an:
            n=int(an.group(1)); return dict(cau=f'Mà game vừa có bản cập nhật miễn phí mừng {dt.so_chu(n)} năm.',chu=f'CẬP NHẬT MIỄN PHÍ MỪNG {n} NĂM')
        return dict(cau='Mà game vừa có bản cập nhật miễn phí.',chu='CẬP NHẬT MIỄN PHÍ')
    if RE_DLC.search(tieu_de) and RE_TRAILER.search(tieu_de):
        return dict(cau='Mà game vừa ra trailer bản mở rộng.',chu='BẢN MỞ RỘNG MỚI')
    if up: return dict(cau=f'Mà game vừa có bản cập nhật {dt.doc_phien_ban(up.group(1))}.',chu=f'UPDATE {up.group(1)}')
    return None
def chon_moc(ten_goc,nong_mau,thap_nhat):
    for m in nong_mau or []:
        r=xet_tieu_de(m.get('tieu_de') or '',ten_goc)
        if r: return dict(loai='tin',cau=r['cau'],chu=r['chu'],nguon=m.get('url') or '',goc=m.get('tieu_de'))
    tn=thap_nhat or {}
    if tn.get('la_thap_nhat') and int(tn.get('so_ngay') or 0)>=7:
        n=int(tn['so_ngay']); return dict(loai='thap_nhat',cau=f'Đây là giá thấp nhất trong {dt.so_chu(n)} ngày Săn Game theo dõi.',chu=f'THẤP NHẤT {n} NGÀY',nguon='',goc='')
    return dict(loai='khong',cau='',chu='',nguon='',goc='')
