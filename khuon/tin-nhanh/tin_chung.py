# Hàm mạng + đọc trang PS Store dùng chung cho chon-tin.py (C1). Mọi hàm ném ngoại lệ khi lỗi mạng -> người gọi bỏ ứng viên đó.
# Ảnh Sony / trailer chỉ TẢI LÚC DỰNG vào tai-san/ (bị .gitignore chặn, không bao giờ vào repo công khai).
import hashlib,json,pathlib,re,subprocess,time,urllib.request,sys
sys.path.insert(0,str(pathlib.Path(__file__).resolve().parent)); import anh_gia

UA="Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0 Safari/537.36"
LOC={'SG':'en-sg','HK':'en-hk','IN':'en-in','ID':'en-id','US':'en-us','TH':'en-th'}
TIEN_TE={'SG':'SGD','HK':'HKD','IN':'INR','ID':'IDR','US':'USD','TH':'THB'}

def mo(url,timeout=40,thu_lai=2):
    for k in range(thu_lai+1):
        try:
            return urllib.request.urlopen(urllib.request.Request(url,headers={'User-Agent':UA}),timeout=timeout)
        except Exception:
            if k==thu_lai: raise
            time.sleep(1.5*(k+1))

_cache={}
def lay_trang(loc,pid):
    k=(loc,pid)
    if k not in _cache:
        _cache[k]=mo(f'https://store.playstation.com/{loc}/product/{pid}').read().decode('utf-8','ignore')
    return _cache[k]

def so_tien(s):
    """'HK$148.00' -> 148.0 ; 'Rp 356,532' -> 356532.0 ; 'SGD43.96' -> 43.96. None nếu không đọc được."""
    if not isinstance(s,str): return None
    t=re.sub(r'[^\d.,]','',s)
    if not t: return None
    if ',' in t and '.' in t: t=t.replace(',','')
    elif ',' in t:
        t=t.replace(',','') if re.fullmatch(r'\d{1,3}(,\d{3})+',t) else t.replace(',','.')
    try: return float(t)
    except ValueError: return None

def cac_gia_trang(html):
    """Mọi khối giá trong trang: [{base, disc, disc_so, tien_te, endTime(ms hoặc None)}]."""
    ra=[]
    for m in re.finditer(r'"__typename":"Price","basePrice":"([^"]*)","discountedPrice":"([^"]*)"[^{}]*?"endTime":(null|"(\d+)")[^{}]*?"discountedValue":(\d+)[^{}]*?"currencyCode":"([A-Z]+)"',html):
        ra.append(dict(base=m.group(1),disc=m.group(2),end=int(m.group(4)) if m.group(4) else None,disc_so=int(m.group(5))/100.0,tien_te=m.group(6)))
    return ra

def gia_khop(html,con,ma):
    """Khối giá của TRANG ĐÚNG VÙNG khớp giá đang giảm trong dữ liệu (con = chuỗi trong sổ, vd 'HK$148.00'). None nếu không khớp
    (giá lệch > 1% hoặc khác loại tiền) — khi đó KHÔNG được coi là deal xác minh được."""
    can=so_tien(con)
    if can is None: return None
    ung=[g for g in cac_gia_trang(html) if g['tien_te']==TIEN_TE.get(ma) and g['end']]
    tot=[g for g in ung if g['disc']==con] or [g for g in ung if abs(g['disc_so']-can)<=max(0.011,can*0.01)]
    return tot[0] if tot else None

def trailers(html):
    return list(dict.fromkeys(re.findall(r'"type":"VIDEO","url":"(https://vulcan\.dl\.playstation\.net[^"]+\.mp4)"',html)))

def anh_chup(html):
    return list(dict.fromkeys(re.findall(r'"role":"SCREENSHOT","type":"IMAGE","url":"([^"]+)"',html)))

def thong_trailer(u):
    """(w, h, giây) đọc đầu file bằng ffprobe; None nếu không đọc được."""
    try:
        r=subprocess.run(['ffprobe','-v','error','-select_streams','v','-show_entries','stream=width,height:format=duration','-of','csv=p=0',u],capture_output=True,text=True,timeout=90).stdout.split()
        w,h=map(int,r[0].split(',')[:2]); return w,h,float(r[1])
    except Exception:
        return None

def xep_trailer(urls,toi_da=3):
    """H21: phân giải cao nhất rồi dài nhất (nhưng trailer > 240 s xếp sau: tải + dò cảnh quá lâu). Trả [{u,w,h,d}] tối đa toi_da."""
    ra=[]
    for u in urls[:6]:
        t=thong_trailer(u)
        if not (t and t[2]>=8): continue
        ld=anh_gia.ly_do_video(u,t[2]*0.3)     # khung 30% trailer: giu cho / chu cam -> bo trailer nay
        if ld: print('  bo trailer',u[-30:],'-',ld); continue
        ra.append(dict(u=u,w=t[0],h=t[1],d=round(t[2],3)))
    ra.sort(key=lambda x:(-x['h'],x['d']>240,-x['d']))   # H21 + trailer > 4 phut bi xep sau (Mac: tai 900 s video ngon 15 phut/nen)
    return ra[:toi_da]

def tai_anh(url,thu_muc,tien_to='a',rong=None):
    """Tải ảnh về thu_muc, tên theo băm URL; trả đường dẫn. Kiểm nhỏ: >= 3 KB và là ảnh (PNG/JPEG/WEBP)."""
    thu_muc=pathlib.Path(thu_muc); thu_muc.mkdir(parents=True,exist_ok=True)
    u=url+(('&' if '?' in url else '?')+f'w={rong}') if rong else url
    b=mo(u).read()
    if len(b)<3000: raise ValueError(f'anh qua nho ({len(b)} B): {url}')
    if b[:8]==b'\x89PNG\r\n\x1a\n': ext='png'
    elif b[:3]==b'\xff\xd8\xff': ext='jpg'
    elif b[:4]==b'RIFF' and b[8:12]==b'WEBP': ext='webp'
    else: raise ValueError(f'khong phai anh: {url}')
    f=thu_muc/f'{tien_to}-{hashlib.sha1(u.encode()).hexdigest()[:10]}.{ext}'
    f.write_bytes(b)
    ld=anh_gia.ly_do(f)
    if ld: f.unlink(); raise ValueError(f'anh bi loai ({ld}): {url}')   # anh giu cho cua PS Store
    return f
