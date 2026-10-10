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
def chu_cam(path):
    """Chữ cấm OCR thấy trong ảnh (chuỗi) hoặc None; không có tesseract -> None."""
    if not co_ocr(): return None
    r=subprocess.run(['tesseract',str(path),'stdout','--psm','11'],capture_output=True,text=True,timeout=60)
    m=CAM.search(r.stdout or ''); return m.group(0) if m else None
def ly_do(path):
    """Lý do ảnh bị loại (str) hoặc None nếu dùng được."""
    try:
        if phang(Image.open(path)): return 'mang mau phang (anh giu cho)'
    except Exception as e: return f'khong doc duoc anh: {e}'
    c=chu_cam(path)
    return f'co chu cam «{c}»' if c else None
def khung_video(src,t,ra):
    subprocess.run(['ffmpeg','-v','error','-y','-ss',f'{t:.2f}','-i',str(src),'-frames:v','1','-vf','scale=960:-2',str(ra)],check=True,timeout=120)
def ly_do_video(src,t):
    with tempfile.TemporaryDirectory() as d:
        f=pathlib.Path(d)/'k.png'
        try: khung_video(src,t,f)
        except Exception as e: return f'khong lay duoc khung: {e}'
        return ly_do(f)
