#!/usr/bin/env python3
"""Thu giong ElevenLabs tren runner (B3) - thay ~/Cong-cu/elevenlabs/el.py khi chay may dung. Giu NGUYEN luat chong lang phi cua el.py:
  1. KHO: cung (loi, voice, model, on dinh, toc do) => dung lai file cu, KHONG goi lai. Khoa kho giong het el.py (sha256 20 ky tu dau) nen kho Mac va kho
     runner cung khoa. Tren runner KHONG con actions/cache (repo cong khai): kho rieng nam o cong (tim_credit_khoa tra link ky 1 h).
  2. SO CAI qua cong sg-cong (bang sg_credit, RLS): tim_credit_khoa (kho rieng) -> giu_credit (n x 1.0, tran thang gio VN) -> tts -> ghi_tep_credit -> xong_credit / huy_credit / khong_ro_credit.
  3. Tran thang cua du an (mac dinh san-game 200000 tu 30/10, Hao bo gioi han 22/10) + chua DU PHONG chung cua tai khoan (10000): vuot => tu choi.
  4. Loi dai > 400 ky tu ma chua tung thu bo cai dat nay bang cau ngan => tu choi (DA_THU_NGAN: Minh Dang / eleven_v3 / on dinh 0.0 da thu 08-10/10/2026).
  5. GIOI HAN: kiem du phong tai khoan (con - giu >= du phong) KHONG nguyen tu voi luot dung ElevenLabs ngoai cong (The Nail) va giua cac dang; chi giam
     rui ro nho lich 3 dang khong chong gio (Tin nhanh 21:00, Top 5 ~10:30-12:00, Keo thom truoc 20:00). Tran thang cua du an thi nguyen tu trong DB.
  6. Kho rieng tra ve 'dong' (da co tep) => CHI phuc hoi, loi => DUNG (khong thu moi). 'chua_ro' (giu/khong_ro chua co tep) => DUNG cho den khi doi soat. Cong hong => DUNG.
  7. DU PHONG GIONG MAY (28/10/2026, Hao chot "het han muc chuyen qua may doc"): CHI 3 cho tu choi vi han muc - vuot tran thang (vuot_tran la True), du phong tai khoan,
     ElevenLabs tra 'tts 4xx: quota_exceeded' - sau khi huy_credit nhu cu thi doc bang VieNeu "Adam bua" (cong-cu/giong_may.py, 0 credit). Loi khac VAN DUNG nhu cu.
     Tat: --khong-may hoac SG_GIONG_MAY=0. Moi lan thanh cong ghi giong-nguon.json canh tep giong (nguon elevenlabs|may).
Khoa: SUPABASE_ANON_THENAIL (anon The Nail, goi edge function doc-giong) + SG_CONG_KHOA (cong so). Mac: doc tu ~/.claude/tools/ neu env trong. KHONG in khoa.
  python3 cong-cu/giong.py giong --loi-file loi.txt --ra dau-vao/giong.mp3 [--du-an san-game] [--dang top5] [--voice ID] [--model M] [--on-dinh 0.0] [--toc-do 1.0]
  python3 cong-cu/giong.py khoa --loi-file loi.txt     # in khoa kho (de workflow dat key cache), khong goi mang
"""
import argparse,datetime,hashlib,json,os,pathlib,re,shutil,sys,time,urllib.error,urllib.request
ROOT=pathlib.Path(__file__).resolve().parent.parent; sys.path.insert(0,str(ROOT)); sys.path.insert(0,str(pathlib.Path(__file__).resolve().parent))
import giong_may   # DU PHONG giong may (VieNeu); chi goi khi bi tu choi vi han muc
URL='https://qkpbokksubmqvinetdtv.supabase.co/functions/v1/doc-giong'
# tran credit/ky tu THEO CAP (voice, model): Minh Dang + eleven_v3 do that 244 credit/554 ky tu ~ 0,44 => 1,0 la tran an toan. Cap KHONG co trong bang => TU CHOI
# truoc khi giu credit (ElevenLabs co he so nhan credit cho mot so giong thu vien).
GIA_TOI_DA={('e71pPu7iHH7VarkDhDNk','eleven_v3'):1.0}
VOICE_MAC_DINH='e71pPu7iHH7VarkDhDNk'       # Minh Dang
DA_THU_NGAN={('e71pPu7iHH7VarkDhDNk','eleven_v3',0.0)}   # (voice, model, on dinh) da thu bang cau ngan, Hao nghe va chot 08-10/10/2026
TRAN_MAC_DINH={'san-game':200000}; DU_PHONG_MAC_DINH=10000   # 30/10: Hao 22/10 'cu dung thoai mai, khong can gioi han' -> tran du an cao hon ca goi (121.075/thang); chan that la DU PHONG 10000 cua tai khoan. Tran 20000 cu lam 28-29/10 roi ve giong may du tai khoan con 61.420
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
class Eleven:
    def __init__(self,anon,khoa=''): self.anon=anon; self.khoa=khoa
    def goi(self,body,timeout=180):
        hd={'Authorization':'Bearer '+self.anon,'content-type':'application/json'}
        if self.khoa: hd['x-khoa']=self.khoa
        rq=urllib.request.Request(URL,data=json.dumps(body).encode(),headers=hd)
        with urllib.request.urlopen(rq,timeout=timeout) as r: return json.loads(r.read())
def lay_mp3(url,dich,lan=3,ngu=time.sleep):
    loi=None
    for i in range(lan):
        try:
            with urllib.request.urlopen(url,timeout=120) as r: b=r.read()
            if len(b)<5000: raise ValueError(f'mp3 qua nho ({len(b)} byte)')
            pathlib.Path(dich).write_bytes(b); return len(b)
        except Exception as e:
            loi=e
            if i+1<lan: ngu(3*(i+1))
    raise loi
def cmd_khoa(a):
    loi=pathlib.Path(a.loi_file).read_text(encoding='utf-8').strip()
    print(khoa_kho(loi,a.voice,a.model,a.on_dinh,a.toc_do,a.muoi))
def _canh_bao(s): print('CANH BAO: '+s,file=sys.stderr)
def cmd_giong(a,cong=None,el=None,ngu=time.sleep,tai=None):
    ra=pathlib.Path(a.ra); ra.parent.mkdir(parents=True,exist_ok=True)
    (ra.parent/giong_may.NGUON_TEN).unlink(missing_ok=True)   # tep nguon cu khong duoc lan sang luot nay
    def ghi_ng(cach,khoa): giong_may.ghi_nguon(ra,nguon='elevenlabs',cach=cach,khoa=khoa,voice=a.voice,model=a.model)
    return _giong_el(a,cong,el,ngu,tai,ghi_ng)
def _giong_el(a,cong,el,ngu,tai,ghi_ng):
    ra=pathlib.Path(a.ra)
    tai=tai or (lambda u,d: lay_mp3(u,d,ngu=ngu))
    loi=pathlib.Path(a.loi_file).read_text(encoding='utf-8').strip() if a.loi_file else a.loi
    khoa=khoa_kho(loi,a.voice,a.model,a.on_dinh,a.toc_do,a.muoi); n=len(loi)
    def kho_cuc_bo(k):
        f=kho_dir()/f'{k}.mp3'
        if f.exists() and f.stat().st_size>=5000:
            shutil.copy(f,ra); print(f'KHO: dung lai {k}.mp3, 0 credit'); return True
    # 0) kho cuc bo (Mac)
    if kho_cuc_bo(khoa): ghi_ng('kho',khoa); return 'kho',0
    anon=_doc_khoa('SUPABASE_ANON_THENAIL','thenail-supabase-anon'); khoa_cong=_doc_khoa('SG_CONG_KHOA','sangame-sg-cong-khoa')
    if not anon or not khoa_cong: raise Loi('LOI: thieu SUPABASE_ANON_THENAIL hoac SG_CONG_KHOA')
    khoa_giong=_doc_khoa('THENAIL_KHOA_GIONG','thenail-khoa-giong')   # tuy chon: thieu thi goi nhu cu (khong header x-khoa)
    bi_mat=[anon,khoa_cong,khoa_giong]
    if cong is None:
        from dang.so import Cong; cong=Cong(khoa_cong)
    el=el or Eleven(anon,khoa_giong)
    def tra(k):   # cong hong => DUNG (khong thu khi khong tra duoc kho)
        try: return cong.goi('tim_credit_khoa',khoa_kho=k)
        except Exception as e: raise Loi(f'DUNG: khong tra duoc kho rieng khoa {k} (cong loi) - khong thu khi chua ro kho: '+che(str(e),bi_mat)[:200])
    def chua_ro_dung(kr,k):
        cr=kr.get('chua_ro') or []
        if cr: raise Loi(f'DUNG: luot thu truoc chua ro ket qua (khoa {k}) id '+', '.join(str(x.get('id')) for x in cr)+' - doi soat (huy dong) roi moi thu lai.')
    def _du_phong(ly_do,loi_cu):   # bi tu choi VI HAN MUC => doc bang may (0 credit); tat bang --khong-may / SG_GIONG_MAY=0 => giu raise cu
        if getattr(a,'khong_may',False) or os.environ.get('SG_GIONG_MAY','')=='0': raise loi_cu
        print(f'DU PHONG: {ly_do} -> doc bang giong may (VieNeu), 0 credit ElevenLabs. Ly do goc: {loi_cu.code}')
        try: return giong_may.doc_may(loi,ra,ly_do=ly_do,muoi=a.muoi,bi_mat=bi_mat)
        except Loi as e: raise Loi(f'{loi_cu.code} | du phong giong may cung loi: {e.code}')
    kr=None
    if a.muoi:   # lan thu lai: tra khoa GOC truoc
        khoa_goc=khoa_kho(loi,a.voice,a.model,a.on_dinh,a.toc_do,'')
        kg=tra(khoa_goc); chua_ro_dung(kg,khoa_goc)
        dg=kg.get('dong') or {}
        if dg and dg.get('trang_thai') in ('xong','khong_ro'): print(f'KHOA: dung khoa co muoi {a.muoi} ({khoa}) vi khoa goc {khoa_goc} da co ban thu HOAN TAT ({dg.get("trang_thai")}) -> chu dich thu ban moi')
        elif dg:   # lan 1 TTS xong nhung chua hoan tat (giu) => phuc hoi ban do, KHONG thu moi
            print(f'KHOA: khoa goc {khoa_goc} co ban thu chua hoan tat (trang thai {dg.get("trang_thai")}) -> PHUC HOI khoa goc, bo muoi {a.muoi}')
            khoa=khoa_goc; kr=kg
        else:
            print(f'KHOA: khoa goc {khoa_goc} chua co ban thu (lan 1 chua thu) -> dung KHOA GOC, bo muoi {a.muoi}')
            khoa=khoa_goc; kr=kg
            if kho_cuc_bo(khoa): ghi_ng('kho',khoa); return 'kho',0
    f=kho_dir()/f'{khoa}.mp3'
    # 1) kho RIENG TU qua cong (thay cache Actions cong khai): co 'dong' (da co tep) => CHI phuc hoi, 0 credit; loi => DUNG
    if kr is None: kr=tra(khoa)
    dong=kr.get('dong') or {}; link=kr.get('link')
    if dong:
        if not link: raise Loi('DUNG: kho rieng co tep nhung khong co link tai - chay lai sau, KHONG thu moi.')
        bi_mat.append(link)
        try: tai(link,f)
        except Exception as e: raise Loi('DUNG: kho rieng co tep nhung tai loi - chay lai sau, KHONG thu moi: '+che(str(e),bi_mat)[:200])
        shutil.copy(f,ra)
        if dong.get('trang_thai')=='giu' and dong.get('id'):
            try: cong.goi('khong_ro_credit',id=dong['id'],ghi_chu='phuc hoi tu tep')
            except Exception as e: _canh_bao('khong_ro_credit (phuc hoi) loi: '+che(str(e),bi_mat)[:200])
        ghi_ng('kho-rieng',khoa); print(f'KHO RIENG: phuc hoi {khoa}.mp3 tu cong, 0 credit'); return 'kho-rieng',0
    chua_ro_dung(kr,khoa)
    # 2) luat > 400 ky tu
    if n>400 and (a.voice,a.model,a.on_dinh) not in DA_THU_NGAN and not a.cho_vuot:
        raise Loi('TU CHOI: chua thu giong/model/cai dat nay bang cau ngan (<=400 ky tu). Thu 1 cau truoc, nghe ung roi moi thu ca bai.')
    # 3) giu MUC TRAN bao dam (moi ky tu <= GIA_TOI_DA credit) - tong thang + giu cho <= tran, nguyen tu trong DB
    gia=GIA_TOI_DA.get((a.voice,a.model))
    if gia is None: raise Loi(f'TU CHOI: cap giong/model ({a.voice}, {a.model}) chua co tran credit/ky tu trong GIA_TOI_DA - them vao bang sau khi do that.')
    giu=round(n*gia,1)
    tran=a.tran if a.tran is not None else TRAN_MAC_DINH.get(a.du_an)
    if tran is None: raise Loi(f'TU CHOI: du an {a.du_an} chua co tran thang (--tran)')
    g=cong.goi('giu_credit',lap_lai=False,thang=thang_vn(),credit_uoc=giu,tran=tran,dang=a.dang,ky_tu=n,khoa_kho=khoa)
    if g.get('vuot_tran') is True: return _du_phong('vuot_tran',Loi(f'TU CHOI: {a.du_an} vuot tran {tran} credit thang {thang_vn()} (lan nay giu toi da {giu}).'))
    if not g.get('id'): raise Loi(f'TU CHOI: {a.du_an} vuot tran {tran} credit thang {thang_vn()} (lan nay giu toi da {giu}).')
    idc=g['id']
    tu_choi=None
    try:
        tk0=el.goi({'action':'goi'},30); con=tk0['gioi_han']-tk0['da_dung']
        if con-giu<a.du_phong:
            cong.goi('huy_credit',id=idc,ghi_chu='du phong tai khoan'); tu_choi=Loi(f'TU CHOI: tai khoan con {con} credit, can giu {giu} + du phong {a.du_phong}.')
    except Exception as e:   # chua goi tts => khong mat credit
        cong.goi('huy_credit',id=idc,ghi_chu=che(f'loi doc tai khoan: {e}',bi_mat)[:200]); raise Loi('LOI doc tai khoan ElevenLabs: '+che(str(e),bi_mat)[:200])
    if tu_choi: return _du_phong('du_phong_tai_khoan',tu_choi)   # da huy_credit o tren
    # 4) tts. doc-giong tra HTTP 200 ke ca khi loi: {"ok":false,"loi":"tts 4xx: ..."} => huy (ElevenLabs tu choi, chua tru); loi khac / luu: / 5xx / mat ket noi => khong_ro (giu nguyen muc giu)
    try: d=el.goi({'action':'tts','voice_id':a.voice,'model_id':a.model,'stability':a.on_dinh,'speed':a.toc_do,'text':loi})
    except urllib.error.HTTPError as e:
        (cong.goi('huy_credit',id=idc,ghi_chu=f'HTTP {e.code}') if e.code<500 else cong.goi('khong_ro_credit',id=idc,ghi_chu=f'HTTP {e.code}'))
        raise Loi(f'LOI tts HTTP {e.code} ({"huy" if e.code<500 else "khong ro"} giu cho credit)')
    except Exception as e:
        cong.goi('khong_ro_credit',id=idc,ghi_chu=che(str(e),bi_mat)[:200]); raise Loi('LOI tts khong ro ket qua (da danh dau khong_ro): '+che(str(e),bi_mat)[:200])
    if not isinstance(d,dict) or d.get('ok') is not True or not d.get('nghe_thu'):
        mo_ta=che(json.dumps(d,ensure_ascii=False) if not isinstance(d,str) else d,bi_mat)[:300]
        ls=str((d or {}).get('loi','')) if isinstance(d,dict) else ''
        if isinstance(d,dict) and d.get('ok') is False and re.match(r'^tts 4\d\d\b',ls):
            cong.goi('huy_credit',id=idc,ghi_chu=mo_ta[:200]); loi_el=Loi('LOI ElevenLabs tu choi (da huy giu cho): '+mo_ta)
            if re.search(r'\bquota_exceeded\b',ls): return _du_phong('quota_exceeded',loi_el)   # chi het han muc; 4xx khac (khoa sai, ...) van DUNG
            raise loi_el
        cong.goi('khong_ro_credit',id=idc,ghi_chu=mo_ta[:200]); raise Loi('LOI tts khong chac ket qua (da danh dau khong_ro, KHONG huy): '+mo_ta)
    bi_mat.append(d['nghe_thu'])
    # 5) NGAY sau tts: ghi duong dan tep vao so de luot sau phuc hoi, khong thu lai
    ghi_ok=False
    for i in range(3):
        try:
            r=cong.goi('ghi_tep_credit',lap_lai=False,id=idc,tep=d.get('path'))
            if isinstance(r,dict) and r.get('so_dong')==1: ghi_ok=True; break
            _canh_bao(f'ghi_tep_credit lan {i+1}: cong tra so_dong={r.get("so_dong") if isinstance(r,dict) else r!r}, can 1')
        except Exception as e: _canh_bao(f'ghi_tep_credit lan {i+1} loi: '+che(str(e),bi_mat)[:200])
        if i<2: ngu(2*(i+1))
    if not ghi_ok: _canh_bao('khong ghi duoc tep vao so (3 lan) - van tai mp3; so se KHONG ghi xong (khong_ro) de luot sau bi chan cho toi khi doi soat')
    # 6) tai mp3 ve. Hong => GIU trang thai giu (tran van tinh giu)
    try: tai(d['nghe_thu'],f)
    except Exception as e:
        hau='luot sau tu phuc hoi tu kho rieng, khong thu lai' if ghi_ok else 'tep CHUA ghi vao so: luot sau se BI CHAN (dong chua ro) cho toi khi doi soat'
        raise Loi(f'LOI tai mp3 (credit DA TRU, so van giu muc giu; {hau}): '+che(str(e),bi_mat)[:200])
    shutil.copy(f,ra)
    # 7) quyet toan: chenh lech tai khoan truoc/sau. So dung cua ElevenLabs cap nhat TRE va TUNG NAC (CI that 11/10: chenh=0; Sol soi cuoi: 100->110->160 dung o 110 ghi 10 trong khi that la 60)
    #    => doc lai toi 8 lan, cach 10 s, CHI chot khi 2 lan doc LIEN TIEP bang nhau va 0 < chenh <= giu. Chua on dinh / ngoai khoang => khong_ro (giu nguyen muc giu).
    that=giu; chenh=None; ghi='chua doc'; so_lan=0; truoc=None; on_dinh=False
    for i in range(8):
        so_lan=i+1
        try:
            tk1=el.goi({'action':'goi'},30); chenh=round(tk1['da_dung']-tk0['da_dung'],1)
            if chenh>giu or chenh<0:
                ghi=f'chenh do duoc {chenh} ngoai khoang (0,{giu}]'; break   # khong the tu sua bang cho them
            if chenh>0 and truoc is not None and chenh==truoc: on_dinh=True; break
            ghi=f'chenh {chenh} chua on dinh (lan doc truoc {truoc})'; truoc=chenh if chenh>0 else None
        except Exception as e: chenh=None; truoc=None; ghi=che(f'khong doc duoc da_dung sau: {e}',bi_mat)[:150]
        if i<7: ngu(10)
    print(f'DOC SO DUNG SAU: {so_lan} lan, chenh={chenh}')
    try:
        if not ghi_ok: cong.goi('khong_ro_credit',id=idc,ghi_chu='chua ghi duoc tep')   # chua co tep trong so: KHONG xong (dong xong khong tep bi luot sau bo qua => thu lai)
        elif on_dinh and chenh is not None and 0<chenh<=giu: cong.goi('xong_credit',id=idc,credit_that=chenh); that=chenh
        else: cong.goi('khong_ro_credit',id=idc,ghi_chu=ghi)
    except Exception as e: _canh_bao('quyet toan loi (file da co, dong van giu = tinh du tran): '+che(str(e),bi_mat)[:200])
    ghi_ng('goi',khoa); print(f'GOI: {n} ky tu, {that} credit (giu toi da {giu}) -> {ra}  [khoa kho {khoa}]'); return 'goi',that
def main(argv=None):
    ap=argparse.ArgumentParser(); sp=ap.add_subparsers(dest='lenh',required=True)
    for ten in ('giong','khoa'):
        p=sp.add_parser(ten); p.add_argument('--loi'); p.add_argument('--loi-file'); p.add_argument('--voice',default=VOICE_MAC_DINH)
        p.add_argument('--model',default='eleven_v3'); p.add_argument('--on-dinh',type=float,default=0.0); p.add_argument('--toc-do',type=float,default=1.0); p.add_argument('--muoi',default=os.environ.get('GIONG_MUOI',''))
        if ten=='giong':
            p.add_argument('--ra',required=True); p.add_argument('--du-an',default='san-game'); p.add_argument('--dang',default='top5')
            p.add_argument('--tran',type=int,default=None); p.add_argument('--du-phong',type=int,default=DU_PHONG_MAC_DINH); p.add_argument('--cho-vuot',action='store_true'); p.add_argument('--khong-may',action='store_true')
    a=ap.parse_args(argv)
    if a.lenh=='khoa': return cmd_khoa(a)
    cmd_giong(a)
if __name__=='__main__': sys.modules.setdefault('giong',sys.modules['__main__']); main()   # giong_may import giong => cung module, cung lop Loi
