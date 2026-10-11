#!/usr/bin/env python3
# C2 — Từ tin-chon.json (chon-tin.py) sinh: tin.json (lời + chỉ số từ + dữ liệu thẻ), tai-san/trailer.json, nen-nguon.json (nguồn nền từng cảnh),
# kiem-lai.json (để máy đăng kiểm lại giá/hạn), loi-dang.json (tít/mô tả/hashtag cho manifest). Mọi chữ/số lấy từ dữ liệu; không viết tay.
#   python3 sinh-tin.py [tin-chon.json]
# Lời đọc: số viết bằng CHỮ (so_chu.py), không còn chữ số nào trong lời (kiểm lại ở cuối), ngày = ngày ĐĂNG.
import datetime as dtm,json,pathlib,re,sys
T=pathlib.Path(__file__).resolve().parent; sys.path.insert(0,str(T))
import so_chu as sc
src=pathlib.Path(sys.argv[1]) if len(sys.argv)>1 else T/'tin-chon.json'
C=json.load(open(src,encoding='utf-8'))
ND=dtm.date.fromisoformat(C['ngay_dang'])
TIN_MOT=['một','hai','ba']
TOI_DA=dict(tit=40,tieu=46,nguon=34,ten_re=30,tong_loi=520)
cat=lambda s,n:s if len(s)<=n else (s[:n].rsplit(' ',1)[0] if ' ' in s[:n] else s[:n]).rstrip(' ,;:-–')   # cat theo TU, khong de chu cut cut (Top 5 'Complet…')

def chi_so(loi,cum):
    """Chỉ số (theo loi.split()) của từ ĐẦU cụm `cum` trong `loi` — full.html bám mốc theo chỉ số này, không tìm chữ cứng."""
    pre=loi.split(cum)[0]
    return len(pre.split())

def xanh(r,k):
    doc=r['ten_doc']; n=r['n_moi']; nc=sc.so_ra_chu(n)
    dau='Kho game PS Plus vừa thêm' if r['kieu']=='ps-plus-kho' else 'PS Plus tháng này thêm'
    if len(doc)>=2:
        loi=f'{dau} {doc[0]} và {doc[1]}.' if n<=2 else f'{dau} {nc} game, có {doc[0]} và {doc[1]}.'
    elif len(doc)==1: loi=f'{dau} {nc} game, có {doc[0]}.'
    else: loi=f'{dau} {nc} game mới.'
    ten_game=r['ten_game'] or [f'{n} game mới',('trong danh sách tháng này' if r['kieu']!='ps-plus-kho' else 'vào kho PS Plus')]
    tieu=f'{dau} '+', '.join(r['ten_noi']) if r['ten_noi'] else f'{dau} {n} game'
    if len(tieu)>TOI_DA['tieu']: tieu=f'{dau} {n} game'
    ci=[]
    full=f'Tin {TIN_MOT[k]}: '+loi
    pos=len(f'Tin {TIN_MOT[k]}:'.split())
    for d_ in doc:
        pre=loi.split(d_)[0]; ci.append(pos+len(pre.split()))
    return dict(loai=r['loai'],mau='xanh',nguon=r['nguon'],tieu=tieu,tit=f'{dau} {n} game',nhan_dong=r['nhan_dong'],anh=r['anh_tep'][:3],ten_game=ten_game[:3],
                loi=full,chi_so=dict(ten=ci),kiem=dict(ten=list(doc),so=[])),loi

def gia(r,k):
    x=r['re_nhat']; ten_chu=x['ten_doc']
    kg=sc.so_ra_chu(x['giam']); gc=sc.so_ra_chu(x['gia_vnd']); nc=sc.so_ra_chu(r['n'])
    loi=f'{nc} game bán chạy {r["cum"]}. Rẻ nhất {ten_chu}, giảm {kg} phần trăm, {gc} ở store {x["vung"]}.'   # dấu phẩy ngay trước giá = khoảng nghỉ cho tiếng đóng dấu giá (A8)
    pos=len(f'Tin {TIN_MOT[k]}:'.split())
    i_ten=pos+len(loi.split(ten_chu)[0].split())
    i_gia=pos+len(loi.split(gc)[0].split())
    kt={'giam-sau':'giảm','vua-giam':'vừa giảm','deal-hot':'đang giảm'}[r['kieu']]
    rg=f'{r["giam_min"]}–{r["giam_max"]}%' if r['giam_min']!=r['giam_max'] else f'{r["giam_max"]}%'
    tit=f'{r["n"]} game bán chạy {kt} {rg}'
    return dict(loai=r['loai'],mau='do',nguon=r['nguon'],tieu=cat(tit,TOI_DA['tieu']),tit=cat(tit,TOI_DA['tit']),ten_re=cat(x['ten_hien'],TOI_DA['ten_re']),
                nhan_dong=r['nhan_dong'],gia=x['gia'],giam=x['giam'],anh=r['anh_tep'][:1],
                loi=f'Tin {TIN_MOT[k]}: '+loi,chi_so=dict(ten=i_ten,gia=i_gia),kiem=dict(ten=[ten_chu],so=[f'{kg} phần trăm',gc],vung=x['ma'],       # B4: ma vung de D3 kiem vung doc; B5: the_gia = ban ghi kiem_lai cua THE nay (doi chieu theo pid+loc)
                          the_gia=dict(pid=x['pid'],loc=x['loc'],gia_vnd=x['gia_vnd'],gia_cuc_bo=x['gia_cuc_bo'],tien_te=x['tien_te'],endTime=str(x['end'])))),loi

def vang(r,k):
    tit=r['tit']; doc_tit=re.sub(r'[:;]','',sc.doc_van_ban(tit,ND)); moc=r.get('moc')
    loi=doc_tit
    ci=None; so=[]
    if moc:
        doc_moc=re.sub(r'[:;]','',sc.doc_van_ban(moc,ND))
        if sc.bo_dau(doc_moc) in sc.bo_dau(doc_tit): moc=None     # nhãn đã nằm trong tít: không đọc lại
        else:
            loi=f'{doc_tit}, {doc_moc}'
            ci=len(f'Tin {TIN_MOT[k]}:'.split())+len(doc_tit.split()); so=[doc_moc]
    if not loi.endswith('.'): loi+='.'
    d=dict(loai=r['loai'],mau='vang',nguon=r['nguon'],tieu=cat(tit,TOI_DA['tieu']),tit=cat(tit,TOI_DA['tit']),dong=r['dong'],nhan_dong=r['nhan_dong'],anh=r['anh_tep'][:1],
           loi=f'Tin {TIN_MOT[k]}: '+loi,chi_so=dict(moc=ci),kiem=dict(ten=[doc_tit],so=[],ngay=so))
    if moc: d['moc']=moc
    return d,loi

TIN=[]
for k,r in enumerate(C['tin']):
    f={'ps-plus-thang':xanh,'ps-plus-kho':xanh,'giam-sau':gia,'vua-giam':gia,'deal-hot':gia,'bai':vang,'sale':vang}[r['kieu']]
    d,_=f(r,k); d['khoa']=r['khoa']; d['kieu']=r['kieu']
    TIN.append(d)
tong_loi=sum(len(x['loi']) for x in TIN)
loi_loi=[]
for x in TIN:
    if re.search(r'\d',re.sub(r'\bF1\b','',x['loi'])):   # F1 (tên giải đua) giữ nguyên như bản 10/10
         loi_loi.append(f'loi con chu so: {x["loi"]}')
    for kh,gh in (('tit','tit'),('tieu','tieu'),('nguon','nguon')):
        if len(x[kh])>TOI_DA[gh]: loi_loi.append(f'{kh} qua dai ({len(x[kh])}>{TOI_DA[gh]}): {x[kh]}')
if tong_loi>TOI_DA['tong_loi']: loi_loi.append(f'tong loi {tong_loi} ky tu > {TOI_DA["tong_loi"]} (cat credit)')
if loi_loi: print('SINH TIN LOI:\n - '+'\n - '.join(loi_loi)); sys.exit(1)

D=dict(ngay_dang=C['ngay_dang'],ngay_dung=C['ngay_dung'],sha_du_lieu=C['sha_du_lieu'],ngay=sc.ngay_ddmm(ND),thu=sc.thu_cua(ND),ngay_doc=sc.ngay_doc(ND),tin=TIN)
json.dump(D,open(T/'tin.json','w',encoding='utf-8'),ensure_ascii=False,indent=1)

# ---- nguồn nền từng cảnh (nen-tin.py đọc nen-nguon.json) + trailer.json ----
(T/'tai-san').mkdir(exist_ok=True)
TRJ={}; nguon={'mo':[],'ket':[]}; cuoi_v=None; cuoi_a=None
for k,r in enumerate(C['tin'],1):
    nen=r.get('trailer') or []
    if nen:
        TRJ[f't{k}']=nen; s=('v',f't{k}'); cuoi_v=s; sl=2
    else:
        tep=(r.get('anh_chup') or r['anh_tep'])[0]; s=('a',pathlib.Path(tep).name); cuoi_a=s; sl=1
    nguon['mo'].append([s[0],s[1],1]); nguon[f't{k}']=[[s[0],s[1],sl]]
nguon['ket']=[list(cuoi_v or cuoi_a)+[1]]
json.dump(TRJ,open(T/'tai-san/trailer.json','w'),indent=1)
json.dump(nguon,open(T/'nen-nguon.json','w'),indent=1)

# ---- kiem-lai.json + loi-dang.json ----
kl=[]
for r in C['tin']: kl+=r.get('kiem_lai') or []
json.dump(kl,open(T/'kiem-lai.json','w',encoding='utf-8'),ensure_ascii=False,indent=1)
tits=[x['tit'] for x in TIN]; td=f'Tin nhanh PlayStation {D["ngay"]}:'
for i in range(len(tits)):
    thu=td+' '+' | '.join(tits[:i+1])
    if len(thu)<=100: td_ok=thu
tieu_de=td_ok if len(tits) and len(td+' '+tits[0])<=100 else td
dong=[f'Bản tin sáng Săn Game, {D["thu"]} {D["ngay"]}:']
for i,x in enumerate(TIN,1): dong.append(f'{i}. {x["loai"]}: {x["tieu"]}.')
for x in TIN:
    if x['mau']=='do': dong.append(f'{x["loai"].capitalize()}: rẻ nhất {x["ten_re"]}, {x["gia"]} ở {x["nhan_dong"].split("· ")[-1].title()} (giảm {x["giam"]}%).')
dong.append('Tra giá mọi game ở 6 vùng PS Store: https://sangame.com.vn/')
json.dump(dict(tieu_de=tieu_de,mo_ta='\n'.join(dong),hashtag=['#SănGame','#PlayStation','#PS5'],link='https://sangame.com.vn/'),open(T/'loi-dang.json','w',encoding='utf-8'),ensure_ascii=False,indent=1)
print(f'tin.json: {len(TIN)} tin, loi {tong_loi} ky tu (~{tong_loi*0.372:.0f} credit) + mo/ket')
for x in TIN: print(' ',x['mau'],x['loai'],'|',x['tit'],'|',x['loi'])
