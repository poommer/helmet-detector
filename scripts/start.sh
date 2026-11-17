#!/bin/bash
# เปิดระบบ Heltect ด้วยคำสั่งเดียว: เปิด Cloudflare Tunnel + ตั้ง PUBLIC_BASE_URL ให้อัตโนมัติ + รันเซิร์ฟเวอร์
# วิธีใช้ (ที่โฟลเดอร์ helmet-detector):  ./scripts/start.sh
# ปิดระบบ: กด Ctrl + C (จะปิด tunnel ให้ด้วย)

cd "$(dirname "$0")/.." || exit 1

if ! command -v cloudflared >/dev/null 2>&1; then
  echo "❌ ไม่พบ cloudflared — ติดตั้งก่อน แล้วรันใหม่"
  exit 1
fi

LOG=$(mktemp -t cloudflared)
cloudflared tunnel --url http://localhost:8000 >"$LOG" 2>&1 &
TUNNEL_PID=$!
trap 'echo; echo "ปิด tunnel..."; kill $TUNNEL_PID 2>/dev/null; rm -f "$LOG"' EXIT

echo "⏳ กำลังเปิด Cloudflare Tunnel..."
URL=""
for _ in $(seq 1 30); do
  URL=$(grep -oE 'https://[a-z0-9-]+\.trycloudflare\.com' "$LOG" | head -1)
  [ -n "$URL" ] && break
  sleep 1
done

if [ -z "$URL" ]; then
  echo "❌ เปิด tunnel ไม่สำเร็จ ดู log:"
  cat "$LOG"
  exit 1
fi

# ค่าจาก environment ชนะค่าใน .env (load_dotenv ไม่ทับ) จึงไม่ต้องแก้ไฟล์ .env ทุกครั้ง
export PUBLIC_BASE_URL="$URL"

echo ""
echo "✅ Tunnel พร้อม: $URL"
echo "   ถ้าใช้ webhook ให้ตั้ง Webhook URL ใน LINE Developers เป็น:"
echo "   $URL/line/webhook"
echo ""

[ -f .venv/bin/activate ] && source .venv/bin/activate
python -m src
