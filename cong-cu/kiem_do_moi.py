#!/usr/bin/env python3
"""B5': du lieu gia 6 vung cua repo rieng tu da CO NGAY HOM NAY (gio VN) chua? Neu roi -> lay data_sha = commit moi nhat cua checkout.
  python3 cong-cu/kiem_do_moi.py <thu-muc-checkout-kenh-game-du-lieu> [--ngay YYYY-MM-DD] [--dang top5|keo-thom|tin-nhanh] [--lan-cuoi] [--github-output]
Dieu kien 'moi' (ca bon phai dung):
  - du-lieu/bang-gia.json  cap_nhat >= ngay, so_mon_giu_lai co DU 6 vung (SG HK IN ID US TH) moi vung > 0 mon
  - du-lieu/trang-game.json cap_nhat >= ngay ;  du-lieu/gia-the.json ngay >= ngay
  - du-lieu/giam-gia-en-{US,HK,SG,ID,TH,IN}.json co so_mon > 0 VA truong cap_nhat (moc rieng cua feed, doi sang gio VN) >= ngay; thieu truong = cu
Chua moi: in 'chua co du lieu' va THOAT 0 (workflow xanh) neu con luot sau. --lan-cuoi (khong con luot sau: top5 lan 2; keo-thom, tin-nhanh luon) ma van chua moi: ntfy loi (NTFY_BAO_LOI) roi thoat 0 (bo khung); gui ntfy hong -> thoat 1.
Dau ra --github-output: moi=1|0, data_sha=<sha>, ly_do=<chuoi 1 dong>."""
import argparse,datetime,json,os,pathlib,re,subprocess,sys
ROOT=pathlib.Path(__file__).resolve().parent.parent
VUNG=['SG','HK','IN','ID','US','TH']
VN=datetime.timezone(datetime.timedelta(hours=7),'Asia/Ho_Chi_Minh')   # VN khong co gio mua he => +07 co dinh tuong duong Asia/Ho_Chi_Minh
TRUONG_MOC_FEED='cap_nhat'   # moc thoi gian rieng trong moi giam-gia-en-<vung>.json (ISO, co Z/offset hoac chi ngay)
TEN_DANG={'top5':'Top 5','keo-thom':'Keo thom','tin-nhanh':'Tin nhanh'}
def hom_nay_vn(): return datetime.datetime.now(VN).date().isoformat()
def ngay_vn(v):
    """Moc thoi gian (chuoi) -> ngay VN (date) hoac None. Chi ngay (YYYY-MM-DD) = ngay VN; co gio: doi sang Asia/Ho_Chi_Minh roi lay ngay (khong cat chuoi)."""
    if not isinstance(v,str) or not v.strip(): return None
    v=v.strip()
    try:
        if re.fullmatch(r'\d{4}-\d{2}-\d{2}',v): return datetime.date.fromisoformat(v)
        t=datetime.datetime.fromisoformat(v)
        if t.tzinfo is None: return t.date()   # khong mui gio: coi la gio VN
        return t.astimezone(VN).date()
    except ValueError: return None
def du_ngay(v,ngay):
    d=ngay_vn(v); return d is not None and d>=datetime.date.fromisoformat(ngay)
def doc(p):
    try:
        with open(p,encoding='utf-8') as f: return json.load(f)
    except Exception: return None
def kiem(repo,ngay):
    """-> (moi: bool, ly_do: list[str])"""
    repo=pathlib.Path(repo); dl=repo/'du-lieu'; ly=[]
    bg=doc(dl/'bang-gia.json'); tg=doc(dl/'trang-game.json'); gt=doc(dl/'gia-the.json')
    for ten,v in (('bang-gia.json cap_nhat',(bg or {}).get('cap_nhat')),('trang-game.json cap_nhat',(tg or {}).get('cap_nhat')),('gia-the.json ngay',(gt or {}).get('ngay'))):
        if not du_ngay(v,ngay): ly.append(f'{ten} = {v or "thieu"} (can >= {ngay})')
    gi=(bg or {}).get('so_mon_giu_lai') or {}
    for v in VUNG:
        if not (isinstance(gi.get(v),int) and gi[v]>0): ly.append(f'bang-gia so_mon_giu_lai[{v}] = {gi.get(v)}')
        g=doc(dl/f'giam-gia-en-{v}.json')
        if not g or not (g.get('so_mon') or 0)>0: ly.append(f'giam-gia-en-{v}.json rong/thieu'); continue
        mc=g.get(TRUONG_MOC_FEED)   # moc RIENG cua tung feed; thieu truong = coi la cu
        if not du_ngay(mc,ngay): ly.append(f'giam-gia-en-{v}.json {TRUONG_MOC_FEED} = {mc or "thieu"} (can >= {ngay})')
    return (not ly),ly
def sha_moi_nhat(repo):
    return subprocess.run(['git','-C',str(repo),'rev-parse','HEAD'],capture_output=True,text=True,check=True).stdout.strip()
def main(argv=None):
    ap=argparse.ArgumentParser(); ap.add_argument('repo'); ap.add_argument('--ngay',default=None); ap.add_argument('--dang',default='top5',choices=sorted(TEN_DANG)); ap.add_argument('--lan-cuoi',action='store_true'); ap.add_argument('--github-output',action='store_true')
    ap.add_argument('--bo-qua-do-moi',action='store_true',help='CHI de thu (che_do=thu): coi du lieu hien co la moi, in canh bao')
    a=ap.parse_args(argv); ngay=a.ngay or hom_nay_vn()
    moi,ly=kiem(a.repo,ngay)
    if a.bo_qua_do_moi and not moi:
        print('CANH BAO: --bo-qua-do-moi - dung du lieu CU de thu (che do thu). Ly do bi bo qua: '+'; '.join(ly)); moi,ly=True,[]
    sha=sha_moi_nhat(a.repo) if moi else ''
    print(f'du lieu MOI ({ngay}), data_sha={sha}' if moi else 'chua co du lieu moi: '+'; '.join(ly))
    if a.github_output and os.environ.get('GITHUB_OUTPUT'):
        with open(os.environ['GITHUB_OUTPUT'],'a') as f: f.write(f'moi={1 if moi else 0}\ndata_sha={sha}\nly_do={"; ".join(ly)[:300]}\n')
    if not moi and a.lan_cuoi:
        sys.path.insert(0,str(ROOT)); ten=TEN_DANG[a.dang]
        try:
            from dang import ntfy; ok=ntfy.loi(f'{ten}: khong co du lieu moi (luot cuoi)',f'Ngay {ngay}: du lieu gia chua ve o luot cuoi -> bo khung {ten} hom nay. '+'; '.join(ly)[:600])
        except Exception as e: print('khong gui duoc ntfy:',type(e).__name__); ok=False
        if not ok: print('LOI: gui ntfy bao bo khung that bai'); return 1
    return 0
if __name__=='__main__': sys.exit(main())
