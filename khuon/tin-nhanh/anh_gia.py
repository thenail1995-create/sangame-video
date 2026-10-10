# Chặn ảnh/khung GIỮ CHỖ của PS Store (nền vàng phẳng, chữ "PLACEHOLDER SCREENSHOTS") — lỗi thật Top 5 11/10.
# Hai lớp: (1) mảng màu phẳng (>55% điểm ảnh trong 1 dải màu hẹp + ít cạnh); (2) OCR tesseract thấy PLACEHOLDER/SCREENSHOT/COMING SOON/TBA.
import pathlib,re,shutil,subprocess,tempfile
from PIL import Image
CAM=re.compile(r'PLACE\s*HOLDER|SCREEN\s*SHOTS?|COMING\s+SOON|\bT\.?B\.?A\.?\b',re.I)
def co_ocr(): return shutil.which('tesseract') is not None
def phang(img):
    """True nếu ảnh gần như một mảng màu phẳng. img: PIL.Image."""
    im=img.convert('RGB').resize((64,36)); px=list(im.getdata())
    nhom={}
    for r,g,b in px: k=(r//24,g//24,b//24); nhom[k]=nhom.get(k,0)+1
    chiem=max(nhom.values())/len(px)
    L=im.convert('L'); w,h=L.size; d=L.load(); canh=sum(abs(d[x,y]-d[x+1,y])+abs(d[x,y]-d[x,y+1]) for x in range(w-1) for y in range(h-1))/((w-1)*(h-1))
    return chiem>0.55 and canh<6
def o_toi_phang(img):
    """True nếu có HỘP TỐI ĐỒNG MÀU hình chữ nhật cỡ vừa (4-30% khung) nằm sẵn trong nguồn — khung UI / ô phụ đề (Tin nhanh 12/10: hộp đen bo góc
    góc dưới trái nền F1 25). Khối 8x8 'tối phẳng' = TB < 25, lệch < 2; lấy thành phần liền kề lớn nhất; phải ĐẶC (>= 90% hình chữ nhật bao)
    và có viền sáng hơn rõ rệt xung quanh (>= 25 mức) — cảnh tối tự nhiên không đặc, không có viền sắc."""
    L=img.convert('L').resize((270,480)); w,h=L.size; d=L.load(); gw,gh=w//8,h//8
    ok=[[False]*gw for _ in range(gh)]; mean=[[0.0]*gw for _ in range(gh)]
    for gy in range(gh):
        for gx in range(gw):
            v=[d[gx*8+i,gy*8+j] for i in range(0,8,2) for j in range(0,8,2)]; m=sum(v)/len(v); mean[gy][gx]=m
            ok[gy][gx]=m<25 and (sum((x-m)**2 for x in v)/len(v))**0.5<2
    seen=[[False]*gw for _ in range(gh)]; best=None
    for sy in range(gh):
        for sx in range(gw):
            if not ok[sy][sx] or seen[sy][sx]: continue
            st=[(sy,sx)]; seen[sy][sx]=True; cells=[]
            while st:
                y,x=st.pop(); cells.append((y,x))
                for dy,dx in ((1,0),(-1,0),(0,1),(0,-1)):
                    ny,nx=y+dy,x+dx
                    if 0<=ny<gh and 0<=nx<gw and ok[ny][nx] and not seen[ny][nx]: seen[ny][nx]=True; st.append((ny,nx))
            if best is None or len(cells)>len(best): best=cells
    if not best: return False
    ys=[c[0] for c in best]; xs=[c[1] for c in best]; y0,y1,x0,x1=min(ys),max(ys),min(xs),max(xs)
    bb=(y1-y0+1)*(x1-x0+1); frac=len(best)/(gw*gh)
    if not (0.04<=frac<=0.30) or len(best)/bb<0.90: return False
    anel=[mean[y][x] for y in range(max(0,y0-2),min(gh,y1+3)) for x in range(max(0,x0-2),min(gw,x1+3)) if not (y0<=y<=y1 and x0<=x<=x1)]
    tr=sum(mean[y][x] for y,x in best)/len(best)
    return bool(anel) and sum(anel)/len(anel)-tr>=25
def chu_cam(path):
    """Chữ cấm OCR thấy trong ảnh (chuỗi) hoặc None; không có tesseract -> None."""
    if not co_ocr(): return None
    r=subprocess.run(['tesseract',str(path),'stdout','--psm','11'],capture_output=True,timeout=60)
    m=CAM.search((r.stdout or b'').decode('utf-8','ignore')); return m.group(0) if m else None
def ly_do(path,toi=True):
    """Lý do ảnh bị loại (str) hoặc None nếu dùng được."""
    try:
        im=Image.open(path)
        if phang(im): return 'mang mau phang (anh giu cho)'
        if toi and o_toi_phang(im): return 'co mang toi dong mau lon (khung UI/o phu de trong nguon)'
    except Exception as e: return f'khong doc duoc anh: {e}'
    c=chu_cam(path)
    return f'co chu cam «{c}»' if c else None
def khung_video(src,t,ra):
    subprocess.run(['ffmpeg','-v','error','-y','-ss',f'{t:.2f}','-i',str(src),'-frames:v','1','-vf','scale=960:-2',str(ra)],check=True,timeout=120)
def ly_do_video(src,t,toi=True):
    with tempfile.TemporaryDirectory() as d:
        f=pathlib.Path(d)/'k.png'
        try: khung_video(src,t,f)
        except Exception as e: return f'khong lay duoc khung: {e}'
        return ly_do(f,toi)
