#!/usr/bin/env bash
# Kiem tep chung-ra.enc lay tu cache: dung sha256 thi chuyen vao <dich>/chung-ra.enc, sai/thieu thi xoa.
# Dung: nhan-chung-ra.sh <tep> <sha_mong_doi> <thu_muc_dich>
# stdout: dong `ok=1|0` (+ `nguon=cache` khi ok=1) de ghi vao $GITHUB_OUTPUT. Ly do in ra stderr. LUON thoat 0 (khi du doi so).
set -euo pipefail
[ "$#" -eq 3 ] || { echo "dung: $0 <tep> <sha_mong_doi> <thu_muc_dich>" >&2; exit 2; }
tep="$1"; mong="$2"; dich="$3"

that_bai() {
  echo "cache chung-ra khong dung duoc: $1 -> dung artifact" >&2
  rm -f -- "$tep"
  echo "ok=0"
  exit 0
}

[ -f "$tep" ] || { echo "cache chung-ra khong dung duoc: khong co tep -> dung artifact" >&2; echo "ok=0"; exit 0; }
[[ "$mong" =~ ^[0-9a-f]{64}$ ]] || that_bai "sha mong doi rong/sai dinh dang"
that="$(sha256sum -- "$tep" | cut -d' ' -f1)"
[ "$that" = "$mong" ] || that_bai "sha khong khop (that=$that mong=$mong)"
mkdir -p -- "$dich"
mv -- "$tep" "$dich/chung-ra.enc"
echo "nguon chung-ra: cache (sha khop $that)" >&2
echo "nguon=cache"
echo "ok=1"
