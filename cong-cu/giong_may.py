#!/usr/bin/env python3
"""Giong MAY du phong (VieNeu-TTS, CPU) khi ElevenLabs bi tu choi VI HAN MUC (SG-GIONG-may, Hao chot 28/10/2026: giong "Adam bua").
Chi giong.py goi vao day o 3 cho tu choi vi han muc (vuot tran thang, du phong tai khoan, ElevenLabs quota_exceeded); loi khac van DUNG nhu cu.
VieNeu chay trong TIEN TRINH CON bang `uv run --with vieneu==3.8.3` (cong-cu/vieneu_doc.py) nen KHONG keo onnxruntime vao pyproject/uv.lock cua repo.
Kho may: khoa rieng ('vieneu:'+giong, phien ban, revision mo hinh, muoi) => KHONG dung kho ElevenLabs. Chuyen ma + kiem thoi luong tren tep TAM roi moi os.replace vao kho.
Khong import gi nang o cap module (giong.py import file nay luc khoi dong)."""
import json,os,pathlib,re,shutil,subprocess,tempfile
GIONG_MAY_MAC_DINH='Adam bựa'
VIENEU_PIN='vieneu==3.8.3'
REV_BACKBONE=('pnnbao-ump/VieNeu-TTS-v3-Turbo','61b85e3d937fbbacb387714180e8182823512523')
REV_CODEC=('OpenMOSS-Team/MOSS-Audio-Tokenizer-Nano-ONNX','ceff0d0749bfb3fa2d61149794ec6feef0d1e1ae')   # gitleaks:allow (commit Hugging Face cong khai, khong phai khoa)
PHIEN_BAN_MO_HINH=f'{VIENEU_PIN}|{REV_BACKBONE[0]}@{REV_BACKBONE[1]}|{REV_CODEC[0]}@{REV_CODEC[1]}'
NGUON_TEN='giong-nguon.json'
TOI_THIEU_BYTE=5000; GIAY_MOI_KY_TU=(0.04,0.12)   # do that Top 5: 689 ky tu -> 32,45 s (0,047/ky tu); ngoai khoang = mo hinh doc lap/cut
TIMEOUT_DOC=900
def bo_the(loi):
    # the cam xuc ElevenLabs dang [excited] / [whispers] -> VieNeu doc thanh chu => bo, gop khoang trang
    s=re.sub(r'\s+',' ',re.sub(r'\[[a-zA-Z _-]+\]\s*','',loi)).strip()
    if not s:
        import giong as G; raise G.Loi('LOI giong may: loi rong sau khi bo the cam xuc')
    return s
def ghi_nguon(ra,**kw):
    # giong-nguon.json canh tep giong: nguon (elevenlabs|may) de gom/ghi chu ve sau; ghi cho MOI lan thanh cong
    p=pathlib.Path(ra).parent/NGUON_TEN; p.write_text(json.dumps(kw,ensure_ascii=False,indent=1),encoding='utf-8'); return p
def _env_con():
    # env TOI THIEU cho tien trinh con: khong SUPABASE_*, SG_*, THENAIL_*
    e={k:v for k,v in os.environ.items() if k in ('PATH','HOME','LANG','LC_ALL','TMPDIR','XDG_CACHE_HOME') or k.startswith(('HF_','UV_'))}
    e['HF_HUB_DISABLE_TELEMETRY']='1'; return e
def _thoi_luong(p,chay):
    import giong as G
    r=chay(['ffprobe','-v','error','-show_entries','format=duration','-of','csv=p=0',str(p)],capture_output=True,text=True,timeout=60)
    try: return float((r.stdout or '').strip())
    except ValueError: raise G.Loi('LOI giong may: ffprobe khong doc duoc thoi luong '+str(p.name))
def _kiem(p,n,chay):
    # tep dat khi >= 5000 byte va thoi luong nam trong [0,04 x n, 0,12 x n] giay; tra thoi luong, hong => ValueError
    if not p.exists() or p.stat().st_size<TOI_THIEU_BYTE: raise ValueError('mp3 qua nho')
    d=_thoi_luong(p,chay); lo,hi=GIAY_MOI_KY_TU[0]*n,GIAY_MOI_KY_TU[1]*n
    if not lo<=d<=hi: raise ValueError(f'thoi luong {d:.1f} s ngoai khoang [{lo:.1f}, {hi:.1f}] s cho {n} ky tu (mo hinh doc lap/cut)')
    return d
def doc_may(loi,ra,giong=GIONG_MAY_MAC_DINH,ly_do='',muoi='',bi_mat=(),chay=subprocess.run):
    """Doc `loi` bang VieNeu -> mp3 o `ra` + giong-nguon.json canh no. Tra ('may',0) hoac ('may-kho',0). Loi => giong.Loi."""
    import giong as G
    sach=bo_the(loi); n=len(sach)
    khoa=G.khoa_kho(sach,'vieneu:'+giong,PHIEN_BAN_MO_HINH,0.0,1.0,muoi)
    kho=G.kho_dir()/f'{khoa}.mp3'; ra=pathlib.Path(ra); ra.parent.mkdir(parents=True,exist_ok=True)
    def xong(cach,d):
        shutil.copy(kho,ra)
        ghi_nguon(ra,nguon='may',cach=cach,dong_co='vieneu',phien_ban=VIENEU_PIN.split('==')[1],giong=giong,ly_do=ly_do,khoa=khoa,giay=round(d,2),
                  mo_hinh={REV_BACKBONE[0]:REV_BACKBONE[1],REV_CODEC[0]:REV_CODEC[1]})
        print(f'GIONG MAY: {n} ky tu, {giong}, {round(d,1)} s, ly do {ly_do or "-"} -> {ra}  [khoa kho may {khoa}] ({cach}, 0 credit)')
        return cach,0
    if kho.exists():   # cache hit cung kiem lai; hong => xoa roi doc lai
        try: return xong('may-kho',_kiem(kho,n,chay))
        except (ValueError,G.Loi): kho.unlink(missing_ok=True)
    with tempfile.TemporaryDirectory() as td:
        td=pathlib.Path(td); lt=td/'loi.txt'; lt.write_text(sach,encoding='utf-8'); wav=td/'x.wav'
        cmd=['uv','run','-q','--no-project','--python','3.13','--with',VIENEU_PIN,'python','-I',str(pathlib.Path(__file__).resolve().parent/'vieneu_doc.py'),
             '--loi-file',str(lt),'--giong',giong,'--ra',str(wav)]
        try: r=chay(cmd,capture_output=True,text=True,timeout=TIMEOUT_DOC,env=_env_con())
        except Exception as e: raise G.Loi('LOI giong may: khong chay duoc VieNeu: '+G.che(str(e),bi_mat)[:300])
        if r.returncode!=0: raise G.Loi('LOI giong may: VieNeu thoat '+str(r.returncode)+': '+G.che(((r.stderr or '')+(r.stdout or '')).strip(),bi_mat)[-300:])
        if not wav.exists(): raise G.Loi('LOI giong may: VieNeu khong ghi ra wav')
        fd,tam=tempfile.mkstemp(prefix=kho.name+'.',suffix='.tmp',dir=kho.parent); os.close(fd); tam=pathlib.Path(tam)   # rieng tung luot (Sol soi diff P2: 2 luot cung khoa dung chung .tmp)
        try:
            r=chay(['ffmpeg','-y','-v','error','-i',str(wav),'-ar','44100','-ac','1','-c:a','libmp3lame','-b:a','128k','-f','mp3',str(tam)],capture_output=True,text=True,timeout=300)
            if r.returncode!=0: raise G.Loi('LOI giong may: ffmpeg doi mp3 that bai: '+G.che((r.stderr or '').strip(),bi_mat)[-300:])
            try: d=_kiem(tam,n,chay)
            except ValueError as e: raise G.Loi('LOI giong may: '+str(e))
            os.replace(tam,kho)
        finally: tam.unlink(missing_ok=True)
    return xong('may',d)
