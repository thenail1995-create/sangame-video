#!/usr/bin/env python3
"""Thu giong ElevenLabs tren runner (B3) - thay ~/Cong-cu/elevenlabs/el.py khi chay may dung. Giu NGUYEN luat chong lang phi cua el.py:
  1. KHO: cung (loi, voice, model, on dinh, toc do) => dung lai file cu, KHONG goi lai. Khoa kho giong het el.py (sha256 20 ky tu dau) nen kho Mac va kho
     runner cung khoa. Tren runner kho = thu muc GIONG_KHO duoc actions/cache theo khoa nay (chay lai cung ngay: 0 credit).
  2. SO CAI qua cong sg-cong (bang sg_credit, RLS): giu_credit (tran thang, gio VN) -> tts -> xong_credit (credit that) / huy_credit / khong_ro_credit.
  3. Tran thang cua du an (mac dinh san-game 20000) + chua DU PHONG chung cua tai khoan (10000): vuot => tu choi.
  4. Loi dai > 400 ky tu ma chua tung thu bo cai dat nay bang cau ngan => tu choi (DA_THU_NGAN: Minh Dang / eleven_v3 / on dinh 0.0 da thu 08-10/10/2026).
Khoa: SUPABASE_ANON_THENAIL (anon The Nail, goi edge function doc-giong) + SG_CONG_KHOA (cong so). Mac: doc tu ~/.claude/tools/ neu env trong. KHONG in khoa.
  python3 cong-cu/giong.py giong --loi-file loi.txt --ra dau-vao/giong.mp3 [--du-an san-game] [--dang top5] [--voice ID] [--model M] [--on-dinh 0.0] [--toc-do 1.0]
  python3 cong-cu/giong.py khoa --loi-file loi.txt     # in khoa kho (de workflow dat key cache), khong goi mang
"""
import argparse,datetime,hashlib,json,os,pathlib,shutil,sys,time,urllib.error,urllib.request
ROOT=pathlib.Path(__file__).resolve().parent.parent; sys.path.insert(0,str(ROOT))
URL='https://qkpbokksubmqvinetdtv.supabase.co/functions/v1/doc-giong'
GIA={'eleven_v4':0.105,'eleven_v3':0.372}   # credit / ky tu, do that 09/10/2026 (goi Creator) - giong el.py
VOICE_MAC_DINH='e71pPu7iHH7VarkDhDNk'       # Minh Dang
DA_THU_NGAN={('e71pPu7iHH7VarkDhDNk','eleven_v3',0.0)}   # (voice, model, on dinh) da thu bang cau ngan, Hao nghe va chot 08-10/10/2026
TRAN_MAC_DINH={'san-game':20000}; DU_PHONG_MAC_DINH=10000
class Loi(SystemExit): pass
def _doc_khoa(env,tep):
    v=os.environ.get(env,'').strip()
    if v: return v
    p=pathlib.Path.home()/'.claude/tools'/tep
    return p.read_text().strip() if p.exists() else ''
def che(s,khoa=()):
    for k in khoa:
        if k and len(k)>=6: s=s.replace(k,'***')
    return s
def khoa_kho(loi,voice,model,on_dinh,toc_do,muoi=''):
    # y het el.py:44 khi muoi rong. muoi (vd 'lan2') = lan thu lai: bat buoc thu BAN MOI (eleven_v3 moi lan mot kieu doc; ban hong ma luu cache thi thu lai vo ich)
    return hashlib.sha256(json.dumps([loi,voice,model,on_dinh,toc_do]+([muoi] if muoi else [])).encode()).hexdigest()[:20]
def kho_dir():
    p=pathlib.Path(os.environ.get('GIONG_KHO') or (pathlib.Path.home()/'.cache/sangame-giong')); p.mkdir(parents=True,exist_ok=True); return p
def thang_vn(): return datetime.datetime.now(datetime.timezone(datetime.timedelta(hours=7))).strftime('%Y-%m')
def uoc_credit(n,model): return round(n*GIA.get(model,0.4),1)
class Eleven:
    def __init__(self,anon): self.anon=anon
    def goi(self,body,timeout=180):
        rq=urllib.request.Request(URL,data=json.dumps(body).encode(),headers={'Authorization':'Bearer '+self.anon,'content-type':'application/json'})
        with urllib.request.urlopen(rq,timeout=timeout) as r: return json.loads(r.read())
def lay_mp3(url,dich,lan=3):
    loi=None
    for i in range(lan):
        try:
            with urllib.request.urlopen(url,timeout=120) as r: b=r.read()
            if len(b)<5000: raise ValueError(f'mp3 qua nho ({len(b)} byte)')
            pathlib.Path(dich).write_bytes(b); return len(b)
        except Exception as e: loi=e; time.sleep(3*(i+1))
    raise loi
def cmd_khoa(a):
    loi=pathlib.Path(a.loi_file).read_text(encoding='utf-8').strip()
    print(khoa_kho(loi,a.voice,a.model,a.on_dinh,a.toc_do,a.muoi))
def cmd_giong(a,cong=None,el=None,ngu=time.sleep):
    loi=pathlib.Path(a.loi_file).read_text(encoding='utf-8').strip() if a.loi_file else a.loi
    khoa=khoa_kho(loi,a.voice,a.model,a.on_dinh,a.toc_do,a.muoi); f=kho_dir()/f'{khoa}.mp3'; n=len(loi); uoc=uoc_credit(n,a.model)
    ra=pathlib.Path(a.ra); ra.parent.mkdir(parents=True,exist_ok=True)
    if f.exists() and f.stat().st_size>=5000:
        shutil.copy(f,ra); print(f'KHO: dung lai {khoa}.mp3, 0 credit'); return 'kho',0
    if n>400 and (a.voice,a.model,a.on_dinh) not in DA_THU_NGAN and not a.cho_vuot:
        raise Loi('TU CHOI: chua thu giong/model/cai dat nay bang cau ngan (<=400 ky tu). Thu 1 cau truoc, nghe ung roi moi thu ca bai.')
    anon=_doc_khoa('SUPABASE_ANON_THENAIL','thenail-supabase-anon'); khoa_cong=_doc_khoa('SG_CONG_KHOA','sangame-sg-cong-khoa')
    if not anon or not khoa_cong: raise Loi('LOI: thieu SUPABASE_ANON_THENAIL hoac SG_CONG_KHOA')
    bi_mat=(anon,khoa_cong)
    if cong is None:
        from dang.so import Cong; cong=Cong(khoa_cong)
    el=el or Eleven(anon)
    # 1) giu cho (nguyen tu trong DB: tong thang + giu cho <= tran)
    tran=a.tran if a.tran is not None else TRAN_MAC_DINH.get(a.du_an)
    if tran is None: raise Loi(f'TU CHOI: du an {a.du_an} chua co tran thang (--tran)')
    g=cong.goi('giu_credit',lap_lai=False,thang=thang_vn(),credit_uoc=uoc,tran=tran,dang=a.dang,ky_tu=n,khoa_kho=khoa)
    if g.get('vuot_tran') or not g.get('id'): raise Loi(f'TU CHOI: {a.du_an} vuot tran {tran} credit thang {thang_vn()} (lan nay ~{uoc}).')
    idc=g['id']
    try:
        tk0=el.goi({'action':'goi'},30); con=tk0['gioi_han']-tk0['da_dung']
        if con-uoc<a.du_phong:
            cong.goi('huy_credit',id=idc,ghi_chu='du phong tai khoan'); raise Loi(f'TU CHOI: tai khoan con {con} credit, phai chua du phong {a.du_phong}.')
    except Loi: raise
    except Exception as e:   # chua goi tts => khong mat credit
        cong.goi('huy_credit',id=idc,ghi_chu=che(f'loi doc tai khoan: {e}',bi_mat)[:200]); raise Loi('LOI doc tai khoan ElevenLabs: '+che(str(e),bi_mat)[:200])
    # 2) tts: loi ro rang (4xx / ket qua khong co nghe_thu) => huy; mat ket noi / 5xx / het gio => khong_ro (co the da tru credit)
    try: d=el.goi({'action':'tts','voice_id':a.voice,'model_id':a.model,'stability':a.on_dinh,'speed':a.toc_do,'text':loi})
    except urllib.error.HTTPError as e:
        (cong.goi('huy_credit',id=idc,ghi_chu=f'HTTP {e.code}') if e.code<500 else cong.goi('khong_ro_credit',id=idc,ghi_chu=f'HTTP {e.code}'))
        raise Loi(f'LOI tts HTTP {e.code} ({"huy" if e.code<500 else "khong ro"} giu cho credit)')
    except Exception as e:
        cong.goi('khong_ro_credit',id=idc,ghi_chu=che(str(e),bi_mat)[:200]); raise Loi('LOI tts khong ro ket qua (da danh dau khong_ro): '+che(str(e),bi_mat)[:200])
    if not d.get('nghe_thu'):
        cong.goi('huy_credit',id=idc,ghi_chu=che(json.dumps(d,ensure_ascii=False),bi_mat)[:200]); raise Loi('LOI ElevenLabs: '+che(json.dumps(d,ensure_ascii=False),bi_mat)[:300])
    # 3) credit that = chenh lech da_dung truoc/sau (neu hop ly), khong thi uoc theo he so
    try:
        tk1=el.goi({'action':'goi'},30); chenh=tk1['da_dung']-tk0['da_dung']
        that=float(chenh) if 0<chenh<=uoc*3 else uoc
    except Exception: that=uoc
    cong.goi('xong_credit',id=idc,credit_that=that)   # credit da tru du tai file co ve duoc hay khong
    try: lay_mp3(d['nghe_thu'],f)
    except Exception as e: raise Loi('LOI tai mp3 (credit DA TRU, da ghi so): '+che(str(e),bi_mat)[:200])
    shutil.copy(f,ra); print(f'GOI: {n} ky tu, {that} credit that (uoc {uoc}) -> {ra}  [khoa kho {khoa}]'); return 'goi',that
def main(argv=None):
    ap=argparse.ArgumentParser(); sp=ap.add_subparsers(dest='lenh',required=True)
    for ten in ('giong','khoa'):
        p=sp.add_parser(ten); p.add_argument('--loi'); p.add_argument('--loi-file'); p.add_argument('--voice',default=VOICE_MAC_DINH)
        p.add_argument('--model',default='eleven_v3'); p.add_argument('--on-dinh',type=float,default=0.0); p.add_argument('--toc-do',type=float,default=1.0); p.add_argument('--muoi',default=os.environ.get('GIONG_MUOI',''))
        if ten=='giong':
            p.add_argument('--ra',required=True); p.add_argument('--du-an',default='san-game'); p.add_argument('--dang',default='top5')
            p.add_argument('--tran',type=int,default=None); p.add_argument('--du-phong',type=int,default=DU_PHONG_MAC_DINH); p.add_argument('--cho-vuot',action='store_true')
    a=ap.parse_args(argv)
    if a.lenh=='khoa': return cmd_khoa(a)
    cmd_giong(a)
if __name__=='__main__': main()
