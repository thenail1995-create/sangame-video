#!/usr/bin/env python3
# C1 — Chọn ĐÚNG 3 tin cho bản tin sáng (dựng 21:00 tối hôm trước bằng dữ liệu hôm trước). Ghi tin-chon.json + tải ảnh Sony vào tai-san/ (không commit).
#   python3 chon-tin.py --du-lieu <repo kenh-game-du-lieu> --ngay-dang 2026-10-12 [--ngay-dung 2026-10-11]
# Dùng LẠI bộ đọc + kiểm bài và bộ chọn của repo dữ liệu (cùng luật với web): bai_viet.danh_sach_duyet (bỏ nháp, bỏ bài lỗi kiem_bai),
# bai_viet.da_het_han, tin_tu_sinh.chon_giam_sau / chon_vua_giam / chon_deal_hot.
# THỨ TỰ ƯU TIÊN (Opus chốt 12/10, luật thuần ở chon_logic.py + test_chon_tin.py): bài tin-nong có ngay >= ngày ĐĂNG - 1 (PS Plus tháng trước)
#   -> GIẢM SÂU -> PS Plus kho mới (>= 1 game) -> đợt sale lớn đang chạy/sắp hết (lich-sale.json) -> MỚI GIẢM -> DEAL HOT (thứ Sáu đảo).
#   KHÔNG 2 tin cùng loại "danh sách giảm giá" (giảm sâu / mới giảm / deal hot) trừ khi hết loại khác.
#   DỰ PHÒNG: SẮP HẾT GIẢM (game bán chạy hết giảm trong 2–4 ngày) — xét SAU deal hot, chỉ khi thiếu tin; là "loại khác" nên không bị luật trên chặn (Hào chốt 11/10).
# Deal (giá) chỉ nhận khi trang sản phẩm PS Store ĐÚNG VÙNG của giá còn hạn >= 2 ngày tính từ 07:30 ngày đăng (endTime của đúng khối giá khớp giá trong sổ).
# Mã thoát: 0 đủ 3 tin · 3 KHÔNG đủ 3 tin (bỏ khung + ntfy; khuôn cố định 3 tin: full.html, am-tin.py) · 4 dữ liệu cũ · 2 lỗi tham số.
import argparse,datetime as dtm,json,os,pathlib,re,subprocess,sys
T=pathlib.Path(__file__).resolve().parent; sys.path.insert(0,str(T))
import so_chu,tin_chung as tc,chon_logic as cl

ap=argparse.ArgumentParser()
ap.add_argument('--du-lieu',required=True,help='thu muc checkout repo rieng tu kenh-game-du-lieu')
ap.add_argument('--ngay-dang',required=True,help='YYYY-MM-DD (gio VN) - ngay video len')
ap.add_argument('--ngay-dung',help='YYYY-MM-DD - ngay du lieu "hom truoc" (mac dinh = ngay dang - 1)')
ap.add_argument('--ra',default=str(T/'tin-chon.json'))
a=ap.parse_args()
VN=dtm.timezone(dtm.timedelta(hours=7))
NGAY_DANG=dtm.date.fromisoformat(a.ngay_dang); NGAY_DUNG=dtm.date.fromisoformat(a.ngay_dung) if a.ngay_dung else NGAY_DANG-dtm.timedelta(days=1)
HAN_MIN_MS=int((dtm.datetime.combine(NGAY_DANG,dtm.time(7,30),VN)+dtm.timedelta(days=2)).timestamp()*1000)   # con han >= 2 ngay tinh tu 07:30 ngay dang
REPO=pathlib.Path(a.du_lieu).resolve(); TS=T/'tai-san'; a.ra=str(pathlib.Path(a.ra).resolve())
sys.path.insert(0,str(REPO)); os.chdir(REPO)
import bai_viet, tin_tu_sinh as t

BO=[]   # ly do bo tung ung vien (ghi vao tin-chon.json)
def bo(ten,ly_do):
    BO.append(f'{ten}: {ly_do}'); print('  bo',ten,'-',ly_do)

d=t.nap_du_lieu()
if d is None: print('LOI: thieu so du lieu (trang-game.json)'); sys.exit(4)
cu_chinh,_=t.kiem_do_moi(NGAY_DUNG,d)
if cu_chinh: print('DU LIEU CU, khong dung bang tin:','; '.join(cu_chinh)); sys.exit(4)
th=t.thu_hang_theo_khoa(d['so'],d['giam_gia']); qd=d['qd']
SHA=subprocess.run(['git','rev-parse','HEAD'],capture_output=True,text=True,cwd=REPO).stdout.strip()
print(f'ngay dang {NGAY_DANG}, ngay dung {NGAY_DUNG}, du lieu cap_nhat {d["cap_nhat"]}, han toi thieu deal {dtm.datetime.fromtimestamp(HAN_MIN_MS/1000,VN):%d/%m %H:%M}')

def vnd_so(h): return int(re.sub(r'\D','',t._dong(qd,h['vnd'])))
def ddmm(iso): return f'{iso[8:10]}/{iso[5:7]}'

# ---------------------------------------------------------------- bài viết đã duyệt (cùng luật web)
BAI=bai_viet.danh_sach_duyet(bai_viet.THU_MUC,NGAY_DUNG)
def tin_nong_ngay():
    return [b for b in BAI if bai_viet.nhom_cua(b)=='tin-nong' and cl.tin_nong_hop_le(b['ngay'],NGAY_DANG) and not bai_viet.da_het_han(b,NGAY_DANG)]

CHUYEN_MUC={'game-moi':'GAME MỚI','ps-plus':'PS PLUS','huong-dan':'HƯỚNG DẪN','giam-gia':'GIẢM GIÁ'}
def rut_tit(b,toi_da=40):
    phu=(b.get('phu_anh') or '').strip()
    if phu:
        if len(phu)<=toi_da: return phu
        dau=re.split(r'\s+[·|]\s+',phu)[0].strip()
        if 8<=len(dau)<=toi_da: return dau
    return {'game-moi':'Tin game mới trên PlayStation','ps-plus':'Tin PS Plus mới','huong-dan':'Hướng dẫn mới cho game thủ'}.get(b.get('chuyen_muc'),'Tin PlayStation mới')   # quá dài -> mẫu theo loại (Sol #18)
def moc_hien(b):
    nhan=(b.get('nhan_anh') or '').strip()
    for x in (nhan,re.sub(r'^THÁNG\s+','',nhan,flags=re.I)):
        if x and len(x)<=9: return x
    return None
def nhan_nguon(b):
    n=(b.get('nguon') or [{}])[0]; ten=re.split(r'\s+[—(]',n.get('ten',''))[0].strip() or 'SĂN GAME'
    return f'{ten[:22]} · {ddmm(n.get("ngay_doc") or b["ngay"])}'.upper()

def tin_vang(b,uu):
    anh=b.get('anh') or (b.get('anh_ghep') or [None])[0]
    if not anh or not bai_viet.anh_hop_le(anh): return bo(f'bai {b["slug"]}','khong co anh hop le')
    f=tc.tai_anh(anh,TS,'bai')
    cm=b.get('chuyen_muc')
    return dict(kieu='bai',mau='vang',uu=uu,khoa=f'bai:{b["slug"]}',loai=CHUYEN_MUC.get(cm,'TIN NÓNG'),nguon=nhan_nguon(b),
                tit=rut_tit(b),moc=moc_hien(b),anh_url=[anh],anh_tep=[f'tai-san/{f.name}'],bai=b['ten_file'],tieu_de_bai=b['tieu_de'],
                nhan_dong='CHI TIẾT TẠI',dong='sangame.com.vn · Tin hot',trailer=[],anh_chup=[])

def nen_tu_trang(html,pid):
    """Trailer (xếp theo H21) rồi ảnh chụp màn hình đầu tiên (nền dự phòng) CHỈ của Product:<pid> trên trang sản phẩm."""
    tr=tc.xep_trailer(tc.trailers(html,pid)); shot=[]
    if not tr:
        ss=tc.anh_chup(html,pid)
        if ss:
            try: shot=[f'tai-san/{tc.tai_anh(ss[0],TS,"man",rong=1920).name}']
            except Exception as e: print('  khong tai duoc anh chup:',e)
    return tr,shot

# PS Plus tháng: tên game mới (dòng "- Tên (mới)" trong bài tự sinh) ghép bìa/sản phẩm qua gameslist của Sony (cùng nguồn bài)
DLC=re.compile(r'starter pack|add-?on|\bdlc\b|bundle|\bpack\b|season pass|demo',re.I)
_feed=[]
def feed_ps_plus():
    if not _feed:
        try:
            f=t.lay_json(t.URL_GAMESLIST)
            _feed.append({t._ten_md(t.gon_ten(g['name'])):g for b in f for g in b.get('games',[]) if g.get('name')})
        except Exception as e:
            print('  khong lay duoc gameslist PS Plus:',e); _feed.append({})
    return _feed[0]

def tin_ps_plus_thang(b,uu):
    moi=re.findall(r'^-\s+(.+?)\s+\(mới\)\s*$',b['noi_dung'],re.M)
    fe=feed_ps_plus(); game=[]
    for ten in moi:
        g=fe.get(ten)
        if DLC.search(ten) or not g or not g.get('imageUrl') or not bai_viet.anh_hop_le(g['imageUrl']): continue
        game.append(dict(ten=ten,anh=g['imageUrl'],pid=g.get('productId'),concept=g.get('conceptUrl')))
    n_moi=len([x for x in moi if not DLC.search(x)])
    if len(game)<2:   # khong ghep duoc ten <-> bia: chi dung bia trong bai, khong noi ten (khong doan)
        ghep=[u for u in (b.get('anh_ghep') or []) if bai_viet.anh_hop_le(u)][:3]
        if len(ghep)<2 or n_moi<1: return bo(f'bai {b["slug"]}','PS Plus: khong ghep duoc ten game voi bia')
        game=[dict(ten=None,anh=u,pid=None,concept=None) for u in ghep]
    ngoai_le=so_chu._ngoai_le()
    bo_doc=lambda x: x['ten'] is None or ngoai_le.get(x['ten'],{}).get('bo_doc')
    game=game[:3]
    tep=[tc.tai_anh(g['anh'],TS,'ps',rong=720) for g in game]
    co_ten=[g for g in game if g['ten']]
    ten_hien=[so_chu.ten_hien_thi(g['ten']) for g in co_ten]
    doc=[(so_chu.ten_doc(so_chu.ten_hien_thi(g['ten']),g['ten'])) for g in co_ten if not bo_doc(g)][:2]
    noi=[th for g,th in zip(co_ten,ten_hien) if not bo_doc(g)][:2]
    pid=next((g['pid'] for g in game if g['pid'] and not bo_doc(g)),None) or next((g['pid'] for g in game if g['pid']),None)
    tr,shot=[],[]
    if pid:
        try: tr,shot=nen_tu_trang(tc.lay_trang('en-sg',pid),pid)
        except Exception as e: print('  khong mo duoc trang game PS Plus (nen dung bia):',e)
    return dict(kieu='ps-plus-thang',mau='xanh',uu=uu,khoa=f'ps-plus-thang:{b["ngay"]}',loai='PS PLUS',nguon=f'PLAYSTATION SG · {ddmm(b["ngay"])}',
                n_moi=n_moi,ten_game=ten_hien,ten_doc=doc,ten_noi=noi,anh_url=[g['anh'] for g in game],anh_tep=[f'tai-san/{f.name}' for f in tep],
                nhan_dong='MỌI GÓI PS PLUS ĐỀU NHẬN',bai=b['ten_file'],tieu_de_bai=b['tieu_de'],pid=pid,loc='en-sg',trailer=tr,anh_chup=shot)

def ung_tin_nong(uu0):
    """Bài đã duyệt nhóm tin-nong có ngay >= ngày đăng - 1: PS Plus tháng trước, rồi các bài khác (mới nhất trước)."""
    ds=sorted(tin_nong_ngay(),key=lambda b:(b.get('loai_tu_sinh')!='ps-plus-thang',[-ord(c) for c in b['ten_file']]))
    if not ds: bo('tin-nong','khong co bai duyet voi ngay >= ngay dang - 1 (hoac het han)')
    for k,b in enumerate(ds):
        try: r=(tin_ps_plus_thang if b.get('loai_tu_sinh')=='ps-plus-thang' else tin_vang)(b,uu0+k*0.1)
        except Exception as e: r=bo(f'bai {b["slug"]}',f'loi mang: {e}')
        if r: yield r

# ---------------------------------------------------------------- tin giá (tin_tu_sinh)
LOAI_GIA={'giam-sau':('GIẢM SÂU','giảm sâu','RẺ NHẤT'),'vua-giam':('MỚI GIẢM','vừa vào đợt giảm','MỚI GIẢM'),'deal-hot':('DEAL HOT','đang giảm mạnh','RẺ NHẤT'),
          'sap-het':('SẮP HẾT GIẢM','sắp hết giảm','RẺ NHẤT')}
def xac_minh(h):
    """(thong_tin, None) nếu trang PS Store đúng vùng xác nhận giá khớp + còn hạn; (None, lý do)."""
    ma=h['ma']; b=d['so']['game'][h['khoa']]['vung'].get(ma) or {}
    if not b.get('id') or not b.get('con'): return None,'so thieu id/gia vung'
    try: html=tc.lay_trang(tc.LOC[ma],b['id'])
    except Exception as e: return None,f'khong mo duoc trang: {e}'
    g=tc.gia_khop(html,b['con'],ma,b['id'])
    if not g: return None,f'trang {tc.LOC[ma]} khong co khoi gia {b["con"]} co han (khong xac minh duoc)'
    if g['end']<HAN_MIN_MS: return None,f'het han {dtm.datetime.fromtimestamp(g["end"]/1000,VN):%d/%m %H:%M} (< han toi thieu)'
    return dict(pid=b['id'],loc=tc.LOC[ma],end=g['end'],gia_cuc_bo=tc.so_tien(b['con']),tien_te=tc.TIEN_TE[ma],html=html),None

def ds_giam_sau():
    hn1=NGAY_DUNG-dtm.timedelta(days=1)     # trạng thái "như lúc bài của NGAY_DUNG sinh": không tính chính bài của hôm đó vào danh sách loại trừ
    bai=[b for b in BAI if b.get('loai_tu_sinh')=='giam-sau' and b['ngay']==NGAY_DUNG.isoformat() and isinstance(b.get('khoa_game'),list)]
    if bai:
        ks=bai[0]['khoa_game']; by={h['khoa']:h for h in d['hangs']}
        return [by[k] for k in ks if k in by]
    return t.chon_giam_sau(d['hangs'],th,t.lich_su_giam_sau(t.THU_MUC_BAI,hn1),hn1,slug_loai=t.slug_keo_gan_day(t.THU_MUC_BAI,hn1))
def ds_vua_giam(): return t.chon_vua_giam(d['so'],d['dls'],th,NGAY_DUNG)
def ds_deal_hot(): return t.chon_deal_hot(d['hangs'],th)
MAX_XET_SAP_HET=60
def ds_sap_het():
    """Game bán chạy đang giảm (cùng luật hạng/% giảm/không gói với giảm sâu) có hạn nằm trong [HAN_MIN, HAN_MIN + 2 ngày] theo trang PS Store đúng vùng.
    Xếp theo hạng; xét tối đa MAX_XET_SAP_HET ứng viên; dừng sớm khi đủ TOI_DA_GAME game."""
    ung=[h for h in d['hangs'] if h['khoa'] in th and th[h['khoa']][0]+1<=t.GIAM_SAU_HANG_TOI_DA and h['giam']>=t.GIAM_TOI_THIEU
         and not t._la_goi_nhieu_game(h) and h.get('vnd')]
    ung.sort(key=lambda h:(th[h['khoa']],h['slug'])); ung=t._bo_trung_ten(ung)[:MAX_XET_SAP_HET]
    ra=[]; xa=0; loi=0; xet=0
    for h in ung:
        if len(ra)>=t.TOI_DA_GAME: break
        xet+=1; kq,ly=xac_minh(h)
        if not kq: loi+=1; continue
        if cl.trong_khoang_sap_het(kq['end'],HAN_MIN_MS): ra.append(h)
        else: xa+=1
    print(f'  sap-het: xet {xet}/{len(ung)} ung vien, {len(ra)} hop khoang han, {xa} het sau khoang (> 4 ngay), {loi} khong xac minh/het han < 2 ngay')
    return ra

DA_DUNG_GOC=set()
def tin_gia(loai,ham,uu):
    ten_loai,cum,nhan=LOAI_GIA[loai]
    try: ds=ham()
    except Exception as e: return bo(loai,f'loi chon: {e}')
    if len(ds)<3: return bo(loai,f'chi {len(ds)} game (can >= 3)')
    ok=[]
    for h in ds:
        if len(ok)>=t.TOI_DA_GAME: break
        kq,ly=xac_minh(h)
        if kq: ok.append((h,kq))
        else: print('    loai game',h['ten'][:40],'-',ly)
    # Game đã là "rẻ nhất" của tin khác -> bỏ khỏi DANH SÁCH này (không chọn game rẻ nhì rồi vẫn gọi "rẻ nhất"); số game N đọc/hiện = danh sách sau khi bỏ.
    trung=[x for x in ok if t._ten_goc(x[0]['ten']) in DA_DUNG_GOC]
    if trung: print('    bo khoi danh sach (da la game re nhat cua tin khac):',', '.join(x[0]['ten'][:30] for x in trung))
    ok=[x for x in ok if t._ten_goc(x[0]['ten']) not in DA_DUNG_GOC]
    if len(ok)<3: return bo(loai,f'chi {len(ok)} game con han >= 2 ngay va khong trung tin khac (can >= 3)')
    h,kq=min(ok,key=lambda x:x[0]['vnd'])
    anh=t.url_anh_day_du(h.get('anh'))
    if not t.hop_le_bia(anh): return bo(loai,'game re nhat khong co bia hop le')
    try:
        f=tc.tai_anh(anh,TS,'gia',rong=720)
        tr,shot=nen_tu_trang(kq['html'],kq['pid'])
    except Exception as e: return bo(loai,f'loi tai anh/trailer: {e}')
    DA_DUNG_GOC.add(t._ten_goc(h['ten']))
    hien=so_chu.ten_hien_thi(h['ten'])
    return dict(kieu=loai,mau='do',uu=uu,khoa=f'{loai}:{h["khoa"].split("|")[0]}',loai=ten_loai,nguon=f'PS STORE · {ddmm(d["cap_nhat"])}',
                n=len(ok),cum=cum,giam_min=min(x[0]['giam'] for x in ok),giam_max=max(x[0]['giam'] for x in ok),
                re_nhat=dict(ten=h['ten'],ten_hien=hien,ten_doc=so_chu.ten_doc(hien,h['ten']),gia_vnd=vnd_so(h),gia=t._dong(qd,h['vnd']),giam=h['giam'],vung=h['vung'],ma=h['ma'],
                             khoa=h['khoa'],pid=kq['pid'],loc=kq['loc'],end=kq['end'],gia_cuc_bo=kq['gia_cuc_bo'],tien_te=kq['tien_te']),
                nhan_dong=f'{nhan} · STORE {h["vung"].upper()}',anh_url=[anh],anh_tep=[f'tai-san/{f.name}'],trailer=tr,anh_chup=shot,
                kiem_lai=[dict(ten=x[0]['ten'],pid=x[1]['pid'],loc=x[1]['loc'],gia_vnd=vnd_so(x[0]),gia_cuc_bo=x[1]['gia_cuc_bo'],tien_te=x[1]['tien_te'],endTime=str(x[1]['end'])) for x in ok])

def tin_kho_plus(uu):
    f=pathlib.Path('du-lieu/kho-plus-vao-roi.json')
    try: k=json.load(open(f,encoding='utf-8'))
    except Exception: return bo('kho-plus','khong doc duoc kho-plus-vao-roi.json')
    if str(k.get('ngay',''))[:10]<(NGAY_DUNG-dtm.timedelta(days=1)).isoformat(): return bo('kho-plus',f'du lieu cu ({k.get("ngay")})')
    moi=[g for g in (k.get('vung',{}).get('en-SG',{}).get('moi_vao') or []) if g.get('ten') and not DLC.search(g['ten']) and bai_viet.anh_hop_le(g.get('anh',''))]
    if len(moi)<1: return bo('kho-plus','khong co game moi vao kho')
    moi=moi[:3]
    try: tep=[tc.tai_anh(g['anh'],TS,'kho',rong=720) for g in moi]
    except Exception as e: return bo('kho-plus',f'loi tai anh: {e}')
    ten=[so_chu.ten_hien_thi(t._ten_md(t.gon_ten(g['ten']))) for g in moi]
    return dict(kieu='ps-plus-kho',mau='xanh',uu=uu,khoa=f'ps-plus-kho:{k.get("ngay")}',loai='PS PLUS',nguon=f'PLAYSTATION SG · {ddmm(k["ngay"])}',n_moi=len(k['vung']['en-SG']['moi_vao']),
                ten_game=ten,ten_doc=[so_chu.ten_doc(x) for x in ten[:2]],ten_noi=ten[:2],anh_url=[g['anh'] for g in moi],anh_tep=[f'tai-san/{f.name}' for f in tep],
                nhan_dong='KHO GAME PS PLUS',bai=None,tieu_de_bai=None,pid=None,loc='en-sg',trailer=[],anh_chup=[])

def tin_sale(uu):
    """Đợt sale lớn đang chạy / sắp hết ở ngày đăng (du-lieu/lich-sale.json); ảnh = bìa game bán chạy đứng đầu đang giảm (sự kiện không có ảnh riêng)."""
    try: ls=json.load(open('du-lieu/lich-sale.json',encoding='utf-8'))
    except Exception: return bo('sale','khong doc duoc lich-sale.json')
    dang=NGAY_DANG.isoformat()
    ev=[e for e in ls.get('su_kien',[]) if e.get('bat_dau','9')<=dang<=e.get('ket_thuc','0') and e.get('nguon_url')]
    if not ev: return bo('sale',f'khong co dot sale dang chay o {dang}')
    e=min(ev,key=lambda x:x['ket_thuc'])
    top=sorted([h for h in d['hangs'] if h['khoa'] in th and t.hop_le_bia(t.url_anh_day_du(h.get('anh')))],key=lambda h:th[h['khoa']])
    if not top: return bo('sale','khong co bia game bat chay')
    try: f=tc.tai_anh(t.url_anh_day_du(top[0]['anh']),TS,'sale',rong=720)
    except Exception as ex: return bo('sale',f'loi tai anh: {ex}')
    ten=re.sub(r'\s*\([^)]*\)\s*$','',e['ten']).strip()
    return dict(kieu='sale',mau='vang',uu=uu,khoa=f'sale:{ten}',loai='ĐỢT SALE',nguon=f'PS STORE · {ddmm(dang)}'.upper(),tit=ten[:40],
                moc=f'HẾT {ddmm(e["ket_thuc"])}',anh_url=[t.url_anh_day_du(top[0]['anh'])],anh_tep=[f'tai-san/{f.name}'],bai=None,tieu_de_bai=e['ten'],
                nhan_dong='ĐANG GIẢM GIÁ',dong='sangame.com.vn · Cho sale',trailer=[],anh_chup=[])

# ---------------------------------------------------------------- chọn
def ung_vien():
    yield from ung_tin_nong(1.0)
    r=tin_gia('giam-sau',ds_giam_sau,2.0)
    if r: yield r
    r=tin_kho_plus(3.0)
    if r: yield r
    r=tin_sale(4.0)
    if r: yield r
    phu=[('vua-giam',ds_vua_giam,5.0),('deal-hot',ds_deal_hot,5.1)]
    if NGAY_DANG.weekday()==4: phu.reverse()
    for loai,ham,uu in phu:
        r=tin_gia(loai,ham,uu)
        if r: yield r
    r=tin_gia('sap-het',ds_sap_het,6.0)      # DỰ PHÒNG: sau mọi loại khác, chỉ tới khi ngày thiếu tin (ung_vien lười)
    if r: yield r

chon=cl.chon_ba(ung_vien())
for r in chon: print('  CHON',r['kieu'],r['khoa'])
ORDER={'xanh':0,'do':1,'vang':2}
chon.sort(key=lambda r:(ORDER[r['mau']],r['uu']))
for r in chon:
    r.pop('uu',None)
    if 'kiem_lai' not in r: r['kiem_lai']=[]
out=dict(ngay_dang=NGAY_DANG.isoformat(),ngay_dung=NGAY_DUNG.isoformat(),sha_du_lieu=SHA,du_lieu_cap_nhat=d['cap_nhat'],han_toi_thieu_ms=HAN_MIN_MS,
         thieu=3-len(chon),tin=chon,loai_bo=BO)
json.dump(out,open(a.ra,'w',encoding='utf-8'),ensure_ascii=False,indent=1)
print(f'{len(chon)}/3 tin ->',a.ra)
if len(chon)<3:
    print('KHONG DU 3 TIN -> bo khung')
    sys.exit(3)
