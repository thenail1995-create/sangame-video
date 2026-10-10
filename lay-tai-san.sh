#!/bin/bash
# Keo tai san + fixture tu repo RIENG TU ve dung cho khuon (A2). Repo cong khai KHONG chua am thanh/giong/trailer.
#   bash lay-tai-san.sh <khuon: tin-nhanh|top5|keo-thom> <fixture> --data <thu-muc-checkout-kenh-game-du-lieu> [--nang <thu-muc-nhanh-video-tai-san>]
# <data>/video/tai-san/am-thanh      -> khuon/<khuon>/am-thanh      (tieng dong Pixabay/ElevenLabs, dung chung)
# <data>/video/fixture/<fixture>/**  -> khuon/<khuon>/**            (tru ref/ va fixture.json)
# <nang>/video/fixture/<fixture>/**  -> khuon/<khuon>/**            (trailer mp4 nang, nhanh video-tai-san)
set -euo pipefail
KHUON="${1:?thieu khuon}"; FX="${2:?thieu fixture}"; shift 2
DATA=""; NANG=""
while [ $# -gt 0 ]; do case "$1" in --data) DATA="$2"; shift 2;; --nang) NANG="$2"; shift 2;; *) echo "tham so la: $1"; exit 2;; esac; done
[ -d "$DATA/video/fixture/$FX" ] || { echo "LOI: khong thay $DATA/video/fixture/$FX"; exit 1; }
ROOT="$(cd "$(dirname "$0")" && pwd)"; D="$ROOT/khuon/$KHUON"
[ -d "$D" ] || { echo "LOI: khong co khuon $KHUON"; exit 1; }
mkdir -p "$D/am-thanh"; cp -R "$DATA/video/tai-san/am-thanh/." "$D/am-thanh/"
copy_fx(){ local src="$1"; [ -d "$src" ] || return 0; (cd "$src" && find . -type f ! -path './ref/*' ! -name fixture.json -print0) | while IFS= read -r -d '' f; do mkdir -p "$D/$(dirname "$f")"; cp -p "$src/$f" "$D/$f"; done; }
copy_fx "$DATA/video/fixture/$FX"
[ -n "$NANG" ] && copy_fx "$NANG/video/fixture/$FX"
echo "lay-tai-san: $KHUON <- fixture $FX ($(find "$D" -type f \( -path '*/am-thanh/*' -o -path '*/dau-vao/*' -o -path '*/tai-san/*' \) | wc -l | tr -d ' ') tep)"
