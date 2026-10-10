# Game da len Top 5 trong N ngay gan nhat (B1: khong lap lai). Nguon: manifest.json cua cac Release `v-<ngay>-top5` cua repo nay
# (kiem_lai[].ten). So sg_dang (sg-cong doc_dang) khong luu ten game nen khong dung duoc cho viec nay.
#   da_len(ngay, so_ngay=3) -> (set khoa dong game, ghi_chu)   ; khoa = ten_dong_game(ten)
# Thu tu: env TOP5_LICH_SU (duong dan json {"ngay":[ten,...]}, de thu tren Mac) > GitHub API (repo = env GITHUB_REPOSITORY).
# Loi mang: thu 3 lan; van loi -> tra tap RONG kem ghi chu 'CANH BAO' (lap game nhe hon bo ca khung).
import datetime,json,os,re,time,urllib.request
def ten_dong_game(ten):   # khoa DONG game (Mafia = Mafia III): ten goc truoc ':', bo (R)(TM), bo so / so La Ma
    k=re.sub(r'[®™]','',ten).lower().split(':')[0]
    return re.sub(r'\s+',' ',re.sub(r'\b(ii|iii|iv|v|vi|\d+)\b','',k)).strip()
def _get(url,tok=None,json_out=True):
    h={'User-Agent':'sangame-video','Accept':'application/vnd.github+json'}
    if tok: h['Authorization']='Bearer '+tok
    for lan in range(3):
        try:
            b=urllib.request.urlopen(urllib.request.Request(url,headers=h),timeout=30).read()
            return json.loads(b) if json_out else b
        except Exception as e:
            err=e; time.sleep(2*(lan+1))
    raise err
def da_len(ngay,so_ngay=3):
    d0=datetime.date.fromisoformat(ngay); tu=d0-datetime.timedelta(days=so_ngay)
    f=os.environ.get('TOP5_LICH_SU')
    if f:
        with open(f,encoding='utf-8') as fh: j=json.load(fh)
        ten=[t for n,ds in j.items() if tu<=datetime.date.fromisoformat(n)<d0 for t in ds]
        return {ten_dong_game(t) for t in ten},f'tu {f}'
    repo=os.environ.get('GITHUB_REPOSITORY','thenail1995-create/sangame-video'); tok=os.environ.get('GH_TOKEN') or os.environ.get('GITHUB_TOKEN')
    try:
        rels=_get(f'https://api.github.com/repos/{repo}/releases?per_page=30',tok)
        ten=[]; dem=0
        for r in rels:
            m=re.fullmatch(r'v-(\d{4}-\d{2}-\d{2})-top5',r.get('tag_name',''))
            if not m or r.get('draft'): continue
            if not (tu<=datetime.date.fromisoformat(m.group(1))<d0): continue
            a=next((x for x in r.get('assets',[]) if x['name']=='manifest.json'),None)
            if not a: continue
            mf=_get(a['browser_download_url'],None)
            ten+= [g['ten'] for g in mf.get('kiem_lai',[]) if g.get('ten')]; dem+=1
        return {ten_dong_game(t) for t in ten},f'{dem} Release top5 trong {so_ngay} ngay truoc {ngay}: {len(ten)} game'
    except Exception as e:
        return set(),f'CANH BAO: khong doc duoc lich su Release ({type(e).__name__}: {str(e)[:120]}) - khong loc game da len'
