# Test cong-cu/gia_trang.py (Sol bcd #14 #15): khoi gia/han/media cua DUNG pid. Fixture = JSON toi gian, cung cau truc trang PS Store that
# (<script id="env:..."> -> {"cache": {"GameCTA:ADD_TO_CART:ADD_TO_CART:<PID>-<SKU>:OUTRIGHT": {"price": {...}}, "Product:<PID>": {...}}}).
import importlib.util,json,pathlib,unittest
_f=pathlib.Path(__file__).resolve().parents[1]/'gia_trang.py'
_sp=importlib.util.spec_from_file_location('gia_trang_test',str(_f)); GT=importlib.util.module_from_spec(_sp); _sp.loader.exec_module(GT)
PID='UP1001-PPSA36393_00-MAFIA1DEPS500000'; GOIY='UP1001-CUSA18097_00-MAFIAONEREMASTER'
END='1792594740000'
def gia(chuoi,gia_tri,goc='HK$318.00',goc_tri=31800,end=END,tien='HKD'):
    return {'__typename':'Price','basePrice':goc,'discountedPrice':chuoi,'basePriceValue':goc_tri,'discountedValue':gia_tri,'currencyCode':tien,'endTime':end}
def cta(pid,sku,price,loai='ADD_TO_CART',hau='OUTRIGHT'):
    return {f'GameCTA:{loai}:{loai}:{pid}-{sku}'+(f':{hau}' if hau else ''):{'__typename':'GameCTA','price':price}}
def trang(*cache,them=''):
    out='<html>'
    for c in cache: out+='<script id="env:abc" type="application/json">'+json.dumps({'cache':c})+'</script>'
    return out+them+'</html>'
class KhoiGia(unittest.TestCase):
    def test_doc_dung_khoi_pid_va_endtime_cua_chinh_khoi(self):
        k=GT.khoi_gia(trang(cta(PID,'H002',gia('HK$47.70',4770))),PID)
        self.assertEqual((k['gia_cuc_bo'],k['gia_goc'],k['tien_te'],k['endTime'],k['sku']),(47.7,318.0,'HKD',END,'H002'))
    def test_khoi_lap_o_nhieu_the_script_van_la_mot(self):
        c=cta(PID,'H002',gia('HK$47.70',4770)); self.assertEqual(GT.khoi_gia(trang(c,c,c),PID)['gia_cuc_bo'],47.7)
    def test_idr_khong_phan_le(self):
        k=GT.khoi_gia(trang(cta(PID,'H007',gia('Rp\xa063,270',63270,'Rp\xa0253,080',253080,tien='IDR'))),PID); self.assertEqual((k['gia_cuc_bo'],k['tien_te']),(63270.0,'IDR'))
    def test_sku_chinh_khong_endtime_thi_khong_muon_han_cua_doi_tuong_khac(self):   # Sol #14: code cu nhan han o doi tuong khac tren trang
        html=trang(cta(PID,'H002',gia('HK$47.70',4770,end=None)),cta(GOIY,'H004',gia('HK$47.70',4770)),them='"endTime":"%s"'%END)
        k=GT.khoi_gia(html,PID); self.assertIsNotNone(k); self.assertIsNone(k['endTime'])   # endTime None -> ben goi loai
    def test_trang_chi_co_khoi_cua_san_pham_khac_thi_khong_nhan(self):   # Sol #15: code cu regex toan trang nhan khoi khong chua pid
        self.assertIsNone(GT.khoi_gia(trang(cta(GOIY,'H004',gia('HK$47.70',4770))),PID))
    def test_nhieu_khoi_mua_dut_khac_gia_cho_cung_pid_thi_mo_ho(self):
        self.assertIsNone(GT.khoi_gia(trang(cta(PID,'H002',gia('HK$47.70',4770)),cta(PID,'H003',gia('HK$99.00',9900))),PID))
        self.assertIsNone(GT.khoi_gia(trang(cta(PID,'H002',gia('HK$47.70',4770)),cta(PID,'H003',gia('HK$47.70',4770,end=None))),PID))   # cung gia khac han
    def test_khong_nhan_pid_co_tien_to_trung_va_cta_khong_phai_mua_dut(self):
        self.assertIsNone(GT.khoi_gia(trang(cta(PID+'XX','H001',gia('HK$47.70',4770))),PID))        # pid dai hon bat dau bang pid
        self.assertIsNone(GT.khoi_gia(trang(cta(PID+'-C','H001',gia('HK$47.70',4770))),PID))        # sku co them dau '-'
        self.assertIsNone(GT.khoi_gia(trang(cta(PID,'H001',gia('HK$47.70',4770),hau='SUBSCRIPTION')),PID))
    def test_game_ps4_cusa_khoa_khong_co_hau_to_outright(self):   # thay tren trang that: GameCTA:ADD_TO_CART:ADD_TO_CART:UP0006-CUSA07995_00-ASIAPLACEHOLDER0-H001
        ps4='UP0006-CUSA07995_00-ASIAPLACEHOLDER0'
        up={'GameCTA:UPSELL_EA_ACCESS_FREE:ADD_TO_CART:'+ps4+'-H001:HP5395-CUSA15164_00-0OLOB22BLSK39PD6':{'price':gia('Included',0)}}
        k=GT.khoi_gia(trang(cta(ps4,'H001',gia('HK$63.00',6300),hau=None),up),ps4); self.assertEqual((k['gia_cuc_bo'],k['endTime'],k['sku']),(63.0,END,'H001'))
    def test_nut_upsell_ps_plus_va_demo_khong_phai_khoi_mua_dut(self):   # trang Returnal: UPSELL_PS_PLUS_GAME_CATALOG 'Included' cung pid
        up={f'GameCTA:UPSELL_PS_PLUS_GAME_CATALOG:ADD_TO_CART:{PID}-H004:SUB001-SUBC00002_00-X':{'price':gia('HK$1.00',100)},f'GameCTA:DOWNLOAD_DEMO:BACKGROUND_PURCHASE_AND_DOWNLOAD:{PID}-H001':{'price':gia('HK$2.00',200)}}
        self.assertIsNone(GT.khoi_gia(trang(up),PID))
        self.assertEqual(GT.khoi_gia(trang(up,cta(PID,'H004',gia('HK$47.70',4770))),PID)['gia_cuc_bo'],47.7)
    def test_gia_khong_doc_duoc_hoac_lech_gia_tri_cache(self):
        self.assertIsNone(GT.khoi_gia(trang(cta(PID,'H001',gia('Included',0))),PID))
        self.assertIsNone(GT.khoi_gia(trang(cta(PID,'H001',gia('HK$47.70',9999))),PID))
    def test_json_hong_va_pid_rong_khong_no(self):
        self.assertIsNone(GT.khoi_gia('<script id="env:x">{khong phai json</script>',PID)); self.assertIsNone(GT.khoi_gia('',PID)); self.assertIsNone(GT.khoi_gia(None,PID)); self.assertIsNone(GT.khoi_gia(trang({}),''))
class KhoiKhop(unittest.TestCase):
    def test_khop_du_lieu_va_dang_giam(self):
        k,ly=GT.khoi_khop(trang(cta(PID,'H002',gia('HK$47.70',4770))),PID,'HK$47.70'); self.assertEqual((k['gia_cuc_bo'],ly),(47.7,None))
        k,ly=GT.khoi_khop(trang(cta(PID,'H002',gia('HK$47.70',4770))),PID,48.0); self.assertIsNotNone(k)   # lech <= 2%
    def test_loai_khi_lech_gia_hoac_khong_giam_hoac_mo_ho(self):
        h=trang(cta(PID,'H002',gia('HK$47.70',4770)))
        self.assertIsNone(GT.khoi_khop(h,PID,'HK$60.00')[0]); self.assertIsNone(GT.khoi_khop(h,PID,None)[0])
        self.assertIsNone(GT.khoi_khop(trang(cta(PID,'H002',gia('HK$318.00',31800))),PID,'HK$318.00')[0])   # goc == con
        self.assertIsNone(GT.khoi_khop(trang(cta(GOIY,'H004',gia('HK$47.70',4770))),PID,'HK$47.70')[0])      # khoi khong chua pid
class Media(unittest.TestCase):
    def test_chi_lay_media_cua_product_pid_ke_ca_personalizedMeta(self):
        v=lambda u:{'type':'VIDEO','role':'PREVIEW','url':'https://vulcan.dl.playstation.net/img/'+u+'.mp4'}
        s=lambda u:{'type':'IMAGE','role':'SCREENSHOT','url':'https://image.api.playstation.com/'+u+'.jpg'}
        m=lambda u:{'type':'IMAGE','role':'MASTER','url':'https://image.api.playstation.com/'+u+'.png'}
        html=trang({f'Product:{PID}':{'media':[s('a'),m('bia')],'personalizedMeta':{'media':[v('dung')]}},f'Product:{GOIY}':{'media':[v('khac'),s('khac')]}})
        r=GT.media(html,PID); self.assertEqual(len(r['video']),1); self.assertTrue(r['video'][0].endswith('dung.mp4')); self.assertEqual(len(r['anh_chup']),1); self.assertTrue(r['anh'].endswith('bia.png'))
        e=GT.media(trang({f'Product:{GOIY}':{'media':[v('khac')]}}),PID); self.assertEqual((e['video'],e['anh_chup'],e['anh']),([],[],None))
class DocGia(unittest.TestCase):
    def test_doc_gia_theo_locale(self):
        for s,v in [('HK$47.70',47.7),('1.234.000₫',1234000),('Rp 1.299.000',1299000),('₹1,299',1299),('1,299.00',1299),('47,70',47.7),('$ 1.299,50',1299.5),('Rp\xa063,270',63270)]: self.assertEqual(GT.doc_gia(s),v,s)
        self.assertIsNone(GT.doc_gia('Included'))

class ThongTinGame(unittest.TestCase):       # 11/10: gioi thieu game — Product:<pid> bi chia manh o nhieu the script (that: starRating o the A, genres o the B, edition.features + descriptions o the C)
    def test_hop_nhat_cac_manh_product_cua_dung_pid(self):
        a={f'Product:{PID}':{'starRating':{'averageRating':4.37,'totalRatingsCount':27172}}}
        b={f'Product:{PID}':{'localizedGenres':[{'value':'Shooter'},{'value':'Shooter'}],'edition':{'name':'Digital Deluxe Edition','type':'PREMIUM','features':['Game','A weapon.\u00b9']}}}
        c={f'Product:{PID}':{'edition':{'name':'Digital Deluxe Edition'},'descriptions':[{'type':'SHORT','value':'ngan'},{'type':'LONG','value':'dai <br/>- x'}]},f'Product:{GOIY}':{'starRating':{'averageRating':1.0,'totalRatingsCount':999}}}
        t=GT.thong_tin_game(trang(a,b,c),PID)
        self.assertEqual(t['diem'],{'tb':4.37,'so_luot':27172}); self.assertEqual(t['the_loai'],['Shooter','Shooter'])
        self.assertEqual((t['edition']['ten'],t['edition']['loai'],t['edition']['tinh_nang']),('Digital Deluxe Edition','PREMIUM',['Game','A weapon.\u00b9']))
        self.assertEqual((t['mo_ta_ngan'],t['mo_ta_dai']),('ngan','dai <br/>- x'))
    def test_thieu_truong_thi_rong_khong_doan(self):
        t=GT.thong_tin_game(trang({f'Product:{PID}':{'name':'X'}}),PID); self.assertEqual((t['the_loai'],t['diem'],t['edition'],t['mo_ta_dai']),([],None,None,''))
        self.assertEqual(GT.thong_tin_game('<html></html>',PID)['diem'],None); self.assertEqual(GT.thong_tin_game(None,PID)['the_loai'],[])
    def test_khong_nhan_diem_cua_san_pham_khac(self):
        self.assertIsNone(GT.thong_tin_game(trang({f'Product:{GOIY}':{'starRating':{'averageRating':1.0,'totalRatingsCount':999}}}),PID)['diem'])
    def test_hop_nhat_nhieu_trang_lay_truong_dau_tien(self):
        h=GT.hop_nhat_thong_tin([dict(the_loai=[],diem=None,edition=None,mo_ta_dai='',mo_ta_ngan=''),dict(the_loai=['Action'],diem={'tb':4.0,'so_luot':300},edition=None,mo_ta_dai='B',mo_ta_ngan=''),dict(the_loai=['Puzzle'],diem=None,edition=None,mo_ta_dai='C',mo_ta_ngan='D')])
        self.assertEqual((h['the_loai'],h['diem']['so_luot'],h['mo_ta_dai'],h['mo_ta_ngan']),(['Action'],300,'B','D'))
    def test_p2_hop_nhat_theo_truong_trong_cung_san_pham(self):      # Sol: manh dau chi co SHORT + averageRating, manh sau co LONG + totalRatingsCount -> khong mat du lieu
        a={f'Product:{PID}':{'descriptions':[{'type':'SHORT','value':'ngan'}],'starRating':{'averageRating':4.2}}}
        b={f'Product:{PID}':{'descriptions':[{'type':'SHORT','value':''},{'type':'LONG','value':'dai'}],'starRating':{'averageRating':4.9,'totalRatingsCount':500}}}
        t=GT.thong_tin_game(trang(a,b),PID); self.assertEqual((t['mo_ta_ngan'],t['mo_ta_dai'],t['diem']),('ngan','dai',{'tb':4.2,'so_luot':500}))
    def test_p2_khong_ghep_edition_cua_trang_nay_voi_mo_ta_trang_khac(self):
        deluxe=dict(the_loai=[],diem=None,edition=dict(ten='Deluxe Edition',loai='PREMIUM',tinh_nang=[]),mo_ta_dai='',mo_ta_ngan='')
        std=dict(the_loai=['Action'],diem={'tb':4.0,'so_luot':300},edition=dict(ten='Standard Edition',loai='',tinh_nang=[]),mo_ta_dai='LONG STANDARD',mo_ta_ngan='')
        h=GT.hop_nhat_thong_tin([deluxe,std],['en-us','en-hk']); self.assertEqual((h['mo_ta_dai'],h['the_loai'],h['diem']),('','',None) if False else ('',[],None)); self.assertEqual(h['edition']['ten'],'Deluxe Edition')
        d2=dict(deluxe,the_loai=['Action'],mo_ta_dai='LONG DELUXE'); h=GT.hop_nhat_thong_tin([deluxe,d2],['en-us','en-hk']); self.assertEqual((h['mo_ta_dai'],h['nguon_truong']['mo_ta_dai'],h['nguon_truong']['edition']),('LONG DELUXE','en-hk','en-us'))

if __name__=='__main__': unittest.main()

class PsPlusCatalog(unittest.TestCase):   # Opus 11/10: Keo thom loai game co trong PS Plus Game Catalog
    def up(self,pid): return {f'GameCTA:UPSELL_PS_PLUS_GAME_CATALOG:ADD_TO_CART:{pid}-H004:SUB001-SUBC00002_00-X':{'price':gia('Included',0)}}
    def test_nut_upsell_ps_plus_cua_dung_pid(self):
        self.assertTrue(GT.ps_plus_catalog(trang(self.up(PID),cta(PID,'H004',gia('HK$47.70',4770))),PID))
    def test_upsell_cua_san_pham_khac_hoac_khong_co_thi_khong(self):   # trang Returnal DDE co upsell cua ban RETURNALGAME0001, khong phai DDE
        self.assertFalse(GT.ps_plus_catalog(trang(self.up(GOIY),cta(PID,'H004',gia('HK$47.70',4770))),PID))
        self.assertFalse(GT.ps_plus_catalog(trang(cta(PID,'H004',gia('HK$47.70',4770))),PID))
        self.assertFalse(GT.ps_plus_catalog(trang(self.up(PID+'XX')),PID)); self.assertFalse(GT.ps_plus_catalog(None,PID))
    def test_nut_ea_access_khong_tinh(self):
        self.assertFalse(GT.ps_plus_catalog(trang({f'GameCTA:UPSELL_EA_ACCESS_FREE:ADD_TO_CART:{PID}-H001:X':{'price':gia('Included',0)}}),PID))


# ---- G3 (13/10) biet_truoc: fixture = TRANG THAT Sniper Elite 5 Complete Edition (en-us, 13/10/2026) cat con CHU toi thieu (khong anh/trailer Sony): cung khoa/cau truc, cung chuoi thong bao (co NBSP trong «PS Plus»)
SNIPER='UP4363-PPSA01685_00-SNIPERELITE500CE'; SP02='UP4363-PPSA01685_00-SNIPERELITE5SP02'
THONG_BAO_THAT='PS\xa0Plus required for online play<br/>Supports up to 16 online players with PS Plus<br/>In-game purchases optional<br/>Online play optional<br/>Vibration function and trigger effect supported (DualSense wireless controller)<br/>1 players'
NGON_NGU_THAT=['es','zh','fr','ja','ru','de','pl','it','pt_BR','en','ko','ch','pt']
def sp(pid,**kw): return {f'Product:{pid}':dict(id=pid,**kw)}
def mo_ta(tp,v): return dict(type=tp,subType='NONE',value=v)
def trang_that(**kw):
    return trang(sp(SNIPER,descriptions=[mo_ta('LEGAL','To play this game on PS5...'),mo_ta('LONG','Sniper Elite 5 Complete Edition includes the base game'),mo_ta('COMPATIBILITY_NOTICE',kw.get('tb',THONG_BAO_THAT))]),
                 sp(SNIPER,screenLanguages=kw.get('sl',NGON_NGU_THAT),spokenLanguages=kw.get('sp',['en'])),
                 # nhieu: san pham KHAC (season pass / goi y) co thong bao + ngon ngu khac; bang dich (khoa khac) chua cung chuoi
                 sp(SP02,screenLanguages=['vi','en'],descriptions=[mo_ta('COMPATIBILITY_NOTICE','Online play required<br/>Supports up to 8 online players<br/>PS Plus required for online play')]),
                 {'Translations:en-us':{'a':'Online play required','b':'PS Plus required for online play','c':'Supports up to 99 online players'}})
class BietTruoc(unittest.TestCase):
    def test_trang_that_sniper_elite_5(self):
        r=GT.biet_truoc(trang_that(),SNIPER)
        self.assertEqual((r['online'],r['can_plus_online'],r['so_nguoi_online'],r['mua_them']),('tuy_chon',True,16,True))
        self.assertEqual(r['screenLanguages'],NGON_NGU_THAT); self.assertEqual(r['spokenLanguages'],['en']); self.assertNotIn('vi',r['screenLanguages'])
    def test_chi_doc_dung_san_pham_khong_do_toan_html_va_bang_dich(self):
        r=GT.biet_truoc(trang_that(),SP02); self.assertEqual((r['online'],r['so_nguoi_online'],r['screenLanguages']),('bat_buoc',8,['vi','en']))       # san pham khac -> gia tri cua CHINH no
        r=GT.biet_truoc(trang_that(tb='Online play optional'),SNIPER); self.assertEqual((r['online'],r['can_plus_online'],r['so_nguoi_online']),('tuy_chon',None,None))   # bang dich / SP02 co 'PS Plus required' + '8 players' khong lan sang
    def test_khoang_trang_dac_biet_va_ba_dang_br(self):
        for tb in ('PS\u00a0Plus required for online play<br/>Online play optional','PS\u202fPlus  required for online play<BR>Online\u00a0play\u00a0optional','ps plus required for online play\nOnline play optional'):
            r=GT.biet_truoc(trang_that(tb=tb),SNIPER); self.assertEqual((r['online'],r['can_plus_online']),('tuy_chon',True),tb)
    def test_online_bat_buoc_va_khong_online(self):
        r=GT.biet_truoc(trang_that(tb='Online play required<br/>PS Plus required for online play'),SNIPER); self.assertEqual((r['online'],r['can_plus_online']),('bat_buoc',True))
        self.assertEqual(GT.biet_truoc(trang_that(tb='Online play not supported<br/>1 players'),SNIPER)['online'],'khong')
    def test_phu_de_viet(self):
        r=GT.biet_truoc(trang_that(sl=['vi','en','ja']),SNIPER); self.assertIn('vi',r['screenLanguages'])
    def test_thieu_thi_none_khong_doan(self):
        r=GT.biet_truoc(trang(sp(SNIPER,descriptions=[mo_ta('LONG','x')])),SNIPER)
        self.assertEqual(r,dict(screenLanguages=None,spokenLanguages=None,online=None,can_plus_online=None,so_nguoi_online=None,mua_them=None))
        r=GT.biet_truoc(trang_that(tb='In-game purchases optional<br/>1 players',sl=[]),SNIPER)
        self.assertEqual((r['online'],r['can_plus_online'],r['so_nguoi_online'],r['screenLanguages'],r['mua_them']),(None,None,None,None,True))
        for h,pid in ((trang_that(),'UP0000-NOPE_00-X'),('',SNIPER),(None,SNIPER),(trang_that(),'')): self.assertIsNone(GT.biet_truoc(h,pid)['online'])
    def test_notice_loai_khac_khong_tinh_va_json_hong_khong_no(self):
        h=trang(sp(SNIPER,descriptions=[mo_ta('LONG','Online play required<br/>PS Plus required for online play<br/>Supports up to 4 online players')]))+'<script id="env:x">{xau</script>'
        r=GT.biet_truoc(h,SNIPER); self.assertEqual((r['online'],r['can_plus_online'],r['so_nguoi_online']),(None,None,None))
    def test_hai_vung_khac_ngon_ngu_lay_dung_tung_trang(self):       # chon-keo lay trang cua vung re nhat, khong bu tu vung khac
        us=GT.biet_truoc(trang_that(sl=['en','es']),SNIPER); hk=GT.biet_truoc(trang_that(sl=['vi','en','zh']),SNIPER)
        self.assertNotIn('vi',us['screenLanguages']); self.assertIn('vi',hk['screenLanguages'])

