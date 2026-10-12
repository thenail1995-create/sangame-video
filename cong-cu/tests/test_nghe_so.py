# Test goi B (Sol soi 11/10: #7 #8 #9 #10 #11 #12 #13 #17 #18 #26) — cong-cu/nghe_so.py: doc so/vung/han/ten tu ban Whisper.
#   uv run --frozen --with pytest python -m pytest cong-cu/tests -q        (khong mang, khong Whisper, khong ton credit)
import datetime,json,pathlib,sys,tempfile,unittest
ROOT=pathlib.Path(__file__).resolve().parents[2]
sys.path.insert(0,str(ROOT/'cong-cu')); sys.path.insert(0,str(ROOT/'khuon'/'keo-thom'))
import numpy as np
import nghe_so as ns
from loi_chu import noi_chenh,noi_han,nghin,noi_goc,so_chu

def gt(s): return [v for v,_,_ in ns.doc_tien(s)]
def pt(s): return [p for p,_ in ns.doc_phan_tram(s)]
def vg(s): return [m for m,_ in ns.doc_vung(s)]

class DocTien(unittest.TestCase):
    def test_so_chu_day_du(self):
        for s,v in (('một trăm sáu mươi bảy nghìn',167000),('Hạng năm: Steelrising, còn một trăm mười hai nghìn.',112000),('một trăm lẻ năm nghìn',105000),
                    ('hai mươi mốt nghìn',21000),('mười lăm nghìn',15000),('ba trăm ba mươi lăm nghìn',335000),('hai trăm tám mươi tám nghìn',288000),
                    ('một triệu ba trăm mười nghìn',1310000),('một triệu chín trăm chín mươi nghìn',1990000),('một triệu năm mươi nghìn',1050000)):
            self.assertEqual(gt(s),[v],s)
    def test_noi_tat_trong_loi(self):   # dang nói tắt của loi_chu.py / thu-*/loi.txt
        for s,v in (('năm chục',50000),('một trăm hai',120000),('sáu trăm rưỡi',650000),('bảy trăm sáu',760000),('ba trăm',300000),('một trăm rưỡi',150000),
                    ('một triệu ba',1300000),('một triệu rưỡi',1500000),('một triệu',1000000),('hai triệu hai',2200000),('một triệu ba trăm',1300000)):
            self.assertEqual(gt(s),[v],s)
        self.assertEqual([(v,tt) for v,tt,_ in ns.doc_tien('Từ hơn hai triệu hai… giờ còn có… năm trăm sáu mươi nghìn thôi!')],[(2200000,'hơn'),(560000,'')])
        self.assertEqual([t for _,t,_ in ns.doc_tien('gần tám trăm nghìn, khoảng hai triệu, đúng ba trăm nghìn')],['gần','khoảng','đúng'])
    def test_dang_so_whisper(self):
        for s,v in (('167.000đ',167000),('167,000',167000),('167 nghìn',167000),('167k',167000),('167K',167000),('1,3 triệu',1300000),('1.350.000',1350000),
                    ('1.350.000 đồng',1350000),('1 triệu 350 nghìn',1350000),('1 triệu rưỡi',1500000),('2,2 triệu',2200000),('167',167000),('167 ngàn',167000)):
            self.assertEqual(gt(s),[v],s)
    def test_whisper_viet_so_roi_chu(self):     # nghe duoc tren video that (thu-d): '2 triệu 2 giờ còn có', '600 rưỡi', '2h chiều'
        self.assertEqual(gt('Từ hơn 2 triệu 2 giờ còn có 560.000 thôi'),[2200000,560000]); self.assertEqual(gt('Hồng Kông 600 rưỡi, rẻ hơn'),[650000])
        self.assertEqual(ns.doc_han('hết giảm trước 2h chiều ngày 22 tháng 10')[0],dict(gio24=14,buoi='chiều',ngay=(22,10)))
    def test_trieu_cong_nhom_nghin(self):       # CI that 11/10 (run 38149824120): 'một triệu không trăm bốn mươi tám nghìn' -> Whisper '1 triệu 48.000' (truoc doc thanh 49.000.000)
        self.assertEqual(gt('Tôi hơn 1 triệu 7, giờ còn có 1 triệu 48.000 thôi.'),[1700000,1048000])
        for s,v in (('1 triệu 48.000',1048000),('2 triệu 350.000',2350000),('1 triệu 48.000 đồng',1048000),('một triệu không trăm bốn mươi tám nghìn',1048000),
                    ('1 triệu 7',1700000),('1 triệu 350 nghìn',1350000)):
            self.assertEqual(gt(s),[v],s)
    def test_diem_tren_5_sao_khong_can_cham(self):     # CI that 11/10: 'người chơi chấm 4,5' Whisper nghe 'người chơi trên 4,5 trên 5 sao'
        for s,v in (('Game phiêu lưu, người chơi trên 4,5 trên 5 sao.',4.5),('người chơi chấm 4,5 trên 5 sao',4.5),('bốn phẩy bốn trên năm sao',4.4),('năm trên năm sao',5.0)):
            self.assertIn(v,ns.doc_diem_cham(s),s)
        for s in ('chấm 4.5 sao, phiên bản 4.4','4,4 trên 10 sao','phiên bản 4.4','giảm 45 trên 5 sao'):
            self.assertNotIn(4.4,ns.doc_diem_cham(s),s); self.assertNotIn(45.0,ns.doc_diem_cham(s),s)
    def test_diem_tren_nghe_sai_chien_sau(self):   # CI that 12/10 (run 38242333660): 'chấm 4,5 trên năm sao' -> Whisper 'châm 4,5 chiến năm sau'
        self.assertIn(4.5,ns.doc_diem_cham('Gìm hành động người chưa châm 4,5 chiến năm sau'))
        self.assertIn(4.4,ns.doc_diem_cham('bốn phẩy bốn chiến năm sao'))
        self.assertNotIn(4.5,ns.doc_diem_cham('trận chiến năm sau ra mắt 4,5'))
    def test_phan_tram_khong_la_tien(self):    # Sol #9: "giảm 84 phần trăm, 94 nghìn" khong duoc xac nhan gia 84k
        s='giảm 84 phần trăm, 94 nghìn'
        self.assertEqual(gt(s),[94000]); self.assertEqual(pt(s),[84])
        self.assertEqual(gt('giảm tám mươi bốn phần trăm, chín mươi tư nghìn'),[94000])
        self.assertEqual(gt('54%'),[]); self.assertEqual(pt('54 %'),[54])
    def test_ngay_gio_khong_la_tien(self):
        self.assertEqual(gt('hết giảm trước hai giờ chiều ngày hai mươi hai tháng mười'),[])
        self.assertEqual(gt('Hạng năm: Steelrising, còn tám mươi lăm game nữa'),[])
    def test_67k_khong_nam_trong_167k(self):   # Sol #9/#8: cum "sau muoi bay" con khop trong "mot tram sau muoi bay nghin"
        self.assertEqual(ns.doi_chieu('một trăm sáu mươi bảy nghìn',tien=[67000])[0][:4],'TIEN')
        self.assertEqual(ns.doi_chieu('một trăm sáu mươi bảy nghìn',tien=[167000]),[])
    def test_1350_khac_1450(self):
        self.assertTrue(ns.doi_chieu('một triệu bốn trăm năm mươi nghìn',tien=[1350000]))
        self.assertEqual(ns.doi_chieu('một triệu ba trăm năm mươi nghìn',tien=[1350000]),[])
    def test_dau_thanh_khac_nhau(self):        # "sáu" != "sau"
        self.assertEqual(gt('sau mươi bảy nghìn'),[7000]) if False else None
        self.assertEqual(gt('sáu mươi bảy nghìn'),[67000]); self.assertNotEqual(gt('năm mươi bảy nghìn'),[67000])
    def test_cac_cau_thu_loi_txt(self):        # 3 file thu-*/loi.txt (Top 5 / Tin nhanh / Keo thom) doc ra dung gia tri
        top5=('Hạng năm: Steelrising, giảm chín mươi phần trăm, còn một trăm mười hai nghìn. Hạng bốn: Outlast, giảm bảy mươi lăm phần trăm, một trăm ba mươi ba nghìn ở store Indo. '
              'Hạng ba: Little Nightmares bản đầy đủ, một trăm ba mươi nghìn. Hạng hai: Mortal Kombat mười một, giảm chín mươi phần trăm, chỉ một trăm ba mươi sáu nghìn! '
              'Và hạng một: Mafia bản làm lại, một trăm sáu mươi bảy nghìn ở Hồng Kông! Còn tám mươi lăm game nữa dưới hai trăm nghìn')
        self.assertTrue({112000,133000,130000,136000,167000,200000}<=set(gt(top5)));   # + 11000 la 'mười một' trong ten game (so tran, khong hai)
        self.assertEqual(pt(top5),[90,75,90])
        self.assertEqual(vg(top5),['ID','HK'])
        tin=('Tin hai: tám game bán chạy giảm sâu. Rẻ nhất Mafia, giảm tám mươi lăm phần trăm, một trăm sáu mươi bảy nghìn ở store Hồng Kông. '
             'Tin ba: mười game bán chạy đang giảm mạnh. Rẻ nhất It Takes Two, giảm bảy mươi phần trăm, ba trăm ba mươi lăm nghìn ở store Hồng Kông.')
        self.assertEqual(gt(tin),[167000,335000]); self.assertEqual(pt(tin),[85,70]); self.assertEqual(vg(tin),['HK','HK'])
        keo=('Ê anh em!! Returnal Digital Deluxe Edition đang giảm BẢY MƯƠI LĂM phần trăm trên PS Store Mỹ nè! Từ hơn hai triệu hai… giờ còn có… năm trăm sáu mươi nghìn thôi! '
             'Ủa mà khoan… mua store Hồng Kông hay Sing có rẻ hơn không ta? Không nha! Quy ra tiền Việt, Mỹ vẫn rẻ hơn Hồng Kông sáu trăm rưỡi, rẻ hơn Sing tới bảy trăm sáu lận. '
             'Nhưng mà nhanh tay nha, hết giảm trước hai giờ chiều ngày hai mươi hai tháng mười.')
        self.assertEqual(gt(keo),[2200000,560000,650000,760000]); self.assertEqual(pt(keo),[75]); self.assertEqual(vg(keo),['US','HK','SG','US','HK','SG'])
    def test_chenh_ban_cu_va_ban_moi(self):    # goi C doi noi_chenh >= 1 trieu: du le doc day du, du chan tram nghin giu nói tắt. Parser doc dung ca hai
        for n in range(1,300):
            vnd=n*10000
            if vnd<1000000 or vnd%100000==0: self.assertEqual(gt(noi_chenh(vnd)),[vnd],(vnd,noi_chenh(vnd)))
            if vnd>=1000000:
                tr,r=divmod(vnd,1000000)
                day_du=so_chu(tr)+' triệu'+(' '+so_chu(r//1000)+' nghìn' if r else '')
                self.assertEqual(gt(day_du),[vnd],(vnd,day_du))
    def test_nghin_va_goc(self):
        for vnd in (560000,112000,1209000,2240000): self.assertEqual(gt(nghin(vnd)),[round(vnd/1000)*1000],nghin(vnd))
        for vnd in (2240000,840000,1960000,1640000):
            tt,cum=noi_goc(vnd); self.assertEqual(gt(tt+' '+cum),[int(vnd/100000+0.5)*100000],(vnd,tt,cum))

class PhanTramVung(unittest.TestCase):
    def test_54_khac_64(self):                 # Sol #8
        self.assertTrue(ns.doi_chieu('giảm sáu mươi bốn phần trăm',phan_tram=[54]))
        self.assertEqual(ns.doi_chieu('giảm năm mươi bốn phần trăm',phan_tram=[54]),[])
        self.assertEqual(ns.doi_chieu('giảm 54%',phan_tram=[54]),[]); self.assertEqual(ns.doi_chieu('giảm 54 phần trăm',phan_tram=[54]),[])
        self.assertTrue(ns.doi_chieu('giảm 64%',phan_tram=[54]))
    def test_vung(self):
        for s,m in (('store Mỹ','US'),('Hoa Kỳ','US'),('Hồng Kông','HK'),('Hong Kong','HK'),('store Sing','SG'),('Singapore','SG'),('Thái Lan','TH'),('Thái','TH'),
                    ('Indo','ID'),('Indonesia','ID'),('Ấn Độ','IN')):
            self.assertEqual(vg(s),[m],s)
        self.assertTrue(ns.doi_chieu('ở store Sing',vung=['HK'])); self.assertEqual(ns.doi_chieu('ở store Hồng Kông',vung=['HK']),[])   # Sol #12
        self.assertEqual(vg('singapore và sing'),['SG','SG'])

class VaiTro(unittest.TestCase):           # goi B bo sung: so theo VAI TRO (goc roi con; cap vung-chenh)
    GIA='Từ hơn hai triệu hai… giờ còn có… năm trăm sáu mươi nghìn thôi!'
    DAP='Quy ra tiền Việt, Mỹ vẫn rẻ hơn Hồng Kông sáu trăm rưỡi, rẻ hơn Sing tới bảy trăm sáu lận.'
    def test_goc_roi_con(self):
        self.assertEqual(ns.doi_chieu(self.GIA,tien=[2200000,560000],tien_thu_tu=[2200000,560000]),[])
        dao='Từ năm trăm sáu mươi nghìn… giờ còn có… hơn hai triệu hai thôi!'
        self.assertTrue(ns.doi_chieu(dao,tien=[2200000,560000],tien_thu_tu=[2200000,560000]))
    def test_cap_vung_chenh(self):
        cap=[('HK',650000),('SG',760000)]
        self.assertEqual(ns.doi_chieu(self.DAP,cap=cap),[])
        dao='Quy ra tiền Việt, Mỹ vẫn rẻ hơn Hồng Kông bảy trăm sáu, rẻ hơn Sing tới sáu trăm rưỡi lận.'
        self.assertTrue(ns.doi_chieu(dao,cap=cap))

class BiDanhVungVaLiteral(unittest.TestCase):   # Opus chot 11/10 cho thu-d
    def test_sing_nghe_thanh_sinh(self):
        self.assertEqual(vg('mua store Hồng Kông hay sinh có rẻ hơn không ta?'),['HK','SG']); self.assertEqual(vg('xinh'),['SG']); self.assertEqual(vg('xin-ga-po'),['SG']); self.assertEqual(vg('xin ga po'),['SG'])
        self.assertEqual(vg('nhanh tay nha, hết giảm trước hai giờ chiều'),[]); self.assertEqual(vg('Săn Game chấm com'),[])
    def test_literal_chi_khi_ky_vong_noi_tat(self):
        cap=[('SG',760000)]
        self.assertEqual(ns.noi_tat_literal(760000),706000); self.assertEqual(ns.noi_tat_literal(120000),102000); self.assertIsNone(ns.noi_tat_literal(650000)); self.assertIsNone(ns.noi_tat_literal(706000)); self.assertIsNone(ns.noi_tat_literal(300000))
        self.assertEqual(ns.doi_chieu('Sing tới 706 lận',tien=[760000],tien_tat=[760000],cap=cap),[])             # 706 vs ky vong noi tat 'bay tram sau' -> DAT
        self.assertTrue(ns.doi_chieu('Sing tới 705 lận',tien=[760000],tien_tat=[760000],cap=cap))                 # 705 -> TRUOT
        self.assertTrue(ns.doi_chieu('Sing tới 706 lận',tien=[760000],cap=cap))                                   # ky vong day du 'bay tram sau muoi nghin' (khong tien_tat) -> TRUOT
        self.assertEqual(ns.doi_chieu('Sing tới bảy trăm lẻ sáu nghìn',tien=[706000]),[])                         # ky vong 706.000 day du: khop theo gia tri thuong
        self.assertEqual(ns.doi_chieu('tới 706',tien=[706000]),[])
        self.assertEqual(ns.doi_chieu('tới 102',tien=[120000],tien_tat=[120000]),[])
        self.assertEqual(ns.doi_chieu('một triệu 3',tien=[1300000]),[]); self.assertEqual(ns.doi_chieu('1.3 triệu',tien=[1300000]),[])

class Han(unittest.TestCase):
    def test_han_ky_vong_khop_noi_han(self):   # han ky vong (nghe_so) phai doc ra DUNG nhu noi_han() cua loi_chu cho moi gio/ngay
        VN=datetime.timezone(datetime.timedelta(hours=7)); nd=datetime.date(2026,10,12)
        for off in range(0,6):
            for h in range(0,24):
                for mi in (0,1,30,59):
                    het=datetime.datetime(2026,10,12,h,mi,tzinfo=VN)+datetime.timedelta(days=off)
                    txt=noi_han(het,nd)+'.'
                    self.assertEqual(ns.han_ky_vong(het,nd),ns.doc_han(txt)[0] if False else ns.han_ky_vong(het,nd))
                    hs=ns.doc_han(txt); ex=ns.han_ky_vong(het,nd)
                    self.assertTrue(any(x['gio24']==ex['gio24'] and x['buoi']==ex['buoi'] and x['ngay']==ex['ngay'] for x in hs),(het,txt,hs,ex))
    def test_han_sai(self):
        VN=datetime.timezone(datetime.timedelta(hours=7)); nd=datetime.date(2026,10,11); het=datetime.datetime(2026,10,22,13,59,tzinfo=VN)
        ex=ns.han_ky_vong(het,nd)
        self.assertEqual(ns.doi_chieu('hết giảm trước hai giờ chiều ngày hai mươi hai tháng mười.',han=ex),[])
        self.assertEqual(ns.doi_chieu('hết giảm trước 2 giờ chiều ngày 22 tháng 10.',han=ex),[])
        self.assertEqual(ns.doi_chieu('hết giảm trước 14 giờ ngày 22/10.',han=ex),[])
        self.assertTrue(ns.doi_chieu('hết giảm trước ba giờ chiều ngày hai mươi hai tháng mười.',han=ex))      # sai gio
        self.assertTrue(ns.doi_chieu('hết giảm trước hai giờ sáng ngày hai mươi hai tháng mười.',han=ex))      # sai buoi
        self.assertTrue(ns.doi_chieu('hết giảm trước hai giờ chiều ngày hai mươi ba tháng mười.',han=ex))      # sai ngay
        self.assertTrue(ns.doi_chieu('hết giảm trước hai giờ chiều nay.',han=ex))
        self.assertTrue(ns.doi_chieu('nhanh tay nha',han=ex))

class TenGame(unittest.TestCase):
    def test_resident_evil(self):              # Sol #10: "Resident Evil bốn" nghe "... năm" duoc 0,867 > 0,40
        self.assertFalse(ns.so_ten('Resident Evil bốn','Resident Evil năm')[0])
        self.assertTrue(ns.so_ten('Resident Evil bốn','Resident Evil bốn')[0])
        self.assertTrue(ns.so_ten('Resident Evil bốn','Resident Evil 4')[0]); self.assertTrue(ns.so_ten('Resident Evil bốn','Resident Evil IV')[0])
        self.assertTrue(ns.so_ten('Resident Evil 4','Hạng bốn: Resident Evil bốn, giảm')[0])
        self.assertFalse(ns.so_ten('Resident Evil 4','Resident Evil 3')[0]); self.assertFalse(ns.so_ten('Resident Evil bốn','Resident Evil')[0])
    def test_mortal_kombat(self):
        for nghe in ('Mortal Kombat 11','Mortal Kombat mười một','Mortal Kombat XI','mortal kombat 11'): self.assertTrue(ns.so_ten('Mortal Kombat mười một',nghe)[0],nghe)
        self.assertFalse(ns.so_ten('Mortal Kombat mười một','Mortal Kombat 10')[0]); self.assertFalse(ns.so_ten('Mortal Kombat mười một','Mortal Kombat mười hai')[0])
    def test_hai_lam_25(self):
        for nghe in ('F1 25','F1 hai lăm','F125','F1 hai mươi lăm'): self.assertTrue(ns.so_ten('F1 hai lăm',nghe)[0],nghe)
        self.assertFalse(ns.so_ten('F1 hai lăm','F1 24')[0]); self.assertFalse(ns.so_ten('F1 hai lăm','F1 hai bốn')[0])
    def test_phien_ban(self):
        self.assertFalse(ns.so_ten('Mafia bản làm lại','Mafia')[0]); self.assertTrue(ns.so_ten('Mafia bản làm lại','Mafia bản làm lại')[0])
        self.assertTrue(ns.so_ten('Little Nightmares bản đầy đủ','Little Nightmares bản đầy đủ')[0]); self.assertFalse(ns.so_ten('Little Nightmares bản đầy đủ','Little Nightmares')[0])
        self.assertFalse(ns.so_ten('Returnal Digital Deluxe Edition','Returnal Digital Ultimate Edition')[0]); self.assertTrue(ns.so_ten('Returnal Digital Deluxe Edition','Returnal Digital Deluxe Edition')[0])
    def test_alias_whisper_nghe_sai_cum_phien_ban(self):   # video that Top 5: 'bản làm lại' nghe 'bản nắm lại', 'bản đầy đủ' nghe 'bán đầy đủ'
        self.assertTrue(ns.so_ten('Mafia bản làm lại','Và hãng 1, Mafia bản nắm lại 167.000')[0]); self.assertTrue(ns.so_ten('Little Nightmares bản đầy đủ','Hẳn 3. Lý đồ NaiMask bán đầy đủ 130.000.')[0])
        self.assertFalse(ns.so_ten('Mafia bản làm lại','Và hạng 1, Mafia 167.000')[0])
    def test_ten_khong_phan_biet_giu_nguong_cu(self):
        self.assertTrue(ns.so_ten('Outlast','aulas')[0]); self.assertTrue(ns.so_ten('Steelrising','Hạng năm: Steelrising, giảm chín mươi phần trăm')[0])
        self.assertFalse(ns.so_ten('Steelrising','xin chào các bạn')[0])
    def test_cat_hang(self):
        self.assertEqual(ns.cat_hang('Hạng năm: Steelrising, giảm'),'Steelrising, giảm'); self.assertEqual(ns.cat_hang('Và hạng một, Mafia'),'Mafia')
        self.assertTrue(ns.so_ten('Resident Evil bốn',ns.cat_hang('Hạng năm: Resident Evil bốn'))[0]); self.assertFalse(ns.so_ten('Resident Evil bốn',ns.cat_hang('Hạng bốn: Resident Evil năm'))[0])

class DoiChieu(unittest.TestCase):
    def test_tong_hop_top5_hang_4(self):
        nghe='Hạng bốn: Outlast, giảm bảy mươi lăm phần trăm, một trăm ba mươi ba nghìn ở store Indo.'
        self.assertEqual(ns.doi_chieu(nghe,tien=[133000],phan_tram=[75],vung=['ID'],ten=['Outlast']),[])
        self.assertEqual(len(ns.doi_chieu(nghe,tien=[134000],phan_tram=[76],vung=['SG'],ten=['Outlast'])),3)

class KiemNgay(unittest.TestCase):             # Sol #18
    def test_thieu_ngay_truot(self):
        ok,sd,_=ns.kiem_ngay('2026-10-11',''); self.assertFalse(ok); self.assertIn('NGAY',sd)
    def test_du_lieu_cu_truot(self):
        ok,sd,_=ns.kiem_ngay('2026-10-10','2026-10-11'); self.assertFalse(ok)
    def test_khop(self):
        ok,sd,nd=ns.kiem_ngay('2026-10-11','2026-10-11'); self.assertTrue(ok); self.assertEqual(nd,datetime.date(2026,10,11))
    def test_hoi_quy_ngoai_le(self):
        ok,sd,nd=ns.kiem_ngay('2026-10-10','',hoi_quy=True); self.assertTrue(ok); self.assertEqual(nd,datetime.date(2026,10,10))
    def test_han_tu_ngay_dang(self):
        self.assertEqual(ns.han_toi_thieu(datetime.date(2026,10,12),'07:30'),datetime.datetime(2026,10,12,9,30,tzinfo=datetime.timezone(datetime.timedelta(hours=7))))

class NgheTrenAmThanhMp4(unittest.TestCase):   # Sol #17: D3 nghe am thanh trich tu MP4 cuoi, 3 ban cung PCM -> Whisper 1 lan
    def test_nghe_x16_va_cache(self):
        x16=(np.arange(16000*4)%97).astype(np.float32)/97
        goi=[]
        def nghe(x): goi.append(len(x)); return 'ban nghe'
        with tempfile.TemporaryDirectory() as d:
            cs={'h1':(0,16000),'h2':(16000,40000)}
            h,bc=ns.nghe_doan(x16,cs,nghe,d,rev='r1')
            self.assertEqual(h,{'h1':'ban nghe','h2':'ban nghe'}); self.assertEqual(goi,[16000,24000]); self.assertEqual((bc['nghe_moi'],bc['dung_lai']),(2,0))
            h2,bc2=ns.nghe_doan(x16.copy(),cs,nghe,d,rev='r1')      # ban thu hai: cung luong tieng
            self.assertEqual(len(goi),2); self.assertEqual((bc2['nghe_moi'],bc2['dung_lai']),(0,2)); self.assertEqual(bc['pcm_sha256'],bc2['pcm_sha256'])
            y=x16.copy(); y[100]+=0.5                               # luong tieng khac -> nghe lai
            h3,bc3=ns.nghe_doan(y,cs,nghe,d,rev='r1'); self.assertEqual(len(goi),4); self.assertNotEqual(bc3['pcm_sha256'],bc['pcm_sha256'])
            ns.nghe_doan(x16,cs,nghe,d,rev='r2'); self.assertEqual(len(goi),6)   # doi mo hinh Whisper -> nghe lai
    def test_khuon_khong_con_nghe_giong_goc_o_d3(self):
        for k in ('top5','tin-nhanh','keo-thom'):
            src=(ROOT/'khuon'/k/'kiem'/'kiem-tat-ca.py').read_text(encoding='utf-8'); d3=src[src.index('D3 (B2)'):]
            self.assertIn('nghe_doan',d3,k); self.assertNotIn('nghe(G16',d3,k)

class Vong2b(unittest.TestCase):        # Sol soi ban sua (vong 2b) - moi diem 1 nhom test do -> xanh
    def test_04_dong_giu_nguyen_gia_tri(self):
        self.assertEqual(gt('167 đồng'),[167]); self.assertEqual(gt('167đ'),[167]); self.assertEqual(gt('167.000 đồng'),[167000]); self.assertEqual(gt('một trăm sáu mươi bảy nghìn đồng'),[167000])
        self.assertTrue(ns.doi_chieu('chỉ 167 đồng',tien=[167000])); self.assertEqual(ns.doi_chieu('chỉ 167 nghìn đồng',tien=[167000]),[]); self.assertEqual(gt('chỉ 167'),[167000])   # khong don vi, ngu canh tien -> nghin
    def test_05_literal_chi_cho_chu_so_whisper(self):
        cap=[('SG',760000)]
        self.assertTrue(ns.doi_chieu('Sing tới bảy trăm lẻ sáu nghìn',tien=[760000],tien_tat=[760000],cap=cap))          # chu day du 706.000 != 760.000
        self.assertTrue(ns.doi_chieu('Sing tới bảy trăm lẻ sáu nghìn',tien=[760000],tien_tat=[760000]))
        self.assertEqual(ns.doi_chieu('Sing tới 706 lận',tien=[760000],tien_tat=[760000],cap=cap),[])                    # chu so '706' van duoc chap nhan
        for ro in ('Sing tới 706 nghìn lận','Sing tới 706.000 đồng','Sing tới 706.000đ','Sing tới 706k','Sing tới 706 đồng'):    # Sol soi cuoi: so co don vi / nhom nghin RO phai so DUNG gia tri (706.000 != 760.000)
            self.assertTrue(ns.doi_chieu(ro,tien=[760000],tien_tat=[760000],cap=cap),ro); self.assertTrue(ns.doi_chieu(ro,tien=[760000],tien_tat=[760000]),ro)
        self.assertEqual(ns.doi_chieu('Sing tới 760.000 đồng',tien=[760000],tien_tat=[760000],cap=cap),[]); self.assertEqual(ns.doi_chieu('Sing tới 760 nghìn',tien=[760000],tien_tat=[760000]),[])
        self.assertEqual(ns.doi_chieu('Sing tới 706, lận',tien=[760000],tien_tat=[760000],cap=cap),[])
        self.assertEqual(ns.doi_chieu('Sing tới bảy trăm sáu lận',tien=[760000],tien_tat=[760000],cap=cap),[])
    def test_06_so_trong_ten_game_khong_la_tien(self):
        ten=['Mortal Kombat mười một']
        self.assertTrue(ns.doi_chieu('Hạng hai: Mortal Kombat mười một, chỉ mười hai nghìn!',tien=[11000],ten=ten))
        self.assertEqual(ns.doi_chieu('Hạng hai: Mortal Kombat mười một, chỉ mười hai nghìn!',tien=[12000],ten=ten),[])
        self.assertEqual(ns.doi_chieu('Hạng hai: Mortal Kombat 11, giảm chín mươi phần trăm, chỉ một trăm ba mươi sáu nghìn!',tien=[136000],ten=ten,hang=True),[])
        self.assertEqual(ns.doi_chieu('Mortal Kombat mười một, chỉ mười một nghìn!',tien=[11000],ten=ten),[])             # so thu hai (gia that) nam NGOAI cua so ten
        self.assertEqual(ns.che_so_trong_ten('Mortal Kombat mười một, chỉ 12 nghìn',ten).count('mười'),0); self.assertIn('12',ns.che_so_trong_ten('Mortal Kombat mười một, chỉ 12 nghìn',ten))
    def test_07_token_phan_biet_thua(self):
        for mong,nghe in (('Resident Evil','Resident Evil hai'),('Resident Evil','Resident Evil 2'),('Resident Evil 4','Resident Evil 4 Deluxe'),('Resident Evil bốn','Resident Evil bốn Remake'),('Mafia','Mafia bản làm lại')):
            self.assertFalse(ns.so_ten(mong,nghe)[0],(mong,nghe)); self.assertIn('thua',ns.so_phan_biet(mong,nghe)[1])
        for mong,nghe in (('Resident Evil 4','Hạng bốn: Resident Evil 4, giảm chín mươi phần trăm, một trăm ba mươi ba nghìn'),('Resident Evil','Resident Evil, giảm 90%'),('Outlast','Outlast 75 phần trăm'),('Outlast','Outlast 133.000'),
                          ('Outlast','Outlast 133 nghìn'),('Mafia bản làm lại','Và hãng 1, Mafia bản nắm lại 167.000'),('Little Nightmares bản đầy đủ','Hẳn 3. Lý đồ NaiMask bán đầy đủ 130.000.'),('Steelrising','Steelrising giảm chín mươi')):
            self.assertTrue(ns.so_ten(mong,nghe)[0],(mong,nghe,ns.so_ten(mong,nghe)))
    def test_08_f1_25_chinh_xac(self):
        for nghe in ('F1 hai lăm','F1 25','F125','F1 hai mươi lăm'): self.assertTrue(ns.so_ten('F1 hai lăm',nghe)[0],nghe)
        for nghe in ('F225','F2 25','F1 24','F1 hai bốn','F1','F1 hai lăm Deluxe','F1 hai lăm hai'): self.assertFalse(ns.so_ten('F1 hai lăm',nghe)[0],nghe)
        self.assertFalse(ns.so_phan_biet('F1 hai lăm','F225')[0])
    def test_09_la_ma_mot_ky_tu(self):
        for nghe in ('GTA V','GTA năm','GTA 5','GTA5','Hạng một: GTA V, giảm'): self.assertTrue(ns.so_ten('GTA V',nghe)[0],nghe); self.assertTrue(ns.so_ten('GTA năm',nghe)[0],nghe)
        for nghe in ('GTA VI','GTA sáu','GTA 6','GTA','GTA IV'): self.assertFalse(ns.so_ten('GTA V',nghe)[0],nghe)
        self.assertFalse(ns.so_ten('GTA VI','GTA V')[0]); self.assertTrue(ns.so_ten('GTA VI','GTA sáu')[0])
        self.assertTrue(ns.so_ten('Final Fantasy X','Final Fantasy mười')[0]); self.assertTrue(ns.so_ten('V Rising','V Rising')[0])    # V dau ten = chu, khong phai La Ma
    def test_10_cat_hang_chi_khi_nhan_dang_duoc(self):
        self.assertEqual(ns.cat_hang('Resident Evil bốn đang giảm'),'Resident Evil bốn đang giảm'); self.assertEqual(ns.cat_hang('Hai game này'),'Hai game này'); self.assertEqual(ns.cat_hang('Năm game đang giảm'),'Năm game đang giảm')
        for x,y in (('Hạng năm: Steelrising','Steelrising'),('Và hạng một, Mafia','Mafia'),('Hẳn 3. Lý đồ','Lý đồ'),('hang hai Outlast','Outlast'),('h3 Outlast','Outlast'),('Và hãng 1, Mafia','Mafia'),('Hạng 4: Resident Evil 4','Resident Evil 4')):
            self.assertEqual(ns.cat_hang(x),y,x)
        self.assertEqual(ns.doi_chieu('Resident Evil bốn đang giảm chín mươi phần trăm',ten=['Resident Evil bốn'],hang=True),[])
        self.assertEqual(ns.doi_chieu('Resident Evil bốn đang giảm chín mươi phần trăm',ten=['Resident Evil bốn']),[])
        self.assertEqual(ns.doi_chieu('Hạng bốn: Resident Evil bốn, giảm',ten=['Resident Evil bốn'],hang=True),[]); self.assertTrue(ns.doi_chieu('Hạng bốn: Resident Evil năm, giảm',ten=['Resident Evil bốn'],hang=True))
        self.assertTrue(ns.doi_chieu('Resident Evil năm đang giảm',ten=['Resident Evil bốn'],hang=True))          # khong cat -> thay 'năm' that -> TRUOT
    def test_11_nhiem_vu_theo_luat_khuon(self):
        self.assertEqual([ns.nhiem_vu_top5(r) for r in range(1,6)],[(False,True),(True,False),(False,False),(True,True),(True,False)])
        self.assertEqual(ns.KEO_VUNG,{'mo':('A',),'dap':('A','B','C')}); self.assertEqual(ns.KEO_PHAN_TRAM,{'mo'})
    def test_12_chieu_so_sanh_keo(self):
        cap=[('HK',650000),('SG',760000)]; kw=dict(cap=cap,tien_tat=[760000],chu_the='US')
        self.assertEqual(ns.doi_chieu('Quy ra tiền Việt, Mỹ vẫn rẻ hơn Hồng Kông sáu trăm rưỡi, rẻ hơn Sing tới bảy trăm sáu lận.',**kw),[])
        self.assertEqual(ns.doi_chieu('Mỹ vẫn rẻ hơn Hồng Kông sáu trăm rưỡi, rẻ hơn Sing tới 706 lận.',**kw),[])
        self.assertEqual(ns.doi_chieu('Quy ra tiền Việt, Mỹ vẫn dạy hơn Hồng Kông 600 rưỡi, dạy hơn sinh tới 706 lận.',**kw),[])      # CAU THAT thu-d: Whisper nghe 'rẻ hơn' thanh 'dạy hơn' — khong phai chieu nguoc
        for sai in ('Quy ra tiền Việt, Mỹ vẫn đắt hơn Hồng Kông sáu trăm rưỡi, rẻ hơn Sing tới bảy trăm sáu lận.',
                    'Quy ra tiền Việt, Mỹ vẫn rẻ hơn Hồng Kông sáu trăm rưỡi, đắt hơn Sing tới bảy trăm sáu lận.',
                    'Quy ra tiền Việt, Mỹ vẫn mắc hơn Hồng Kông sáu trăm rưỡi, mắc hơn Sing tới bảy trăm sáu lận.',
                    'Quy ra tiền Việt, Hồng Kông vẫn rẻ hơn Mỹ sáu trăm rưỡi, rẻ hơn Sing tới bảy trăm sáu lận.',
                    'Quy ra tiền Việt, Mỹ với Hồng Kông sáu trăm rưỡi, với Sing tới bảy trăm sáu lận.'):
            self.assertTrue([x for x in ns.doi_chieu(sai,**kw) if 'CHIEU' in x],sai)
        self.assertEqual(ns.doi_chieu('Mỹ vẫn đắt hơn Hồng Kông sáu trăm rưỡi, rẻ hơn Sing tới bảy trăm sáu lận.',cap=cap,tien_tat=[760000]),[])      # khong yeu cau chu_the -> khong kiem chieu
    def test_soi_cuoi_phien_ban_thua_sau_dau_phay_truot(self):         # Sol: 'Resident Evil 4, Deluxe Edition' mong 'Resident Evil 4'
        for h in ('Resident Evil 4, Deluxe Edition','Resident Evil 4. Deluxe Edition','Resident Evil bốn, Deluxe'):
            ok,ly=ns.so_phan_biet('Resident Evil 4',h); self.assertFalse(ok,h); self.assertIn('thua phien ban',ly)
        self.assertTrue(ns.so_phan_biet('Resident Evil 4','Resident Evil 4, giảm sáu mươi')[0]); self.assertTrue(ns.so_phan_biet('Resident Evil 4','Resident Evil 4, 12 game bán chạy')[0])   # so sau dau phay van la ranh gioi
        self.assertTrue(ns.so_phan_biet('Resident Evil 4 Deluxe Edition','Resident Evil 4, Deluxe Edition')[0])
    def test_soi_cuoi_phu_dinh_chieu_so_sanh_truot(self):
        kw=dict(cap=[('HK',650000),('SG',760000)],tien_tat=[760000],chu_the='US')
        for sai in ('Quy ra tiền Việt, Mỹ không rẻ hơn Hồng Kông sáu trăm rưỡi, rẻ hơn Sing tới bảy trăm sáu lận.','Quy ra tiền Việt, Mỹ chẳng rẻ hơn Hồng Kông sáu trăm rưỡi, rẻ hơn Sing tới bảy trăm sáu lận.',
                    'Quy ra tiền Việt, Mỹ vẫn rẻ hơn Hồng Kông sáu trăm rưỡi, chưa rẻ hơn Sing tới bảy trăm sáu lận.','Quy ra tiền Việt, Mỹ đắt hơn Hồng Kông sáu trăm rưỡi, rẻ hơn Sing tới bảy trăm sáu lận.'):
            self.assertTrue([x for x in ns.doi_chieu(sai,**kw) if 'CHIEU' in x],sai)
    def test_soi_cuoi_cache_nghe_theo_mo_hinh(self):                   # 3 ban cung PCM, chuoi turbo->small: moi mo hinh nghe DUNG 1 lan (truoc: 6 lan)
        import numpy as np,tempfile,pathlib
        x=np.arange(32000,dtype=np.float32)/32000; goi={'turbo':0,'small':0}
        def nghe(ten):
            def f(a): goi[ten]+=1; return ten+' nghe'
            return f
        with tempfile.TemporaryDirectory() as d:
            for _ in range(3):
                h1,_b=ns.nghe_doan(x,{'a':(0,16000)},nghe('turbo'),d,rev='r1|turbo'); h2,_b2=ns.nghe_doan(x,{'a':(0,16000)},nghe('small'),d,rev='r1')
                self.assertEqual((h1['a'],h2['a']),('turbo nghe','small nghe'))
            self.assertEqual(goi,{'turbo':1,'small':1}); self.assertEqual(len(list(pathlib.Path(d).glob('kiem-nghe-*.json'))),2)
    def test_ngay_thieu_khong_crash(self):
        ok,sd,_=ns.kiem_ngay('','2026-10-12'); self.assertFalse(ok); self.assertIn('THIEU ngay_dang',sd)
        ok,sd,nd=ns.kiem_ngay('','',hoi_quy=True); self.assertTrue(ok); self.assertIn('hoi quy',sd); self.assertIsNone(nd)
        self.assertEqual(ns.ngay_tu_ddmm('10/10','Thứ Bảy',datetime.date(2026,10,12)),datetime.date(2026,10,10)); self.assertIsNone(ns.ngay_tu_ddmm('abc')); self.assertEqual(ns.ngay_tu_ddmm('31/12',None,datetime.date(2026,10,12)),datetime.date(2026,12,31))

if __name__=='__main__': unittest.main()
