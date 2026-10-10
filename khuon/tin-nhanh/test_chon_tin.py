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
if __name__=='__main__': unittest.main()
