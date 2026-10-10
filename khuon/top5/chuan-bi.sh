#!/bin/bash
# B2: chon 5 game + loi doc cho ngay DANG (che do tu dong). Ra: top5.json, cau-hinh.json, loi-dang.json, kich-ban.json, loi.txt, tai-san/bia1..5.png, ket-qua-chon.json.
# Thoat 3 = KHONG du 5 game dat dieu kien -> bo khung (workflow ntfy). Bien: NGAY (YYYY-MM-DD, ngay DANG), GIO_DANG (12:00), DU_LIEU_REPO (thu muc checkout kenh-game-du-lieu).
set -euo pipefail
M="$(cd "$(dirname "$0")" && pwd)"; ROOT="$(cd "$M/../.." && pwd)"
if [ -n "${CHUAN_BI_PY:-}" ]; then PY=("$CHUAN_BI_PY"); else PY=(uv run -q --frozen --project "$ROOT" python); fi   # CI: job chon dung python3 he thong (chi stdlib)
cd "$M"
"${PY[@]}" chon-top5.py ${DU_LIEU_REPO:+"$DU_LIEU_REPO"} ${NGAY:+--ngay "$NGAY"}
"${PY[@]}" kich-ban.py
