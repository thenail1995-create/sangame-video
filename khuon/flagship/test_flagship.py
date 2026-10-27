# Test A1 (Flagship): doc tien/the, moc tin, kieu mo xoay, loc + kiem trang (gia tri lap, khong mang), fail-closed.  Chay: uv run --frozen python -m pytest khuon/flagship -q
import datetime,importlib.util,json,os,pathlib,sys,tempfile,types,unittest
T=pathlib.Path(__file__).resolve().parent; ROOT=T.parent.parent
sys.path.insert(0,str(T)); sys.path.insert(0,str(ROOT/'cong-cu'))
import doc_tien as dt, moc_tin, loi_flagship as lf, ten_day_du as td
_sp=importlib.util.spec_from_file_location('chon_flagship',str(T/'chon-flagship.py')); CF=importlib.util.module_from_spec(_sp); _sp.loader.exec_module(CF)
NGAY='2026-10-27'
END_OK=str(int(datetime.datetime(2026,11,5,14,59,tzinfo=dt.VN).timestamp()*1000))
def trang(pid,con=19.99,goc=49.99,tien='USD',end=END_OK,video=True,sku='SKU1'):
    pr={'discountedPrice':f'${con}','basePrice':(f'${goc}' if goc else f'${con}'),'discountedValue':int(round(con*100)),'basePriceValue':int(round((goc or con)*100)),'currencyCode':tien,'endTime':end}
    cache={f'GameCTA:ADD_TO_CART:ADD_TO_CART:{pid}-{sku}:OUTRIGHT':{'price':pr}}
    if video: cache[f'Product:{pid}']={'media':[{'type':'VIDEO','url':'https://vulcan.dl.playstation.net/a.mp4'}]}
    return '<html><script id="env:1" type="application/json">'+json.dumps({'cache':cache})+'</script></html>'
def dong(hang=1,ten='Red Dead Redemption 2',ma='US',gia='$19.99',giam=60,pid='UP4497-PPSA03974_00-0000000000000CP1',nong=None,tn=None,**kw):
    loc={'US':'en-us','HK':'en-hk','SG':'en-sg','IN':'en-in'}[ma]
    r=dict(hang=hang,nen_tang='ps',ma='X',ten=ten,vung_re_nhat=ma,gia_vnd=560000,giam=giam,cach_quy='the',da_kiem_trang=True,lech_gia=False,
           gia_vung={ma:{'gia':gia,'tien':'USD'}},link=f'https://store.playstation.com/{loc}/product/{pid}',anh_url='https://image.api.playstation.com/x.png?w=320',
           nong=nong or {'diem':80,'mau':[]},thap_nhat=tn or {'la_thap_nhat':False,'so_ngay':5}); r.update(kw); return r
class DDGia:   # deal_diem gia: tra ket qua dat truoc
    def __init__(s,kq): s.kq=kq
    def gia_the_con_han(s,g,n): return True
    def quy_vnd(s,*a,**k): return s.kq
THE_OK=dict(vnd=560000,cach='the',the=[(10.0,2,280000.0)],tong_menh_gia=20.0,thua=0.01,mua_duoc=True,ly_do=None)
class NBRong:
    def trung(s,ten,pids): return None
class NBTrung:
    def trung(s,ten,pids): return 'dong game "x" (v-2026-10-25-top5)'
def chon(bang_dong,html=None,kq=THE_OK,nb=None,steam=None,gio='15:30'):
    pg=(lambda loc,pid:html) if not callable(html) else html
    return CF.Chon(NGAY,gio,{'keo':bang_dong if isinstance(bang_dong,list) else [bang_dong]},{'ngay':NGAY,'ty_gia_ngan_hang':{},'vung':{}},DDGia(kq),pg,nb or NBRong(),steam or (lambda t:[]))
PID='UP4497-PPSA03974_00-0000000000000CP1'

class DocTien(unittest.TestCase):
    def test_hien(self):
        self.assertEqual(dt.hien_tien(19.99,'USD'),'$19,99'); self.assertEqual(dt.hien_tien(74.75,'HKD'),'HK$74,75'); self.assertEqual(dt.hien_tien(12.6,'SGD'),'S$12,60'); self.assertEqual(dt.hien_tien(20,'USD'),'$20')
        self.assertEqual(dt.hien_the(80,'HKD'),'HK$80'); self.assertEqual(dt.hien_the(20,'SGD'),'S$20'); self.assertEqual(dt.hien_vnd(560000),'560.000đ')
    def test_doc_tien_usd_hkd_sgd(self):
        self.assertEqual(dt.doc_tien(19.99,'USD'),'mười chín đô chín mươi chín')
        self.assertEqual(dt.doc_tien(74.75,'HKD'),'bảy mươi tư đô Hồng Kông bảy mươi lăm')
        self.assertEqual(dt.doc_tien(12.6,'SGD'),'mười hai đô Singapore sáu mươi')
        self.assertEqual(dt.doc_tien(20,'USD'),'hai mươi đô'); self.assertEqual(dt.doc_tien(9.05,'USD'),'chín đô lẻ năm')
    def test_doc_the(self):
        self.assertEqual(dt.doc_the([{'menh_gia':10,'so_luong':2}],'USD'),'Hai thẻ mười đô')
        self.assertEqual(dt.doc_the([(10.0,1,1),(5.0,1,1),(1.0,1,1)],'USD'),'Một thẻ mười đô, một thẻ năm đô và một thẻ một đô')
        self.assertEqual(dt.doc_the([(80.0,1,1)],'HKD'),'Một thẻ tám mươi đô Hồng Kông'); self.assertEqual(dt.doc_the([(20.0,2,1)],'SGD'),'Hai thẻ hai mươi đô Singapore')
        self.assertEqual(dt.the_hien([(10.0,2,1)],'USD'),['$10','$10'])
    def test_han_va_vnd(self):
        d,h,c=dt.han_vn(END_OK); self.assertEqual((h,c),('5/11','ngày năm tháng mười một')); self.assertEqual(dt.doc_vnd(560000),'năm trăm sáu mươi nghìn')
        self.assertEqual(dt.doc_phien_ban('2.5'),'hai chấm năm'); self.assertEqual(dt.doc_phien_ban('1.05'),'một chấm không năm')

class Moc(unittest.TestCase):
    def test_free_update_anniversary(self):
        r=moc_tin.xet_tieu_de('Dragon Ball Xenoverse 2 - Official 10th Anniversary Free Update Trailer','DRAGON BALL XENOVERSE 2 Deluxe Edition')
        self.assertEqual(r['cau'],'Mà game vừa có bản cập nhật miễn phí mừng mười năm.'); self.assertEqual(r['chu'],'CẬP NHẬT MIỄN PHÍ MỪNG 10 NĂM')
    def test_free_update_tran(self): self.assertEqual(moc_tin.xet_tieu_de('Cyberpunk 2077 Free Update is out','Cyberpunk 2077')['chu'],'CẬP NHẬT MIỄN PHÍ')
    def test_update_so(self):
        r=moc_tin.xet_tieu_de('Cyberpunk 2077 - Update 2.5 now live','Cyberpunk 2077'); self.assertEqual((r['cau'],r['chu']),('Mà game vừa có bản cập nhật hai chấm năm.','UPDATE 2.5'))
        self.assertEqual(moc_tin.xet_tieu_de('Cyberpunk 2077 Free Update 2.5','Cyberpunk 2077')['chu'],'UPDATE 2.5 MIỄN PHÍ')
    def test_dlc_trailer(self): self.assertEqual(moc_tin.xet_tieu_de('Elden Ring - DLC Announcement Trailer','Elden Ring')['chu'],'BẢN MỞ RỘNG MỚI')
    def test_dlc_khong_trailer(self): self.assertIsNone(moc_tin.xet_tieu_de('Elden Ring - DLC review','Elden Ring'))
    def test_khong_khop_dong_game_khac(self):   # Legacy of Atlantis KHONG phai moc cho Tomb Raider Definitive Edition
        for t in ('Tomb Raider: Legacy of Atlantis - Official 30th Anniversary Teaser Trailer','Tomb Raider: Legacy of Atlantis Gets New Gameplay Sneak Peek','Tomb Raider: Legacy of Atlantis Free Update'):
            self.assertIsNone(moc_tin.xet_tieu_de(t,'Tomb Raider: Definitive Edition'),t)
        m=moc_tin.chon_moc('Tomb Raider: Definitive Edition',[{'tieu_de':'Tomb Raider: Legacy of Atlantis - Official 30th Anniversary Teaser Trailer','url':'u'}],{'la_thap_nhat':False,'so_ngay':5}); self.assertEqual(m['loai'],'khong')
    def test_khong_bat_dau_bang_ten(self): self.assertIsNone(moc_tin.xet_tieu_de('New Free Update for Cyberpunk 2077','Cyberpunk 2077'))
    def test_thap_nhat(self):
        m=moc_tin.chon_moc('X',[],{'la_thap_nhat':True,'so_ngay':9}); self.assertEqual((m['loai'],m['cau'],m['chu']),('thap_nhat','Đây là giá thấp nhất trong chín ngày Săn Game theo dõi.','THẤP NHẤT 9 NGÀY'))
        self.assertEqual(moc_tin.chon_moc('X',[],{'la_thap_nhat':True,'so_ngay':6})['loai'],'khong')
    def test_tin_uu_tien_hon_thap_nhat(self):
        m=moc_tin.chon_moc('Cyberpunk 2077',[{'tieu_de':'Cyberpunk 2077 Free Update','url':'https://u'}],{'la_thap_nhat':True,'so_ngay':9}); self.assertEqual((m['loai'],m['nguon']),('tin','https://u'))

class TenDayDu(unittest.TestCase):
    def test_deluxe(self):
        n='STAR WARS Jedi: Fallen Order Deluxe Edition'
        self.assertEqual(td.hien(n),'STAR WARS Jedi: Fallen Order Deluxe'); self.assertEqual(td.doc(n),'STAR WARS Jedi, Fallen Order bản Deluxe'); self.assertEqual(td.tach(n)[1],'Deluxe')
        self.assertEqual(td.doc('Dead Space Deluxe Edition'),'Dead Space bản Deluxe')
    def test_definitive_sau_hai_cham(self):
        self.assertEqual(td.hien('Tomb Raider: Definitive Edition'),'Tomb Raider Definitive'); self.assertEqual(td.doc('Tomb Raider: Definitive Edition'),'Tomb Raider bản Definitive')
    def test_ten_co_so_va_bo_ky_hieu(self):
        self.assertEqual(td.doc('Resident Evil 4 Gold Edition for PS5®'),'Resident Evil bốn bản Gold'); self.assertEqual(td.hien('Marvel’s Spider-Man 2 PS4 & PS5'),"Marvel's Spider-Man 2")
        self.assertEqual(td.doc('Mortal Kombat 11'),'Mortal Kombat mười một'); self.assertEqual(td.hien('Digital Deluxe Edition Dead Space'),'Digital Deluxe Edition Dead Space')
    def test_khong_phien_ban(self): self.assertEqual(td.tach('Elden Ring'),('Elden Ring','')); self.assertEqual(td.doc('Elden Ring'),'Elden Ring')
    def test_doc_duoc(self): self.assertTrue(td.doc_duoc('Resident Evil 4')); self.assertFalse(td.doc_duoc('NBA 2K27')); self.assertFalse(td.doc_duoc('FINAL FANTASY XVI'))
    def test_han_con_ngay(self):
        self.assertEqual(CF.han_con_ngay(END_OK,NGAY,'15:30'),8)   # 27/10 15:30 -> 5/11 14:59 = 8 ngay 23 gio (lam tron xuong)
        d,g,bo=0,0,0
    def test_loi_co_gia_goc_va_ngay_con(self):
        f=dict(vnd_doc='a',ten_doc='b',ma='US',giam=80,gia_doc='chín đô chín mươi chín',goc_doc='bốn mươi chín đô chín mươi chín',han_con_ngay=8,the_doc='Một thẻ mười đô',han_doc='ngày năm tháng mười một',moc=dict(loai='khong'))
        l=dict(lf.doan(f,NGAY)); self.assertEqual(l['gia'],'Game đang giảm tám mươi phần trăm trên PS Store Mỹ, từ bốn mươi chín đô chín mươi chín còn chín đô chín mươi chín.')
        self.assertEqual(l['han'],'Giảm giá tới ngày năm tháng mười một, còn tám ngày nữa.'); self.assertEqual(dict(lf.doan(dict(f,han_con_ngay=1),NGAY))['han'],'Giảm giá tới ngày năm tháng mười một.')
    def test_qua_ngan_bi_loai(self):
        f=dict(vnd_doc='a',ten_doc='b',ma='US',giam=80,gia_doc='c',goc_doc='g',han_con_ngay=0,the_doc='x',han_doc='y',moc=dict(loai='khong'))
        ds,g,bo=lf.lap_loi(f,NGAY); self.assertIsNone(ds); self.assertLess(g,16)

class KieuMo(unittest.TestCase):
    def test_xoay_7_ngay_khong_trung(self):
        f=dict(vnd_doc='năm trăm sáu mươi nghìn',ten_doc='Cyberpunk hai không bảy bảy'); d0=datetime.date(2026,10,21)
        ks=[lf.kieu_mo((d0+datetime.timedelta(days=i)).isoformat()) for i in range(7)]; self.assertEqual(sorted(ks),list(range(7)))
        cs=[lf.cau_mo(f,k) for k in ks]; self.assertEqual(len(set(cs)),7)
        for c in cs: self.assertTrue(c.lower().startswith(('năm trăm','chỉ năm trăm')))   # so tien dung dau cau
    def test_loi_day_du(self):
        f=dict(vnd_doc='a',ten_doc='b',ma='US',giam=60,gia_doc='c',goc_doc='g',han_con_ngay=8,the_doc='Hai thẻ mười đô',han_doc='ngày năm tháng mười một',moc=dict(loai='tin',cau='Mà game vừa có.'))
        ds=lf.doan(f,NGAY); self.assertEqual([k for k,_ in ds],['mo','gia','the','moc','han','vung','ket']); self.assertEqual(ds[-1][1],'Săn Game: săn đúng kèo, chơi đỡ nghèo!')
        self.assertEqual([k for k,_ in lf.doan(dict(f,moc=dict(loai='khong')),NGAY)],['mo','gia','the','han','vung','ket'])
    def test_do_dai_qua_26_bi_loai(self):
        f=dict(vnd_doc='năm trăm sáu mươi nghìn',ten_doc=' '.join(['Supercalifragilistic']*40),ma='US',giam=60,gia_doc='c',goc_doc='g',the_doc='Hai thẻ mười đô',han_doc='ngày năm',moc=dict(loai='khong'))
        ds,g,bo=lf.lap_loi(f,NGAY); self.assertIsNone(ds); self.assertGreater(g,26)
    def test_qua_25_bo_moc(self):
        f=dict(vnd_doc='năm trăm sáu mươi nghìn',ten_doc='Cyberpunk',ma='US',giam=60,gia_doc='c',goc_doc='g',the_doc='Hai thẻ mười đô',han_doc='ngày năm',moc=dict(loai='tin',cau=' '.join(['từ']*80)))
        ds,g,bo=lf.lap_loi(f,NGAY); self.assertTrue(bo)   # >25 s -> bo moc (con lai co the < 16 s -> None)

class Loc(unittest.TestCase):
    def kq(self,r,html=None,**kw): return chon(r,trang(PID) if html is None else html,**kw).xet(r)
    def test_dat(self):
        f,ly=self.kq(dong()); self.assertIsNone(ly)
        self.assertEqual((f['gia_hien'],f['goc_hien'],f['giam'],f['gia_vnd_hien'],f['the_hien'],f['han_hien']),('$19,99','$49,99',60,'560.000đ',['$10','$10'],'5/11')); self.assertEqual(f['moc']['loai'],'khong')
    def test_vung_in_ua_va_nen_tang(self):
        c=chon([]); self.assertIn('IN',c.xet(dong(ma='IN'))[1]); self.assertIn('vùng UA',c.xet(dong(vung_re_nhat='UA'))[1]); self.assertIn('PS',c.xet(dong(nen_tang='xbox'))[1])
    def test_cac_cong_loc_dau(self):
        c=chon([]); self.assertIn('kiểm trang',c.xet(dong(da_kiem_trang=False))[1]); self.assertIn('lệch giá',c.xet(dong(lech_gia=True))[1]); self.assertIn('cách quy',c.xet(dong(cach_quy='ngan_hang'))[1]); self.assertIn('< 30',c.xet(dong(giam=20))[1])
    def test_endtime_gan_gio_dang(self):   # hết trước giờ đăng + 6h (15:30 + 6h = 21:30 VN) -> loại
        sat=str(int(datetime.datetime(2026,10,27,21,0,tzinfo=dt.VN).timestamp()*1000)); f,ly=self.kq(dong(),trang(PID,end=sat)); self.assertIsNone(f); self.assertIn('hết hạn sớm',ly)
        ok=str(int(datetime.datetime(2026,10,27,21,31,tzinfo=dt.VN).timestamp()*1000)); self.assertIsNone(self.kq(dong(),trang(PID,end=ok))[1])
    def test_khong_endtime(self): self.assertIn('endTime',self.kq(dong(),trang(PID,end=None))[1])
    def test_thieu_gia_goc_bo_game(self):   # auto-post-claim-guard: trang khong cho gia goc -> bo game, khong lay % cua bang
        f,ly=self.kq(dong(),trang(PID,goc=None)); self.assertIsNone(f); self.assertIn('giá gốc',ly)
    def test_giam_lay_tu_trang_va_canh_bao_lech(self):
        c=chon(dong(giam=60),trang(PID,con=19.99,goc=39.99)); f,ly=c.xet(dong(giam=60)); self.assertIsNone(ly); self.assertEqual(f['giam'],50); self.assertEqual(f['giam_bang'],60); self.assertTrue(any('CANH BAO' in x for x in c.canh_bao))
    def test_gia_trang_lech_bang(self): self.assertIn('lệch giá bảng',self.kq(dong(gia='$25.00'))[1])
    def test_tien_te_sai(self): self.assertIn('tiền tệ',self.kq(dong(),trang(PID,tien='HKD'))[1])
    def test_trung_3_ngay(self): self.assertIn('đã nổi bật',self.kq(dong(),nb=NBTrung())[1])
    def test_the_khong_khit(self):
        self.assertIn('không vừa khít',self.kq(dong(),kq=dict(THE_OK,thua=5.25,tong_menh_gia=80.0))[1])
        self.assertIsNone(self.kq(dong(),kq=dict(THE_OK,thua=0.8,tong_menh_gia=20.0))[1])   # 4% -> khit
    def test_the_qua_nhieu_tam_hoac_le_nghin(self):
        self.assertIn('tấm',self.kq(dong(),kq=dict(THE_OK,the=[(1.0,5,36000.0)],thua=0.01))[1]); self.assertIn('tròn nghìn',self.kq(dong(),kq=dict(THE_OK,vnd=560500))[1])
    def test_the_ngan_hang(self): self.assertIn('không quy được bằng thẻ',self.kq(dong(),kq=dict(THE_OK,cach='ngan_hang',mua_duoc=False,ly_do='giá thẻ cũ'))[1])
    def test_khong_video(self):
        self.assertIn('không có video',self.kq(dong(),trang(PID,video=False))[1])
        f,ly=self.kq(dong(),trang(PID,video=False),steam=lambda t:[{'url':'https://steam/v.mp4','app_id':1,'ten':'x'}]); self.assertIsNone(ly); self.assertEqual(f['nguon_video'],'steam')
    def test_chon_uu_tien_moc_trong_3_hang(self):
        tin={'diem':80,'mau':[{'tieu_de':'Elden Ring Free Update 1.2','url':'https://u'}]}
        a=dong(hang=1,ten='Red Dead Redemption 2',pid=PID); b=dong(hang=3,ten='Elden Ring',pid='UP0001-PPSA00001_00-ELDEN',nong=tin)
        c=chon([a,b],lambda loc,pid:trang(pid)); self.assertEqual(c.chon()['ten_goc'],'Elden Ring')
        b2=dong(hang=5,ten='Elden Ring',pid='UP0001-PPSA00001_00-ELDEN',nong=tin)   # cach 4 hang -> khong uu tien
        self.assertEqual(chon([a,b2],lambda loc,pid:trang(pid)).chon()['ten_goc'],'Red Dead Redemption 2')
    def test_het_ung_vien(self):
        with self.assertRaises(CF.Thoat): chon([dong(ma='IN')],trang(PID)).chon()

class FailClosed(unittest.TestCase):
    def dung(self,d,gia_the_ngay=NGAY,keo_ngay=NGAY):
        d=pathlib.Path(d); (d/'repo'/'du-lieu').mkdir(parents=True)
        (d/'repo'/'deal_diem.py').write_text("def gia_the_con_han(g,n):\n    import datetime\n    return (datetime.date.fromisoformat(n)-datetime.date.fromisoformat(g['ngay'])).days<=7\ndef quy_vnd(*a,**k): raise RuntimeError('khong goi')\n")
        json.dump({'ngay':gia_the_ngay,'ty_gia_ngan_hang':{},'vung':{}},open(d/'repo'/'du-lieu'/'gia-the.json','w'))
        json.dump({'ngay':keo_ngay,'keo':[]},open(d/'keo.json','w')); return dict(DU_LIEU_REPO=str(d/'repo'),KEO_FILE=str(d/'keo.json'),NGAY=NGAY,GIO_DANG='15:30')
    def chay(self,env,sua=None):
        cu=CF.T
        with tempfile.TemporaryDirectory() as t2:
            CF.T=pathlib.Path(t2)
            try: ma=CF.main([],env); kq=json.load(open(pathlib.Path(t2)/'ket-qua-chon.json'))
            finally: CF.T=cu
        return ma,kq
    def test_bang_sai_ngay(self):
        with tempfile.TemporaryDirectory() as d: ma,kq=self.chay(self.dung(d,keo_ngay='2026-10-26'))
        self.assertEqual(ma,3); self.assertIn('sai ngày',kq['ly_do'])
    def test_gia_the_cu(self):
        with tempfile.TemporaryDirectory() as d: ma,kq=self.chay(self.dung(d,gia_the_ngay='2026-10-10'))
        self.assertEqual(ma,3); self.assertIn('giá thẻ cũ',kq['ly_do'])
    def test_lich_su_loi_mang(self):   # khong doc duoc lich su trung -> THOAT 3, khong chon bua
        with tempfile.TemporaryDirectory() as d:
            env=self.dung(d); env['NOI_BAT_LICH_SU']=str(pathlib.Path(d)/'khong-co.json')
            cu=os.environ.get('NOI_BAT_LICH_SU'); os.environ['NOI_BAT_LICH_SU']=env['NOI_BAT_LICH_SU']
            try: ma,kq=self.chay(env)
            finally:
                if cu is None: os.environ.pop('NOI_BAT_LICH_SU',None)
                else: os.environ['NOI_BAT_LICH_SU']=cu
        self.assertEqual(ma,3); self.assertIn('lịch sử trùng',kq['ly_do'])
    def test_thieu_bang(self):
        with tempfile.TemporaryDirectory() as d:
            env=self.dung(d); env['KEO_FILE']=str(pathlib.Path(d)/'khong.json'); ma,kq=self.chay(env)
        self.assertEqual(ma,3)

class DealDiemThat(unittest.TestCase):
    """Neu may co repo du lieu: tinh to hop the that. Khong co -> bo qua (CI khong checkout repo rieng tu)."""
    def test_vua_khit(self):
        repo=next((pathlib.Path(p) for p in (os.environ.get('DU_LIEU_REPO'),) if p and (pathlib.Path(p)/'deal_diem.py').exists()),None)
        if not repo: self.skipTest('khong co DU_LIEU_REPO')
        sys.modules.pop('deal_diem',None); sys.modules.pop('nguon',None); sys.path.insert(0,str(repo)); import deal_diem
        g=json.load(open(repo/'du-lieu'/'gia-the.json')); th,ly=CF.danh_gia_the('US',19.99,'USD',g,g['ngay'],deal_diem)
        self.assertIsNone(ly); self.assertEqual((dt.so_tam(th['the']),th['vnd']%1000),(2,0))
if __name__=='__main__': unittest.main()
