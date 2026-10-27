#!/bin/bash
# Chon 1 game Flagship + loi doc cho ngay DANG. Ra: flagship.json, cau-hinh.json, loi-dang.json, kich-ban.json, loi.txt, tai-san/bia1.png, ket-qua-chon.json.
# Thoat 3 = KHONG co game dat / du lieu cu -> bo khung (workflow ntfy). Bien: NGAY (YYYY-MM-DD, ngay DANG), GIO_DANG (15:30), KEO_FILE | KEO_DIR (keo/<NGAY>.json), DU_LIEU_REPO.
set -euo pipefail
M="$(cd "$(dirname "$0")" && pwd)"; ROOT="$(cd "$M/../.." && pwd)"
if [ -n "${CHUAN_BI_PY:-}" ]; then PY=("$CHUAN_BI_PY"); else PY=(uv run -q --frozen --project "$ROOT" python); fi
cd "$M"
"${PY[@]}" chon-flagship.py ${DU_LIEU_REPO:+"$DU_LIEU_REPO"} ${NGAY:+--ngay "$NGAY"}
"${PY[@]}" kich-ban.py
