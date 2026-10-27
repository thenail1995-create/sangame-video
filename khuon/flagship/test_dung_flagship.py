"""Test phan DUNG HINH + KIEM cua khuon flagship (chay: uv run --frozen python -m pytest khuon/flagship -q)."""
import json,pathlib,re,sys,subprocess
B=pathlib.Path(__file__).resolve().parent
sys.path.insert(0,str(B))
import flag_chung as FC

def _game(**k):
    g=dict(ten='X Game',ten_the='X Game',ten_goc='X Game',gia_hien='$9,99',goc_hien='$49,99',gia_vnd_hien='280.000đ',han_hien='5/11',giam=80,gia_vnd=280000,
           the_hien=['$10'],han_con_ngay=8,moc=dict(loai='khong',chu=''))
    g.update(k); return g

def test_nen_tang_trailer_1000_ca_3_ban():
    nt=json.load(open(B/'nen-tang.json'))
    assert set(nt)=={'tiktok','reels','shorts'}
    assert all(v['trailer']==1000 and v['duoi']==1480 for v in nt.values())

def test_full_html_khong_blur_khong_chu_thich_nuot_lenh():
    s=(B/'full.html').read_text(encoding='utf-8')
    assert 'blur(' not in s and 'backdrop-filter' not in s      # SAN #1
    assert not re.search(r'(?<![:\w])//.*\b(tf|op|show)\(',s)     # H25: // nuot lenh JS
    assert '__GAME__' in s and '__MOC__' in s and '__CANH__' in s and '__CFG__' in s and '__NT__' in s

def test_tap_so_cho_phep():
    ok=FC.tap_so(_game(moc=dict(loai='tin',chu='UPDATE 2.5 MIỄN PHÍ')))
    assert {'280','280.000','9,99','49,99','80','10','5','11','8','2.5'}<=ok
    assert '7' not in ok and '47,06' not in ok                  # SAN #47: so la khong duoc phep

def test_vnd_k():
    assert FC.vnd_k(_game())=='280K'
    assert FC.vnd_k(_game(gia_vnd=280500,gia_vnd_hien='280.500đ'))=='280.500đ'

def test_dung_build_chen_het_du_lieu(tmp_path):
    # dung.py build chen du lieu vao full.html, khong con ma __X__ nao sot lai
    if not (B/'canh.json').exists() or not (B/'dau-vao/moc-chu.json').exists(): return
    subprocess.run([sys.executable,str(B/'dung.py'),'build','tiktok'],check=True)
    s=(B/'full-tiktok.build.html').read_text(encoding='utf-8')
    assert not re.search(r'__[A-Z]+__(?!\w)',s.split('<script>')[1].split('window.__ready')[0])
