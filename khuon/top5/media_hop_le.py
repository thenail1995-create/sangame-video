# Phat hien ANH GIU CHO cua PS Store ("PLACEHOLDER SCREENSHOTS", nen vang phang chu den) - LOI-SAI K18.
#   la_giu_cho(duong_dan_anh) -> ly do (str) neu la anh giu cho, nguoc lai None
#   ocr_chu(duong_dan_anh)    -> chu doc duoc (tesseract); None neu may khong co tesseract
# Hai lop: (1) OCR tim PLACEHOLDER / SCREENSHOT / COMING SOON / TBA / NOT AVAILABLE ; (2) mang mau phang: > 55% diem anh trong 1 dai mau hep
# (luong tu hoa 32 muc/kenh): anh giu cho that do 84-88% (chu to van co canh 7-9); canh trailer toi tu nhien chi 61% - bat ca anh giu cho khong co chu.
import re,shutil,subprocess,sys
MAU_CHU=re.compile(r'place\s*holder|screen\s*shots?|coming\s+soon|\btba\b|not\s+available|image\s+unavailable|no\s+image',re.I)
def ocr_chu(p):
    if not shutil.which('tesseract'): return None
    try:
        r=subprocess.run(['tesseract',str(p),'stdout','--psm','6','-l','eng'],capture_output=True,text=True,timeout=60)
    except Exception: return None
    return r.stdout
def phang(p):
    """(ty le diem anh trong dai mau pho bien nhat, mat do canh trung binh)"""
    import numpy as np
    from PIL import Image
    im=Image.open(p).convert('RGB'); im.thumbnail((160,160)); a=np.asarray(im).astype(int)
    q=(a[:,:,0]//32)*64+(a[:,:,1]//32)*8+(a[:,:,2]//32); top=np.bincount(q.ravel()).max()/q.size
    g=np.asarray(im.convert('L')).astype(int); canh=(np.abs(np.diff(g,axis=0)).mean()+np.abs(np.diff(g,axis=1)).mean())/2
    return top,canh
def la_giu_cho(p):
    t=ocr_chu(p)
    if t and MAU_CHU.search(t): return f"OCR thay chu giu cho: '{MAU_CHU.search(t).group(0)}'"
    top,canh=phang(p)
    # nguong 0,55 + canh thap bat nham canh xe toi trong trailer Mafia (61%, canh 1,3); anh giu cho that 84-88%
    if top>0.75: return f'mang mau phang ({top*100:.0f}% diem anh 1 dai mau)'
    return None
if __name__=='__main__':
    for f in sys.argv[1:]: print(f,'->',la_giu_cho(f) or 'hop le')
