# Chon 1 game cho video dung FLAGSHIP (15:30) tu bang keo hang ngay cua may san deal. A1.
#   python3 chon-flagship.py [DU_LIEU_REPO] [--ngay YYYY-MM-DD]
#   Env: NGAY, GIO_DANG (15:30), KEO_FILE (duong dan tep) | KEO_DIR (thu muc chua keo/<NGAY>.json), DU_LIEU_REPO, GH_TOKEN (da_noi_bat).
#   Ra: flagship.json, cau-hinh.json, loi-dang.json, tai-san/bia1.png, ket-qua-chon.json. Thoat 3 = BO KHUNG (du lieu cu/khong game dat/khong doc duoc lich su).
# Luat (ke-hoach.md 3.2, FAIL-CLOSED): bang sai ngay · gia the cu > 7 ngay · lich su trung khong doc duoc -> thoat 3. % GIAM lay tu gia goc + gia ban DOC TREN TRANG
# (auto-post-claim-guard), khong lay `giam` cua bang; trang khong co gia goc -> bo game. Ghi ca hai % vao ket-qua-chon.json; lech > 1 diem -> CANH BAO.
import datetime,importlib.util,json,os,pathlib,re,sys,time,urllib.error,urllib.request
T=pathlib.Path(__file__).resolve().parent; ROOT=T.parent.parent
sys.path.insert(0,str(T)); sys.path.insert(0,str(T.parent/'top5'))
import ten_rut_gon as tr, ten_day_du as td, doc_tien as dt, moc_tin, loi_flagship as lf
def _nap(ten,duong):
    sp=importlib.util.spec_from_file_location(ten,str(duong)); m=importlib.util.module_from_spec(sp); sp.loader.exec_module(m); return m
GT=_nap('sangame_gia_trang',ROOT/'cong-cu'/'gia_trang.py')
UA="Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0 Safari/537.36"
VN=dt.VN; GIAM_MIN=30; DUNG_SAI_GIA=0.02; DEM_SAU_GIO=6*3600; TOI_DA_TAM=4; THUA_TI_LE=0.05; HANG_UU_TIEN=3; LECH_GIAM_CANH_BAO=1
RE_LINK=re.compile(r'https://store\.playstation\.com/([a-z]{2}-[a-z]{2})/product/([A-Za-z0-9_\-]+)')

class Thoat(Exception):
    def __init__(s,ly_do,ma=3): super().__init__(ly_do); s.ly_do=ly_do; s.ma=ma

def doc_bang(ngay,keo_file=None,keo_dir=None):
    p=keo_file or (os.path.join(keo_dir,'keo',f'{ngay}.json') if keo_dir else None)
    if not p or not os.path.exists(p): raise Thoat('chưa có bảng kèo hôm nay (không thấy tệp keo/%s.json)'%ngay)
    k=json.load(open(p,encoding='utf-8'))
    if k.get('ngay')!=ngay: raise Thoat(f"bảng kèo sai ngày: bảng {k.get('ngay')} ≠ {ngay} (chưa có bảng kèo hôm nay)")
    return k
def kiem_gia_the(gia_the,ngay,deal_diem):
    if not deal_diem.gia_the_con_han(gia_the,ngay): raise Thoat(f"giá thẻ cũ/thiếu (gia-the.json ngày {(gia_the or {}).get('ngay')}, cần ≤ 7 ngày so với {ngay})")

def tach_link(link):
    m=RE_LINK.fullmatch(link or ''); return (m.group(1),m.group(2)) if m else (None,None)

def danh_gia_the(ma,gia_cuc_bo,tien_te,gia_the,ngay,deal_diem):
    """Tinh LAI to hop the tren gia doc tu trang (khong tin `meo`). -> (dict the|None, ly_do)."""
    kq=deal_diem.quy_vnd('ps',ma,gia_cuc_bo,tien_te,gia_the,gia_the['ty_gia_ngan_hang'],hom_nay=ngay)
    if kq.get('cach')!='the' or not kq.get('mua_duoc'): return None,f"không quy được bằng thẻ ({kq.get('cach')}: {kq.get('ly_do')})"
    the=dt.gom_the(kq['the']); n=dt.so_tam(the)
    if n>TOI_DA_TAM: return None,f'cần {n} tấm thẻ (> {TOI_DA_TAM})'
    tong=kq['tong_menh_gia']
    if not tong or kq['thua']>THUA_TI_LE*tong+1e-9: return None,f"thẻ không vừa khít (dư {kq['thua']} trên tổng {tong})"
    if kq['vnd']%1000: return None,f"chi phí thẻ {kq['vnd']}đ không tròn nghìn"
    return dict(the=the,tong_menh_gia=tong,thua=kq['thua'],vnd=kq['vnd']),None

def han_con_ngay(end_ms,ngay,gio):
    """So ngay con lai tu luc dang (ngay+gio VN) toi endTime, lam tron xuong."""
    dang=datetime.datetime.fromisoformat(f'{ngay}T{gio}:00+07:00').timestamp()
    return int((int(end_ms)/1000-dang)//86400)

def tinh_giam(gia_cuc_bo,goc):
    """% giam tu gia goc + gia ban DOC TREN TRANG. Khong co goc / goc <= gia ban -> None."""
    if not goc or goc<=gia_cuc_bo: return None
    return int(round((1-gia_cuc_bo/goc)*100))

class Chon:
    """Moi phu thuoc ngoai (mang, lich su, deal_diem, video Steam) truyen qua ham/doi tuong de test khong mang."""
    def __init__(s,ngay,gio_dang,bang,gia_the,deal_diem,lay_trang,nb,video_steam):
        s.ngay=ngay; s.gia_the=gia_the; s.dd=deal_diem; s.lay_trang=lay_trang; s.nb=nb; s.video_steam=video_steam
        s.gio=gio_dang; s.han_ms=int((datetime.datetime.fromisoformat(f'{ngay}T{gio_dang}:00+07:00')+datetime.timedelta(seconds=DEM_SAU_GIO)).timestamp()*1000)
        s.bang=bang; s.loai=[]; s.canh_bao=[]; s.kieu_mo=lf.kieu_mo(ngay)
    def ghi_loai(s,r,ly): s.loai.append(f"#{r.get('hang')} {str(r.get('ten'))[:40]} ({r.get('vung_re_nhat')}, {r.get('gia_vnd')}đ): {ly}")
    def xet(s,r):
        """Mot dong bang -> (flagship dict | None, ly do). Dung thu tu 3.2: loc, trung, ten, trang, the, media, loi."""
        if r.get('nen_tang')!='ps': return None,'không phải PS'
        ma=r.get('vung_re_nhat')
        if ma not in dt.TIEN_TE_CUA_MA: return None,f'vùng {ma} không phải US/HK/SG'
        if not r.get('da_kiem_trang'): return None,'chưa kiểm trang'
        if r.get('lech_gia'): return None,'bảng báo lệch giá'
        if r.get('cach_quy')!='the': return None,f"cách quy {r.get('cach_quy')} ≠ the"
        if (r.get('giam') or 0)<GIAM_MIN: return None,f"giảm {r.get('giam')}% < {GIAM_MIN}%"
        loc,pid=tach_link(r.get('link'))
        if not pid: return None,f"link không đúng dạng store.playstation.com/<loc>/product/<pid>: {r.get('link')}"
        if loc!=dt.LOC_CUA_MA[ma]: return None,f'locale {loc} lệch vùng {ma}'
        ly=s.nb.trung(r['ten'],[pid])
        if ly: return None,f'đã nổi bật trong 3 ngày: {ly}'
        ten_goc=r['ten']
        if not td.doc_duoc(ten_goc): return None,f'tên máy đọc không ổn định ({td.hien(ten_goc)})'
        if re.search(r'\b(cat|cats|mèo|kitten|kitty)\b',ten_goc,re.I): return None,'tên có mèo (cấm hình mèo)'
        html=s.lay_trang(loc,pid)
        if not html: return None,f'không mở được trang {loc}/{pid}'
        g=GT.khoi_gia(html,pid)
        if not g: return None,'trang không có khối giá mua đứt rõ ràng của đúng pid'
        tien=dt.TIEN_TE_CUA_MA[ma]
        if g['tien_te']!=tien: return None,f"tiền tệ trang {g['tien_te']} ≠ {tien}"
        con=g['gia_cuc_bo']; bang_gia=GT.doc_gia(((r.get('gia_vung') or {}).get(ma) or {}).get('gia'))
        if not bang_gia or abs(con-bang_gia)/bang_gia>DUNG_SAI_GIA: return None,f'giá trang {con} lệch giá bảng {bang_gia} > 2%'
        if not g['endTime']: return None,'không có endTime (không biết hạn giảm)'
        if int(g['endTime'])<s.han_ms: return None,f"hết hạn sớm ({datetime.datetime.fromtimestamp(int(g['endTime'])/1000,VN):%d/%m %H:%M} < giờ đăng + 6h)"
        giam=tinh_giam(con,g['gia_goc'])
        if giam is None: return None,'trang không cho giá gốc (hoặc gốc ≤ giá bán): không tính được % giảm từ trang'
        if giam<GIAM_MIN: return None,f'giảm theo trang {giam}% < {GIAM_MIN}%'
        lech=abs(giam-r['giam'])
        if lech>LECH_GIAM_CANH_BAO: s.canh_bao.append(f"CANH BAO #{r.get('hang')} {r['ten'][:40]}: giảm theo trang {giam}% ≠ bảng {r['giam']}% (lệch {lech} điểm) — dùng {giam}%"); print(s.canh_bao[-1])
        th,ly=danh_gia_the(ma,con,tien,s.gia_the,s.ngay,s.dd)
        if not th: return None,ly
        m=GT.media(html,pid); trailer=sorted(m['video']); nguon='ps'; vst=[]
        if not trailer:
            vst=s.video_steam(ten_goc) or []
            if not vst: return None,'không có video game (PS Store không có trailer, Steam không có)'
            trailer=[v['url'] for v in vst]; nguon='steam'
        han_dt,han_hien,han_doc=dt.han_vn(g['endTime'])
        moc=moc_tin.chon_moc(ten_goc,(r.get('nong') or {}).get('mau'),r.get('thap_nhat'))
        try:
            f=dict(ten=td.hien(ten_goc),ten_goc=ten_goc,ten_doc=td.doc(ten_goc),ten_the=td.hien(ten_goc),pid=pid,loc=loc,ma=ma,vung=dt.TEN_VUNG[ma],tien_te=tien,
                   gia_cuc_bo=con,goc_cuc_bo=g['gia_goc'],giam=giam,gia_hien=dt.hien_tien(con,tien),goc_hien=dt.hien_tien(g['gia_goc'],tien),gia_doc=dt.doc_tien(con,tien),goc_doc=dt.doc_tien(g['gia_goc'],tien),han_con_ngay=han_con_ngay(g['endTime'],s.ngay,s.gio),
                   endTime=str(g['endTime']),han_hien=han_hien,han_doc=han_doc,
                   the=th['the'],the_hien=dt.the_hien(th['the'],tien),the_doc=dt.doc_the(th['the'],tien),tong_menh_gia=th['tong_menh_gia'],thua=th['thua'],
                   gia_vnd=th['vnd'],gia_vnd_hien=dt.hien_vnd(th['vnd']),vnd_doc=dt.doc_vnd(th['vnd']),moc=moc,
                   trailer=trailer,nguon_video=nguon,video_steam=vst,anh_chup=m['anh_chup'][:6],anh=(r.get('anh_url') or '').split('?')[0],
                   keo=dict(hang=r.get('hang'),diem=r.get('diem'),nong_diem=(r.get('nong') or {}).get('diem')),
                   the_nguon=the_nguon(s.gia_the,th['the'],tien,s.gia_the_vung(ma)),
                   giam_bang=r['giam'])
        except (ValueError,KeyError) as e: return None,f'không đọc được số thành chữ: {e}'
        if not f['anh']: return None,'không có ảnh bìa'
        ds,gi,bo=lf.lap_loi(f,s.ngay)
        if ds is None: return None,(f'lời ước lượng {gi:.1f}s < {lf.SAN_GIAY:.0f}s (quá ngắn)' if gi<lf.SAN_GIAY else f'lời ước lượng {gi:.1f}s > 26s dù đã bỏ móc')
        if bo:
            f['moc']=dict(loai='khong',cau='',chu='',nguon='',goc=''); s.canh_bao.append(f"{r['ten'][:40]}: lời {gi:.1f}s sau khi bỏ móc (bỏ móc vì quá 25s)")
        f['uoc_luong_giay']=round(gi,1)
        return f,None
    def gia_the_vung(s,ma): return ((s.gia_the.get('vung') or {}).get(ma) or {})
    def chon(s):
        rows=sorted([r for r in s.bang.get('keo',[]) if r.get('nen_tang')=='ps'],key=lambda r:r.get('hang') or 0)
        dat=[]
        for r in rows:
            if dat and (r.get('hang') or 0)>(dat[0].get('keo') or {}).get('hang',0)+HANG_UU_TIEN: break
            f,ly=s.xet(r)
            if f is None: s.ghi_loai(r,ly); continue
            dat.append(f)
            if f['moc']['loai']=='tin': break
        if not dat: raise Thoat(f'không game PS nào qua mọi lọc ({len(rows)} dòng PS trong bảng)')
        return next((f for f in dat if f['moc']['loai']=='tin'),dat[0])

def the_nguon(gia_the,the,tien,vung_the):
    """Shop + ngay cua gia the da dung (cho mo ta): the re nhat khop menh gia + gia VND."""
    shops=[]
    for t in the:
        for c in vung_the.get('cac_the') or []:
            if abs(float(c['menh_gia'])-float(t['menh_gia']))<1e-9 and t.get('gia_vnd') and abs(float(c['gia'])-t['gia_vnd'])<1: shops.append(c.get('shop')); break
    return dict(ngay=gia_the.get('ngay'),shop=sorted(set(x for x in shops if x)))

def lay_trang_mang(loc,pid):
    for lan in range(3):
        try: return urllib.request.urlopen(urllib.request.Request(f'https://store.playstation.com/{loc}/product/{pid}',headers={'User-Agent':UA}),timeout=40).read().decode('utf-8','ignore')
        except urllib.error.HTTPError as e:
            if e.code in (404,410): return None
            time.sleep(2*(lan+1))
        except Exception: time.sleep(2*(lan+1))
    return None

def loi_dang(f,ngay):
    k=lf.kieu_mo(ngay); N=f"{f['gia_vnd']//1000} nghìn"; ten=f['ten']; v=f['vung']
    td=['{t} còn {N}, mua sao cho khít tiền?','{N} đồng mua đứt {t}, có thật không?','{t} giảm {g}%: về tay chỉ {N}','Chỉ {N} là có {t} trên PS5','{t} PS5 còn {N}, thẻ PSN nào cho khít?','{t} đang giảm {g}%, quy ra còn {N}','Mua {t} hết {N}: nạp thẻ sao cho khít tiền'][k]
    tieu_de=td.format(t=ten,N=N,g=f['giam'])
    d=[f"{ten} đang giảm {f['giam']}% trên PS Store {v}: {f['gia_hien']} (giá gốc {f['goc_hien']}), giảm tới {f['han_hien']}."]
    tn=f.get('the_nguon') or {}; shop=', '.join(tn.get('shop') or [])
    d.append(f"{f['the_doc']} là vừa khít: {' + '.join(f['the_hien'])} = {f['gia_vnd_hien']}"+(f" (giá thẻ PSN ngày {tn['ngay'][8:10]}/{tn['ngay'][5:7]}"+(f", shop {shop}" if shop else '')+')' if tn.get('ngay') else '')+'.')
    m=f.get('moc') or {}
    if m.get('loai')=='tin': d.append(f"Tin mới: {m['goc']}"+(f" — nguồn: {m['nguon']}" if m.get('nguon') else ''))
    elif m.get('loai')=='thap_nhat': d.append(m['chu'].capitalize()+' (theo dõi giá của Săn Game).')
    d.append(f'Lưu ý: mua ở store {v} thì cần tài khoản PSN {v}.')
    d.append('Tra giá các vùng PS Store: https://sangame.com.vn/')
    return dict(tieu_de=tieu_de[:100],mo_ta='\n'.join(d)[:2000],hashtag=['#SănGame','#PlayStation','#PS5','#GiảmGiá'],link='https://sangame.com.vn/',ten_game=ten)

def ghi_ket_qua(ma_loi,kq): json.dump(kq,open(T/'ket-qua-chon.json','w',encoding='utf-8'),ensure_ascii=False,indent=1)

def main(argv=None,env=None):
    argv=list(sys.argv[1:] if argv is None else argv); env=os.environ if env is None else env
    ngay=next((argv[i+1] for i,a in enumerate(argv) if a=='--ngay'),None) or env.get('NGAY') or ''
    args=[a for a in argv if not a.startswith('--') and a!=ngay]
    if not ngay: ngay=datetime.datetime.now(VN).date().isoformat()
    gio=env.get('GIO_DANG') or '15:30'
    ch=None
    try:
        repo=next((pathlib.Path(p) for p in [args[0] if args else None,env.get('DU_LIEU_REPO'),ROOT/'du-lieu',pathlib.Path.home()/'Kho-luu/kenh-game/dang-lam/kenh-game-du-lieu'] if p and (pathlib.Path(p)/'deal_diem.py').exists()),None)
        if not repo: raise Thoat('không thấy thư mục kenh-game-du-lieu (deal_diem.py) — đặt DU_LIEU_REPO',2)
        sys.modules.pop('deal_diem',None); sys.path.insert(0,str(repo)); import deal_diem
        bang=doc_bang(ngay,env.get('KEO_FILE'),env.get('KEO_DIR'))
        gia_the=json.load(open(repo/'du-lieu'/'gia-the.json',encoding='utf-8')); kiem_gia_the(gia_the,ngay,deal_diem)
        DNB=_nap('sangame_da_noi_bat',ROOT/'cong-cu'/'da_noi_bat.py'); VS=_nap('sangame_video_steam',ROOT/'cong-cu'/'video_steam.py')
        nb=DNB.da_noi_bat(ngay,'flagship',3)
        print('đã nổi bật 3 ngày (mọi khuôn):',nb.ghi_chu)
        if nb.canh_bao: raise Thoat('lịch sử trùng không đọc được (fail-closed): '+nb.canh_bao)
        def video_steam(ten):
            for t in dict.fromkeys([tr.hien_thi(ten),ten]):
                try: kq=VS.tim_video(t)
                except Exception: kq=[]
                if kq: return kq
            return []
        ch=Chon(ngay,gio,bang,gia_the,deal_diem,lay_trang_mang,nb,video_steam)
        f=ch.chon()
        (T/'tai-san').mkdir(exist_ok=True)
        for lan in range(3):
            try: urllib.request.urlretrieve(f['anh']+'?w=720',T/'tai-san'/'bia1.png'); break
            except Exception as e:
                if lan==2: raise Thoat(f'không tải được ảnh bìa: {e}')
                time.sleep(2)
        ghi_json=lambda n,o: json.dump(o,open(T/n,'w',encoding='utf-8'),ensure_ascii=False,indent=1)
        ghi_json('flagship.json',f)
        dd,mm=ngay[8:10],ngay[5:7]
        json.dump(dict(ngay=f'{dd}/{mm}',ngay_iso=ngay,gio_dang=gio,kieu_mo=ch.kieu_mo),open(T/'cau-hinh.json','w',encoding='utf-8'),ensure_ascii=False)
        ghi_json('loi-dang.json',loi_dang(f,ngay))
        ghi_json('ket-qua-chon.json',dict(trang_thai='du',ngay=ngay,chon=dict(hang=f['keo']['hang'],ten=f['ten_goc'],pid=f['pid'],giam_theo_trang=f['giam'],giam_theo_bang=f['giam_bang'],goc_cuc_bo=f['goc_cuc_bo'],gia_cuc_bo=f['gia_cuc_bo'],moc=f['moc']['loai'],uoc_luong_giay=f['uoc_luong_giay']),uoc_luong_giay=f['uoc_luong_giay'],canh_bao=ch.canh_bao,ghi_chu_lich_su=nb.ghi_chu,loai=ch.loai))
        print(f"CHON #{f['keo']['hang']} {f['ten']} [{f['ten_doc']}] {f['gia_hien']} (gốc {f['goc_hien']}, -{f['giam']}% theo trang / bảng {f['giam_bang']}%) {f['vung']} · thẻ {' + '.join(f['the_hien'])} = {f['gia_vnd_hien']} · hết {f['han_hien']} · móc {f['moc']['loai']} {f['moc'].get('chu','')} · {f['nguon_video']} · ~{f['uoc_luong_giay']}s")
        for l in ch.loai: print('  loại',l)
        return 0
    except Thoat as e:
        kq=dict(trang_thai='thieu' if e.ma==3 else 'loi',ly_do=e.ly_do,ngay=ngay,loai=(ch.loai[-40:] if ch else []),canh_bao=(ch.canh_bao if ch else []))
        try: json.dump(kq,open(T/'ket-qua-chon.json','w',encoding='utf-8'),ensure_ascii=False,indent=1)
        except OSError: pass
        print('BỎ KHUNG:',e.ly_do,file=sys.stderr)
        for l in (ch.loai if ch else []): print('  loại',l,file=sys.stderr)
        return e.ma
if __name__=='__main__': sys.exit(main())
