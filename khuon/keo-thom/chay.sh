#!/bin/bash
# Dung Keo thom v8.3 3 ban theo nen tang + kiem (A5). Dau vao (lay-tai-san.sh dat san): dau-vao/{giong.mp3,moc-chu.json,trailer/,nen-doan.json}, am-thanh/.
# Lop alpha dung -> ghep -> XOA tung ban (~4,9 GB/ban; may GitHub co ~14 GB trong).
M="$(cd "$(dirname "$0")" && pwd)"; . "$M/../../cong-cu/chay-chung.sh"
cd "$M"
"${PY[@]}" nen08.py tat-ca;                 moc "nen trailer 3 ban"
for nt in "${NTS[@]}"; do
  "${PY[@]}" dung.py lop "$nt";             moc "lop chu $nt"
  "${PY[@]}" ghep08.py "$nt"; rm -f "$M/lop-$nt.mov"; moc "ghep hinh $nt (xoa lop)"
done
"${PY[@]}" dung.py build tiktok && node do-khung.cjs tiktok; moc "khung cham"
"${PY[@]}" am08.py;                         moc "tieng + ghep 3 ban"
"${PY[@]}" dung.py bia tat-ca 3.7;          moc "bia"
chay_kiem
