#!/bin/bash
# Vong TU SUA MOC CHU (ke hoach 30-dung-dung-lan-1.md, DOT 2a muc A+B) - source file nay (chay-chung.sh da source), roi goi trong chay.sh THAY CHO `can-chu.py | tail -4`:
#   can_chu_tu_sua <cach1> [cach2 ...]     (thu tu uu tien cua khuon; chi 1 cach = chi BAO, khong doi duoc)
# Can: ROOT, M (thu muc khuon), PY. Buoc 1: can-chu.py (cach mac dinh cua khuon) -> cong-cu/kiem_moc.py (moc chu dau doan vs giong + ws0).
#   - dat (0)              : xong, ghi kiem/tu-sua.json {da_sua:false}.
#   - lech (5)             : chay lai can-chu.py --cach <cach KE TIEP sau cach da dung trong danh sach> (EP: that bai => ma 6, KHONG am tham roi cach khac), kiem_moc lai.
#                            TOI DA 1 LAN DOI CACH. Dat => 0 (da_sua:true); van lech => 5 (dung); hoac khuon chi co 1 cach => chi bao, tra 0.
#   - ma khac (crash/sai dau vao) : tra NGUYEN ma do (bao toan ma thoat).
# Ham nay chay NGAY SAU can-chu va TRUOC moi buoc phu thuoc moc (nen chon / build + do khung / tieng / so-moc voi Mac): chua buoc nao chay nen KHONG can chay lai
# buoc nao khi doi cach - sau khi ham tra 0, cac buoc cua khuon (dung dung thu tu cu) dung moc cuoi cung (Sol P1 #1: moc doi thi nen/khung/neo/tieng deu lay tu moc moi).
# Ghi: kiem/tu-sua.json (manifest.tu_sua), kiem/kiem-moc-1.json (+ -2), kiem/can-chu-1.log (+ -2), dau-vao/moc-chu.lan1.json (moc cua lan 1 neu da doi cach).
# LUU Y set -e: ham nay tu kiem ma thoat tung buoc (|| rc=$?), vi trong ngu canh `ham || ...` bash bo set -e ben trong.

_tsm_hien(){ local log=$1; grep -E '^(CAN CHU|CACH CAN CHU)' "$log" || true; tail -4 "$log"; }

_tsm_ghi(){   # _tsm_ghi <cuoi.json|""> <cach_dau> <cach_cuoi> <da_sua 0|1> <ghi chu>
  "${PY[@]}" "$ROOT/cong-cu/kiem_moc.py" ghi-tu-sua "$M/kiem/tu-sua.json" --lan-dau "$M/kiem/kiem-moc-1.json" --cuoi "$1" --cach-dau "$2" --cach-cuoi "$3" --da-sua "$4" --ghi-chu "$5"
}

can_chu_tu_sua(){
  [ "$#" -ge 1 ] || { echo "can_chu_tu_sua: can it nhat 1 ten cach"; return 2; }
  local cachs=("$@") KD="$M/kiem" DV="$M/dau-vao" rc=0 cach1="" next="" found=0 c
  mkdir -p "$KD" "$DV"
  rm -f "$DV/ws0.json" "$KD/kiem-moc-1.json" "$KD/kiem-moc-2.json" "$KD/tu-sua.json"
  "${PY[@]}" "$M/can-chu.py" > "$KD/can-chu-1.log" 2>&1 || rc=$?
  if [ "$rc" != 0 ]; then cat "$KD/can-chu-1.log"; echo "CAN CHU: that bai (ma $rc)"; return "$rc"; fi
  _tsm_hien "$KD/can-chu-1.log"
  cach1="$(sed -n 's/^CACH CAN CHU: //p' "$KD/can-chu-1.log" | tail -1)"
  rc=0; "${PY[@]}" "$ROOT/cong-cu/kiem_moc.py" "$DV/moc-chu.json" "$DV/giong.mp3" --ws0 "$DV/ws0.json" --ra "$KD/kiem-moc-1.json" || rc=$?
  if [ "$rc" = 0 ]; then _tsm_ghi "" "$cach1" "$cach1" 0 "dat ngay lan dau"; return 0; fi
  [ "$rc" = 5 ] || { echo "KIEM MOC: loi ma $rc (khong phai dat/lech) - dung"; return "$rc"; }
  for c in "${cachs[@]}"; do
    if [ "$found" = 1 ]; then next="$c"; break; fi
    if [ "$c" = "$cach1" ]; then found=1; fi
  done
  if [ -z "$next" ]; then
    _tsm_ghi "" "$cach1" "$cach1" 0 "lech, khong con cach khac sau '$cach1' trong danh sach ($*)"
    if [ "${#cachs[@]}" = 1 ]; then echo "TU SUA: moc lech nhung khuon chi co 1 cach -> CHI BAO (de kiem som/kiem cuoi quyet dinh)"; return 0; fi
    echo "TU SUA: moc lech, khong con cach khac sau '$cach1' -> DUNG"; return 5
  fi
  echo "TU SUA: moc lech (cach '$cach1') -> chay lai can-chu EP cach '$next'"
  cp "$DV/moc-chu.json" "$DV/moc-chu.lan1.json"
  rc=0; "${PY[@]}" "$M/can-chu.py" --cach "$next" > "$KD/can-chu-2.log" 2>&1 || rc=$?
  if [ "$rc" != 0 ]; then
    cat "$KD/can-chu-2.log"; _tsm_ghi "" "$cach1" "$cach1" 0 "ep cach '$next' that bai (ma $rc), khong tu roi sang cach khac"
    echo "TU SUA: EP cach '$next' THAT BAI (ma $rc) -> DUNG"; return "$rc"
  fi
  _tsm_hien "$KD/can-chu-2.log"
  rc=0; "${PY[@]}" "$ROOT/cong-cu/kiem_moc.py" "$DV/moc-chu.json" "$DV/giong.mp3" --ws0 "$DV/ws0.json" --ra "$KD/kiem-moc-2.json" || rc=$?
  if [ "$rc" = 0 ]; then _tsm_ghi "$KD/kiem-moc-2.json" "$cach1" "$next" 1 "da doi cach $cach1 -> $next, dat"; echo "TU SUA: DA SUA ($cach1 -> $next), moc dat"; return 0; fi
  [ "$rc" = 5 ] || { echo "KIEM MOC lan 2: loi ma $rc - dung"; return "$rc"; }
  _tsm_ghi "$KD/kiem-moc-2.json" "$cach1" "$next" 1 "da doi cach $cach1 -> $next, VAN LECH"
  echo "TU SUA: doi cach '$cach1' -> '$next' van lech -> DUNG (toi da 1 lan doi cach)"; return 5
}

# so_moc_voi_mac: K14 (moc may moi vs moc Mac) CHI co y nghia khi CUNG thuat toan. Neu tu sua da DOI CACH (kiem/tu-sua.json da_sua=true) thi bo qua (in canh bao),
# khong doi cach thi so-moc nhu cu (tran 80 ms, that bai => ma thoat khac 0). Goi sau can_chu_tu_sua; khong co moc-chu.mac.json thi khong lam gi.
so_moc_voi_mac(){
  [ -f "$M/dau-vao/moc-chu.mac.json" ] || return 0
  if [ -f "$M/kiem/tu-sua.json" ] && grep -q '"da_sua": true' "$M/kiem/tu-sua.json"; then
    echo "so-moc bo qua: cach can doi tu $(sed -n 's/^ *"cach_dau": "\(.*\)",$/\1/p' "$M/kiem/tu-sua.json") sang $(sed -n 's/^ *"cach_cuoi": "\(.*\)",$/\1/p' "$M/kiem/tu-sua.json") (so-moc chi so cung thuat toan)" | tee -a "$DO"
    return 0
  fi
  "${PY[@]}" "$ROOT/cong-cu/so-moc.py" "$M/dau-vao/moc-chu.mac.json" "$M/dau-vao/moc-chu.json" 0.08 | tee -a "$DO"
}
