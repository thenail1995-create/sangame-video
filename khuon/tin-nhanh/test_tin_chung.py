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
class VungUkraine(unittest.TestCase):      # 15/10: UA = vung THAM KHAO (khong the o VN): co bang tra, KHONG bao gio la deal
    def test_bang_tra(self):
        self.assertEqual(tc.LOC['UA'],'uk-ua'); self.assertEqual(tc.TIEN_TE['UA'],'UAH'); self.assertEqual(set(tc.LOC),set(tc.TIEN_TE))
        for ma,loc in tc.LOC.items():
            if ma!='UA': self.assertEqual(loc,'en-'+ma.lower())
        self.assertEqual(set(tc.VUNG_THAM_KHAO),{'IN','UA'})
    def test_nhan_kiem_lai_ua_khong_loi_key(self):
        sys.path.insert(0,str(T.parent.parent/'cong-cu')); import sau_manifest_chung as sm
        self.assertEqual(sm.VUNG_LOC['UA'],'uk-ua'); self.assertEqual({k:v for k,v in sm.VUNG_LOC.items() if k!='UA'},{k:v for k,v in tc.LOC.items() if k not in ('UA',)})
    def test_xac_minh_chan_ua_du_re_nhat(self):
        import ast,types
        def mang(*a): raise AssertionError('khong duoc goi mang cho vung tham khao')
        src=(T/'chon-tin.py').read_text(encoding='utf-8'); ns=dict(tc=types.SimpleNamespace(VUNG_THAM_KHAO=tc.VUNG_THAM_KHAO,LOC=tc.LOC,lay_trang=mang),
            d=dict(so=dict(game={'g':dict(vung=dict(UA=dict(id='P',con='UAH 100')))})),HAN_MIN_MS=0)
        fn=next(n for n in ast.parse(src).body if isinstance(n,ast.FunctionDef) and n.name=='xac_minh'); exec(compile(ast.Module(body=[fn],type_ignores=[]),'chon-tin.py','exec'),ns)
        for ma in ('UA','IN'):
            r,ly=ns['xac_minh'](dict(khoa='g',ma=ma)); self.assertIsNone(r); self.assertIn('tham khao',ly)
        r,ly=ns['xac_minh'](dict(khoa='g',ma='SG')); self.assertIsNone(r); self.assertEqual(ly,'so thieu id/gia vung')   # vung mua duoc van qua cua chan
if __name__=='__main__': unittest.main()
