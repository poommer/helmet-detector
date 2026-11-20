#!/bin/bash
# เปิดระบบ Heltect สำหรับ demo ด้วย ngrok (domain ถาวร) ในคำสั่งเดียว
# วิธีใช้ (ที่โฟลเดอร์ helmet-detector):  bash scripts/start-demo.sh
# ปิดระบบ: กด Ctrl + C (จะปิด ngrok ให้ด้วย)
#
# ต้องมีใน .env:
#   NGROK_AUTHTOKEN=โทเคนของบัญชีที่เป็นเจ้าของ domain
#   NGROK_DOMAIN=stapling-mandate-absolute.ngrok-free.dev

cd "$(dirname "$0")/.." || exit 1

if ! command -v ngrok >/dev/null 2>&1; then
  echo "❌ ไม่พบ ngrok — ติดตั้งก่อน:  brew install ngrok"
  exit 1
fi

# อ่านค่าจาก .env
read_env() { grep -E "^$1=" .env 2>/dev/null | tail -1 | cut -d= -f2- | tr -d '"' | tr -d "'" | tr -d '[:space:]'; }
NGROK_AUTHTOKEN=$(read_env NGROK_AUTHTOKEN)
NGROK_DOMAIN=$(read_env NGROK_DOMAIN)
NGROK_DOMAIN=${NGROK_DOMAIN:-stapling-mandate-absolute.ngrok-free.dev}

if [ -z "$NGROK_AUTHTOKEN" ]; then
  echo "❌ ยังไม่มี NGROK_AUTHTOKEN ใน .env"
  exit 1
fi

# ให้ LINE ดึงรูปหลักฐานจาก domain นี้ (ค่าจาก environment ชนะค่าใน .env)
export PUBLIC_BASE_URL="https://$NGROK_DOMAIN"

LOG=$(mktemp -t ngrok)
ngrok http --url="$NGROK_DOMAIN" 8000 --authtoken "$NGROK_AUTHTOKEN" --log stdout >"$LOG" 2>&1 &
NGROK_PID=$!
trap 'echo; echo "ปิด ngrok..."; kill $NGROK_PID 2>/dev/null; rm -f "$LOG"' EXIT

echo "⏳ กำลังเปิด ngrok..."
for _ in $(seq 1 15); do
  grep -q "started tunnel\|url=https://" "$LOG" && break
  if ! kill -0 $NGROK_PID 2>/dev/null; then
    echo "❌ เปิด ngrok ไม่สำเร็จ:"
    cat "$LOG"
    echo "   (ถ้าขึ้น ERR_NGROK_334 = เพื่อนเปิด domain นี้ค้างไว้อยู่ ให้เพื่อนปิดก่อน)"
    exit 1
  fi
  sleep 1
done

echo ""
echo "✅ ngrok พร้อม: $PUBLIC_BASE_URL"
echo "   หน้าเว็บ:      $PUBLIC_BASE_URL"
echo "   LINE Webhook: $PUBLIC_BASE_URL/line/webhook"
echo ""

# หา Python ตัวที่ติดตั้งแพ็กเกจของโปรเจกต์ไว้แล้ว (uvicorn + ultralytics)
PY=""
for candidate in \
  ".venv/bin/python" \
  "/Library/Frameworks/Python.framework/Versions/3.12/bin/python3" \
  "/usr/local/bin/python3" \
  "$(command -v python3)"; do
  if [ -x "$candidate" ] && "$candidate" -c "import uvicorn, ultralytics" >/dev/null 2>&1; then
    PY="$candidate"
    break
  fi
done

if [ -z "$PY" ]; then
  echo "❌ ไม่พบ Python ที่ติดตั้งแพ็กเกจของโปรเจกต์ไว้"
  echo "   รัน: python3 -m pip install -r requirements.txt"
  exit 1
fi

echo "🐍 ใช้ Python: $PY"
"$PY" -m src
