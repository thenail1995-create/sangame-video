# python3 -m unittest khuon/tin-nhanh/test_chon_tin.py  (hoặc: cd khuon/tin-nhanh && python3 -m unittest test_chon_tin)
import datetime as dtm,unittest
import chon_logic as cl
def U(kieu,i=''): return dict(kieu=kieu,khoa=f'{kieu}{i}')
class T(unittest.TestCase):
    def test_tin_nong_ngay(self):
        d=dtm.date(2026,10,12)
        self.assertTrue(cl.tin_nong_hop_le('2026-10-12',d)); self.assertTrue(cl.tin_nong_hop_le('2026-10-11',d))
        self.assertFalse(cl.tin_nong_hop_le('2026-10-10',d))
    def test_khong_hai_tin_danh_sach_gia(self):
        r=cl.chon_ba(iter([U('giam-sau'),U('vua-giam'),U('deal-hot'),U('ps-plus-kho'),U('bai')]))
        self.assertEqual([x['kieu'] for x in r],['giam-sau','ps-plus-kho','bai'])
    def test_het_loai_khac_thi_chap_nhan_trung(self):
        r=cl.chon_ba([U('giam-sau'),U('ps-plus-kho'),U('vua-giam'),U('deal-hot')])
        self.assertEqual([x['kieu'] for x in r],['giam-sau','ps-plus-kho','vua-giam'])
        r=cl.chon_ba([U('giam-sau'),U('deal-hot')]); self.assertEqual(len(r),2)
    def test_lazy_dung_som(self):
        goi=[]
        def gen():
            for k in ('bai','giam-sau','ps-plus-kho','vua-giam'): goi.append(k); yield U(k)
        cl.chon_ba(gen()); self.assertEqual(goi,['bai','giam-sau','ps-plus-kho'])
    def test_trung_khoa(self):
        self.assertEqual(len(cl.chon_ba([U('bai',1),U('bai',1),U('bai',2)])),2)
    # ---- SAP HET GIAM (du phong, Hao chot 11/10)
    def test_sap_het_la_loai_khac_khong_phai_ds_gia(self):
        self.assertNotIn('sap-het',cl.LOAI_DS_GIA)
    def test_ngay_thieu_tin_giam_sau_deal_hot_sap_het(self):   # [giam sau, deal hot (de danh), sap het] -> 3 tin gom sap-het
        r=cl.chon_ba(iter([U('giam-sau'),U('vua-giam',1),U('deal-hot'),U('sap-het')]))
        self.assertEqual([x['kieu'] for x in r],['giam-sau','sap-het','vua-giam'])   # sap-het (loai khac) di truoc tin giam gia thu 2
        r=cl.chon_ba(iter([U('giam-sau'),U('deal-hot'),U('sap-het')]))
        self.assertEqual(len(r),3); self.assertIn('sap-het',[x['kieu'] for x in r])
    def test_ngay_du_tin_khong_toi_sap_het(self):             # ung_vien luoi: du 3 tin truoc khi sinh sap-het (khong tai trang thua)
        goi=[]
        def gen():
            for k in ('bai','giam-sau','ps-plus-kho','deal-hot','sap-het'): goi.append(k); yield U(k)
        r=cl.chon_ba(gen()); self.assertNotIn('sap-het',[x['kieu'] for x in r]); self.assertNotIn('sap-het',goi)
    def test_khoang_han_sap_het(self):
        H=1_000_000_000_000; N2=2*24*3600*1000
        self.assertTrue(cl.trong_khoang_sap_het(H,H))                # bien duoi: dung 2 ngay
        self.assertTrue(cl.trong_khoang_sap_het(H+N2,H))             # bien tren: dung 4 ngay
        self.assertTrue(cl.trong_khoang_sap_het(H+N2//2,H))
        self.assertFalse(cl.trong_khoang_sap_het(H-1,H)); self.assertFalse(cl.trong_khoang_sap_het(H+N2+1,H))
class LocNoiBatTruocKhiCat(unittest.TestCase):    # Sol P1: nguon 15 game, 7 chua noi bat; cat 10 roi loc chi con 2, loc truoc roi cat con 7
    def test_loc_truoc_khi_cat(self):
        ds=[f'g{i}' for i in range(15)]; chua={'g1','g3','g4','g8','g10','g12','g14'}; trung=lambda h:None if h in chua else 'da noi bat'
        cu=[h for h in ds[:10] if not trung(h)]; # cach cu: chi con cac game chua noi bat nam TRONG 10 dau
        self.assertEqual(sorted(cu),['g1','g3','g4','g8'])
        moi,bo=cl.loc_noi_bat_truoc_khi_cat(ds,trung,10)
        self.assertEqual(moi,['g1','g3','g4','g8','g10','g12','g14']); self.assertEqual(len(bo),8)
    def test_cat_sau_loc(self):
        moi,_=cl.loc_noi_bat_truoc_khi_cat([f'g{i}' for i in range(30)],lambda h:'x' if h in ('g0','g1') else None,10); self.assertEqual(moi,[f'g{i}' for i in range(2,12)])
if __name__=='__main__': unittest.main()
