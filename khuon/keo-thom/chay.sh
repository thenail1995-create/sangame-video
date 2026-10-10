#!/bin/bash
# Dung Keo thom v9 3 ban theo nen tang + kiem. DAU VAO phai co san (xem NHAT-KY GD D):
#   keo.json (chon-keo.py) · kich-ban.json + loi.txt (kich-ban.py) · dau-vao/giong.mp3 (cong-cu/giong.py hoac el.py) · am-thanh/ (lay-tai-san.sh)
#   · trailer: dau-vao/trailer/*.mp4 (neu khong co, nen08.py tai tu keo.json)
# Thu tu v9: can chu (Whisper) -> trang that + do khung/neo.json (moc theo khoa doan) -> nen trailer TU CHON -> (lop -> ghep -> xoa) x 3 -> tieng -> bia -> kiem.
# HOI_QUY=1: dung moc-chu.json co san (mau Spider-Man 2 v8.3, da gan khoa doan bang hoi-quy/gan-doan.py) — bo buoc can chu.
# Lop alpha dung -> ghep -> XOA tung ban (~4,9 GB/ban; may GitHub co ~14 GB trong).
M="$(cd "$(dirname "$0")" && pwd)"; . "$M/../../cong-cu/chay-chung.sh"
cd "$M"
# LIVE=1 (workflow tu dong, cung quy uoc voi Top 5): chon keo + loi (chuan-bi.sh) va thu giong (cong-cu/giong.py) neu chua co. LIVE khac => dau vao co san (fixture/thu tay).
if [ "${LIVE:-0}" = 1 ]; then
  if [ ! -f keo.json ] || [ ! -f kich-ban.json ]; then bash "$M/chuan-bi.sh"; moc "chon keo + loi"; fi
  if [ ! -f dau-vao/giong.mp3 ]; then mkdir -p dau-vao; "${PY[@]}" "$ROOT/cong-cu/giong.py" giong --loi-file loi.txt --ra dau-vao/giong.mp3 --du-an san-game --dang keo-thom; moc "giong"; fi
fi
for f in keo.json kich-ban.json dau-vao/giong.mp3; do [ -f "$f" ] || { echo "THIEU $f"; exit 2; }; done
if [ -z "${HOI_QUY:-}" ]; then
  "${PY[@]}" can-chu.py | tail -4;          moc "can chu (Whisper)"
fi
[ -f dau-vao/moc-chu.json ] || { echo "THIEU dau-vao/moc-chu.json"; exit 2; }
"${PY[@]}" dung.py build tiktok && node do-khung.cjs tiktok; moc "khung cham + neo.json"
"${PY[@]}" nen08.py tat-ca | tail -3;       moc "nen trailer 3 ban"
for nt in "${NTS[@]}"; do
  "${PY[@]}" dung.py lop "$nt";             moc "lop chu $nt"
  "${PY[@]}" ghep08.py "$nt"; rm -f "$M/lop-$nt.mov"; moc "ghep hinh $nt (xoa lop)"
done
"${PY[@]}" am08.py | tail -1;               moc "tieng + ghep 3 ban"
"${PY[@]}" dung.py bia tat-ca | tail -1;    moc "bia"
chay_kiem
