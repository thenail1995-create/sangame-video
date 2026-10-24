# Test cong-cu/video_steam.py (24/10/2026): tim video Steam cho game PS Store khong co media video. DU LIEU GIA, khong goi mang.
import importlib.util,pathlib,unittest
_sp=importlib.util.spec_from_file_location('video_steam_test',str(pathlib.Path(__file__).resolve().parents[1]/'video_steam.py')); VS=importlib.util.module_from_spec(_sp); _sp.loader.exec_module(VS)

def item(id_,ten,tp='app'): return {'type':tp,'name':ten,'id':id_}
def tim(items): return {'total':len(items),'items':items}
def mv(*ten,app=1):
    return {str(app):{'success':True,'data':{'movies':[{'id':i,'name':t,'hls_h264':f'https://video.akamai.steamstatic.com/store_trailers/{app}/{i}/hls_264_master.m3u8?t=1'} for i,t in enumerate(ten,1)]}}}
def gia_lap(search,movies=None):
    """lay_json gia: storesearch -> search, appdetails -> movies[app_id]."""
    def f(url):
        if 'storesearch' in url: return search
        return movies or {}
    return f

class ChuanHoa(unittest.TestCase):
    def test_bo_nhan_hieu_nen_tang_va_ban(self):
        self.assertEqual(VS.chuan_hoa('RESIDENT EVIL 5'),'resident evil 5')
        self.assertEqual(VS.chuan_hoa('Ultra Street Fighter® IV'),'ultra street fighter 4')
        self.assertEqual(VS.chuan_hoa('Shadow of the Tomb Raider: Definitive Edition'),VS.chuan_hoa('Shadow of the Tomb Raider for PS5™'))
        self.assertEqual(VS.chuan_hoa('Marvel & Co PS4 & PS5'),'marvel and co')
    def test_giong(self):
        self.assertGreaterEqual(VS.giong('RESIDENT EVIL 5','Resident Evil 5'),0.99)
        self.assertLess(VS.giong('Resident Evil 5','Resident Evil 4'),VS.NGUONG); self.assertGreaterEqual(VS.giong('Ultra Street Fighter IV','Ultra Street Fighter® 4'),0.99)
        self.assertEqual(VS.giong('','x'),0.0)
    def test_la_game_goc(self):
        for x in ('Resident Evil 5 - UNTOLD STORIES BUNDLE','Game Soundtrack','Game Upgrade','Game Weapon Exclusive Upgrade Ticket x5 (A)','Game DLC','Game Season Pass','Game Demo'):
            self.assertFalse(VS.la_game_goc(x),x)
        for x in ('Resident Evil 5','Risk of Rain 2','Ultra Street Fighter® IV'): self.assertTrue(VS.la_game_goc(x),x)

class TimApp(unittest.TestCase):
    def test_chon_game_goc_khong_nhan_bundle_va_ve(self):
        s=tim([item(352000,'Resident Evil 5 - UNTOLD STORIES BUNDLE'),item(2197328,'Resident Evil 4 Weapon Exclusive Upgrade Ticket x5 (A)'),item(21690,'Resident Evil 5')])
        self.assertEqual(VS.tim_app('RESIDENT EVIL 5',gia_lap(s))['id'],21690)
    def test_khong_khop_thi_none(self):   # inFAMOUS Second Son khong co tren Steam: ket qua tim kiem la game khac
        s=tim([item(1,'Infamous Mod Tool'),item(2,'Second Son Racing'),item(3,'Famous Cooking')])
        self.assertIsNone(VS.tim_app('inFAMOUS Second Son',gia_lap(s)))
    def test_chi_nhan_type_app_va_chon_giong_nhat(self):
        s=tim([item(5,'Risk of Rain 2','dlc'),item(6,'Risk of Rain 2 Dedicated Server'),item(632360,'Risk of Rain 2')])
        self.assertEqual(VS.tim_app('Risk of Rain 2',gia_lap(s))['id'],632360)
    def test_loi_mang_hoac_rong_thi_none(self):
        self.assertIsNone(VS.tim_app('x',lambda u:None)); self.assertIsNone(VS.tim_app('x',lambda u:{}))
    def test_ban_dac_biet_van_khop(self):   # PS Store ghi ten ngan, Steam ghi Definitive Edition
        s=tim([item(750920,'Shadow of the Tomb Raider: Definitive Edition')])
        self.assertEqual(VS.tim_app('Shadow of the Tomb Raider',gia_lap(s))['id'],750920)

class TimVideo(unittest.TestCase):
    def test_tra_url_m3u8_ten_app_id(self):
        v=VS.tim_video('RESIDENT EVIL 5',gia_lap(tim([item(21690,'Resident Evil 5')]),mv('Resident Evil 5 Trailer',app=21690)))
        self.assertEqual(len(v),1); self.assertEqual((v[0]['ten'],v[0]['app_id']),('Resident Evil 5 Trailer',21690)); self.assertIn('.m3u8',v[0]['url'])
    def test_uu_tien_trailer_roi_gameplay_pegi_sau(self):
        v=VS.tim_video('Risk of Rain 2',gia_lap(tim([item(632360,'Risk of Rain 2')]),mv('CU6 - English - No Rating','1.0 Wide','Gameplay reel','PEGI Launch Trailer','Official Trailer',app=632360)))
        self.assertEqual([x['ten'] for x in v],['Official Trailer','Gameplay reel','PEGI Launch Trailer','1.0 Wide','CU6 - English - No Rating'])
    def test_ha_diem_rtx_nvidia_accolade_review_award_teaser(self):
        v=VS.tim_video('Risk of Rain 2',gia_lap(tim([item(632360,'Risk of Rain 2')]),mv('GeForce RTX Trailer','Accolades Trailer','Teaser Trailer','Review Trailer','Award Trailer','NVIDIA Gameplay','Story so far','Official Trailer',app=632360)))
        self.assertEqual([x['ten'] for x in v][:2],['Official Trailer','Story so far']); self.assertEqual({x['ten'] for x in v[2:]},{'GeForce RTX Trailer','Accolades Trailer','Teaser Trailer','Review Trailer','Award Trailer','NVIDIA Gameplay'})
    def test_pegi_chi_tru_nhe(self):
        v=VS.tim_video('Risk of Rain 2',gia_lap(tim([item(632360,'Risk of Rain 2')]),mv('PEGI EN Launch Trailer','RTX Trailer','Misc',app=632360)))
        self.assertEqual([x['ten'] for x in v],['PEGI EN Launch Trailer','Misc','RTX Trailer'])
    def test_app_khong_video_hoac_khong_co_hls_thi_rong(self):
        self.assertEqual(VS.tim_video('Risk of Rain 2',gia_lap(tim([item(632360,'Risk of Rain 2')]),{'632360':{'632360':{'success':True,'data':{'movies':[{'id':1,'name':'t'}]}}}})),[])
        self.assertEqual(VS.tim_video('Risk of Rain 2',gia_lap(tim([item(632360,'Risk of Rain 2')]),{'632360':{'632360':{'success':True,'data':[]}}})),[])
        self.assertEqual(VS.tim_video('Risk of Rain 2',gia_lap(tim([item(632360,'Risk of Rain 2')]),{'632360':{'632360':{'success':False}}})),[])
    def test_khong_co_app_thi_rong_va_khong_goi_appdetails(self):
        goi=[]
        def f(u): goi.append(u); return tim([item(1,'Totally Different')])
        self.assertEqual(VS.tim_video('inFAMOUS Second Son',f),[]); self.assertEqual(len(goi),1)

if __name__=='__main__': unittest.main()
