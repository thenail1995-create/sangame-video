#!/usr/bin/env python3
"""B5': du lieu gia 6 vung cua repo rieng tu da CO NGAY HOM NAY (gio VN) chua? Neu roi -> lay data_sha = commit moi nhat cua checkout.
  python3 cong-cu/kiem_do_moi.py <thu-muc-checkout-kenh-game-du-lieu> [--ngay YYYY-MM-DD] [--lan 1|2] [--github-output]
Dieu kien 'moi' (ca bon phai dung):
  - du-lieu/bang-gia.json  cap_nhat >= ngay, so_mon_giu_lai co DU 6 vung (SG HK IN ID US TH) moi vung > 0 mon
  - du-lieu/trang-game.json cap_nhat >= ngay ;  du-lieu/gia-the.json ngay >= ngay
  - du-lieu/giam-gia-en-{US,HK,SG,ID,TH,IN}.json co so_mon > 0 (du 6 vung, ke ca An Do)
Chua moi: in 'chua co du lieu' va THOAT 0 (workflow xanh). --lan 2 ma van chua moi: ntfy loi (NTFY_BAO_LOI) roi van thoat 0 (bo khung).
Dau ra --github-output: moi=1|0, data_sha=<sha>, ly_do=<chuoi 1 dong>."""
import argparse,datetime,json,os,pathlib,subprocess,sys
ROOT=pathlib.Path(__file__).resolve().parent.parent
VUNG=['SG','HK','IN','ID','US','TH']
def hom_nay_vn(): return datetime.datetime.now(datetime.timezone(datetime.timedelta(hours=7))).date().isoformat()
def doc(p):
    try:
        with open(p,encoding='utf-8') as f: return json.load(f)
    except Exception: return None
def kiem(repo,ngay):
    """-> (moi: bool, ly_do: list[str])"""
    repo=pathlib.Path(repo); dl=repo/'du-lieu'; ly=[]
    bg=doc(dl/'bang-gia.json'); tg=doc(dl/'trang-game.json'); gt=doc(dl/'gia-the.json')
    for ten,v in (('bang-gia.json cap_nhat',(bg or {}).get('cap_nhat')),('trang-game.json cap_nhat',(tg or {}).get('cap_nhat')),('gia-the.json ngay',(gt or {}).get('ngay'))):
        if not v or str(v)[:10]<ngay: ly.append(f'{ten} = {v or "thieu"} (can >= {ngay})')
    gi=(bg or {}).get('so_mon_giu_lai') or {}
    for v in VUNG:
        if not (isinstance(gi.get(v),int) and gi[v]>0): ly.append(f'bang-gia so_mon_giu_lai[{v}] = {gi.get(v)}')
        g=doc(dl/f'giam-gia-en-{v}.json')
        if not g or not (g.get('so_mon') or 0)>0: ly.append(f'giam-gia-en-{v}.json rong/thieu')
    return (not ly),ly
def sha_moi_nhat(repo):
    return subprocess.run(['git','-C',str(repo),'rev-parse','HEAD'],capture_output=True,text=True,check=True).stdout.strip()
def main(argv=None):
    ap=argparse.ArgumentParser(); ap.add_argument('repo'); ap.add_argument('--ngay',default=None); ap.add_argument('--lan',type=int,default=1); ap.add_argument('--github-output',action='store_true')
    a=ap.parse_args(argv); ngay=a.ngay or hom_nay_vn()
    moi,ly=kiem(a.repo,ngay)
    sha=sha_moi_nhat(a.repo) if moi else ''
    print(f'du lieu MOI ({ngay}), data_sha={sha}' if moi else 'chua co du lieu moi: '+'; '.join(ly))
    if not moi and a.lan>=2:
        sys.path.insert(0,str(ROOT))
        try:
            from dang import ntfy; ntfy.loi('Top 5: khong co du lieu moi lan 2',f'Ngay {ngay}: du lieu gia chua ve sau lan thu 2 -> bo khung Top 5 hom nay. '+'; '.join(ly)[:600])
        except Exception as e: print('khong gui duoc ntfy:',type(e).__name__)
    if a.github_output and os.environ.get('GITHUB_OUTPUT'):
        with open(os.environ['GITHUB_OUTPUT'],'a') as f: f.write(f'moi={1 if moi else 0}\ndata_sha={sha}\nly_do={"; ".join(ly)[:300]}\n')
    return 0
if __name__=='__main__': sys.exit(main())
