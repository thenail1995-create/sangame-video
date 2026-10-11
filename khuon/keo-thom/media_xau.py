# Chan media XAU lay tu trang PS Store (Top 5 11/10: nhieu game dung ANH GIU CHO nen vang phang + chu "PLACEHOLDER SCREENSHOTS", may lay lam nen).
# 2 lop: (1) OCR tesseract tim chu PLACEHOLDER / SCREENSHOT / COMING SOON / TBA; (2) mang mau PHANG (>55% diem anh dung 1 dai mau hep + it canh).
# Dung o chon-keo.py (trailer + anh cua game), nen08.py (tung doan trailer truoc khi dung), kiem/kiem-tat-ca.py (khung nen cua moi canh sau dung).
# Can `tesseract` trong PATH (CI: apt-get install tesseract-ocr). Thieu / loi tesseract = 'khong kiem duoc' = LOI (fail-closed); stdout rong voi ma thoat 0 = khong thay chu (hop le); KHONG_OCR=1 chi de thu may.
import os,re,shutil,subprocess,tempfile
import numpy as np
from PIL import Image
BAN=re.compile(r'placeholder|screenshots?\b|coming\s*soon|\btba\b|to\s*be\s*announced|image\s*not\s*available',re.I)
class OcrLoi(Exception): pass
def ocr(duong):
    """'' (tesseract thoat 0, khong co chu) la HOP LE. Khong chay duoc / ma thoat != 0 / exception -> OcrLoi (khong kiem duoc != khong thay)."""
    if os.environ.get('KHONG_OCR')=='1': return ''
    if not shutil.which('tesseract'): raise OcrLoi('THIEU tesseract (apt-get install tesseract-ocr / brew install tesseract)')
    try: r=subprocess.run(['tesseract',str(duong),'stdout','--psm','11','-l','eng'],capture_output=True,timeout=60)
    except Exception as e: raise OcrLoi(f'tesseract loi: {e}')
    if r.returncode!=0: raise OcrLoi(f'tesseract ma thoat {r.returncode}: {r.stderr.decode("utf-8","ignore")[:100]}')
    return r.stdout.decode('utf-8','ignore')
def phang(duong):
    """True neu >55% diem anh nam trong 1 o mau hep (luong tu 16 muc/kenh) va do doc canh thap — anh nen phang / man mau tron."""
    a=np.asarray(Image.open(duong).convert('RGB').resize((320,180)),dtype=np.int16)
    q=(a//16).reshape(-1,3); ma=q[:,0]*256+q[:,1]*16+q[:,2]; top=np.bincount(ma).max()/len(ma)
    g=np.abs(np.diff(a.mean(axis=2),axis=1)).mean()
    return bool(top>0.55 and g<6)
def kiem_anh(duong):
    """-> ly do (str) neu anh XAU, None neu on."""
    if phang(duong): return 'mang mau phang'
    try: m=BAN.search(ocr(duong))
    except OcrLoi as e: return f'khong kiem duoc OCR: {e}'     # loai media / TRUOT phep kiem
    return f'co chu «{m.group(0)}»' if m else None
def khung(video,t,ra):
    subprocess.run(['ffmpeg','-v','error','-y','-ss',f'{t:.2f}','-i',str(video),'-frames:v','1',str(ra)],check=True); return ra
def kiem_video_o(video,ts):
    """-> [(t, ly do)] cac thoi diem XAU trong video"""
    xau=[]
    with tempfile.TemporaryDirectory() as d:
        for t in ts:
            ly=kiem_anh(khung(video,t,os.path.join(d,'k.png')))
            if ly: xau.append((round(t,2),ly))
    return xau
