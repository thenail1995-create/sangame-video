# Test tin_chung (Sol P1 Tin nhanh): gia/han/media CHI theo pid, khong quet toan trang.  python3 -m pytest khuon/tin-nhanh/test_tin_chung.py
import json,pathlib,sys,unittest
T=pathlib.Path(__file__).resolve().parent; sys.path.insert(0,str(T))
import tin_chung as tc
PID='UP1001-PPSA36393_00-MAFIA1DEPS500000'; KHAC='UP1001-CUSA18097_00-MAFIAONEREMASTER'; END='1792594740000'
def cta(pid,chuoi,value,end=END,tien='HKD'):
    return {f'GameCTA:ADD_TO_CART:ADD_TO_CART:{pid}-H002:OUTRIGHT':{'price':{'basePrice':'HK$318.00','discountedPrice':chuoi,'basePriceValue':31800,'discountedValue':value,'currencyCode':tien,'endTime':end}}}
def trang(*cache): return ''.join('<script id="env:a" type="application/json">'+json.dumps({'cache':c})+'</script>' for c in cache)
class GiaKhop(unittest.TestCase):
    def test_khoi_dung_pid(self):
        g=tc.gia_khop(trang(cta(PID,'HK$47.70',4770)),'HK$47.70','HK',PID); self.assertEqual((g['disc_so'],g['tien_te'],g['end']),(47.7,'HKD',int(END)))
    def test_trang_chi_co_khoi_gia_mang_pid_khac_thi_khong_nhan(self):   # code cu quet toan trang: nhan khoi game goi y
        self.assertIsNone(tc.gia_khop(trang(cta(KHAC,'HK$47.70',4770)),'HK$47.70','HK',PID))
    def test_khong_muon_han_cua_khoi_khac_khi_khoi_pid_khong_co_han(self):
        self.assertIsNone(tc.gia_khop(trang(cta(PID,'HK$47.70',4770,end=None),cta(KHAC,'HK$47.70',4770)),'HK$47.70','HK',PID))
    def test_lech_gia_hoac_khac_tien_te_thi_loai(self):
        h=trang(cta(PID,'HK$47.70',4770)); self.assertIsNone(tc.gia_khop(h,'HK$60.00','HK',PID)); self.assertIsNone(tc.gia_khop(h,'HK$47.70','SG',PID))
class Media(unittest.TestCase):
    def test_media_chi_theo_product_pid(self):
        v=lambda u:{'type':'VIDEO','role':'PREVIEW','url':f'https://vulcan.dl.playstation.net/img/{u}.mp4'}
        s=lambda u:{'type':'IMAGE','role':'SCREENSHOT','url':f'https://image.api.playstation.com/{u}.jpg'}
        h=trang({f'Product:{PID}':{'media':[s('dung')],'personalizedMeta':{'media':[v('dung')]}},f'Product:{KHAC}':{'media':[v('khac'),s('khac')]}})
        self.assertEqual([u[-8:] for u in tc.trailers(h,PID)],['dung.mp4']); self.assertEqual([u[-8:] for u in tc.anh_chup(h,PID)],['dung.jpg'])
        self.assertEqual((tc.trailers(h,'X-Y'),tc.anh_chup(h,'X-Y')),([],[]))
if __name__=='__main__': unittest.main()
