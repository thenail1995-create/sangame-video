#!/bin/bash
# Dung Top 5 3 ban theo nen tang + kiem (A5). Dau vao (lay-tai-san.sh dat san): top5.json, cau-hinh.json, kich-ban.json, loi.txt, dau-vao/giong.mp3 (+ moc-chu.json cua Mac de so K14), tai-san/, am-thanh/.
# Lop alpha: dung -> ghep -> XOA tung ban (~4,9 GB/ban).
M="$(cd "$(dirname "$0")" && pwd)"; . "$M/../../cong-cu/chay-chung.sh"
cd "$M"
# LIVE=1 (B2): chon game + loi (chuan-bi.sh) + thu giong (cong-cu/giong.py) neu workflow/nguoi dung chua lam. LIVE khac => fixture (dau vao co san).
if [ "${LIVE:-0}" = 1 ]; then
  if [ ! -f top5.json ] || [ ! -f kich-ban.json ]; then bash "$M/chuan-bi.sh"; moc "chon 5 game + loi"; fi
  if [ ! -f dau-vao/giong.mp3 ]; then mkdir -p dau-vao; "${PY[@]}" "$ROOT/cong-cu/giong.py" giong --loi-file loi.txt --ra dau-vao/giong.mp3 --du-an san-game --dang top5; moc "giong"; fi
fi
if [ -f dau-vao/moc-chu.json ]; then cp dau-vao/moc-chu.json dau-vao/moc-chu.mac.json; fi
"${PY[@]}" can-chu.py | tail -4;            moc "can chu (Whisper)"
if [ -f dau-vao/moc-chu.mac.json ]; then "${PY[@]}" "$ROOT/cong-cu/so-moc.py" dau-vao/moc-chu.mac.json dau-vao/moc-chu.json 0.08 | tee -a "$DO"; fi
"${PY[@]}" nen-top5.py tat-ca | tail -3;    moc "nen trailer 3 ban"
for nt in "${NTS[@]}"; do
  "${PY[@]}" dung.py lop "$nt";             moc "lop chu $nt"
  "${PY[@]}" dung.py hinh "$nt"; rm -f "$M/lop-$nt.mov"; moc "ghep hinh $nt (xoa lop)"
done
"${PY[@]}" dung.py build tiktok && node do-khung.cjs tiktok; moc "khung cham"
"${PY[@]}" am-top5.py | tail -1;            moc "tieng + ghep 3 ban"
"${PY[@]}" dung.py bia tat-ca 2.2 | tail -1; moc "bia"
chay_kiem
