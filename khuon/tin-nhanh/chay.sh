#!/bin/bash
# Dung Tin nhanh 3 ban theo nen tang + kiem (A5). Dau vao (lay-tai-san.sh dat san): tin.json, kich-ban.json, dau-vao/giong.mp3 (+ moc-chu.json cua Mac de so K14), tai-san/, am-thanh/.
# Lop alpha: dung -> ghep -> XOA tung ban (~4,9 GB/ban).
M="$(cd "$(dirname "$0")" && pwd)"; . "$M/../../cong-cu/chay-chung.sh"
cd "$M"
if [ -f dau-vao/moc-chu.json ]; then cp dau-vao/moc-chu.json dau-vao/moc-chu.mac.json; fi
"${PY[@]}" can-chu.py | tail -4;            moc "can chu (Whisper)"
if [ -f dau-vao/moc-chu.mac.json ]; then "${PY[@]}" "$ROOT/cong-cu/so-moc.py" dau-vao/moc-chu.mac.json dau-vao/moc-chu.json 0.08 | tee -a "$DO"; fi
"${PY[@]}" nen-tin.py tat-ca | tail -4;     moc "nen trailer 3 ban"
for nt in "${NTS[@]}"; do
  "${PY[@]}" dung.py lop "$nt";             moc "lop chu $nt"
  "${PY[@]}" dung.py hinh "$nt"; rm -f "$M/lop-$nt.mov"; moc "ghep hinh $nt (xoa lop)"
done
"${PY[@]}" dung.py build tiktok && node do-khung.cjs tiktok; moc "khung cham"
"${PY[@]}" am-tin.py | tail -1;             moc "tieng + ghep 3 ban"
"${PY[@]}" dung.py bia tat-ca 1.6 | tail -1; moc "bia"
chay_kiem
