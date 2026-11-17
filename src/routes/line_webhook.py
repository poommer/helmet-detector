# use Webhok to collect LINE User ID and response test message 

import asyncio
import base64
import hashlib
import hmac
import json

from fastapi import APIRouter, Header, Request, HTTPException

from ..config import LINE_CHANNEL_SECRET
from ..services.line_service import add_recipient, remove_recipient, reply_message
router = APIRouter(prefix="/line", tags=["LINE"])


def verify_signature(body: bytes, signature: str) -> bool:
    # ตรวจลายเซ็นว่าคำขอมาจาก LINE จริง (HMAC-SHA256 ด้วย channel secret)
    digest = hmac.new(LINE_CHANNEL_SECRET.encode(), body, hashlib.sha256).digest()
    return hmac.compare_digest(base64.b64encode(digest).decode(), signature)


@router.post("/webhook")
async def line_webhook(request: Request, x_line_signature: str = Header(...)):
    body = await request.body()

    # ลายเซ็นไม่ถูกต้อง = ไม่ใช่ LINE ส่งมา ปฏิเสธ
    if not LINE_CHANNEL_SECRET or not verify_signature(body, x_line_signature):
        raise HTTPException(status_code=401, detail="Invalid signature")

    payload = json.loads(body)

    for event in payload.get("events", []):
        source = event.get("source", {})
        # ถ้ามาจากกลุ่มใช้ groupId, ถ้าแชทเดี่ยวใช้ userId
        target_id = source.get("groupId") or source.get("roomId") or source.get("userId")
        event_type = event.get("type")
        reply_token = event.get("replyToken")

        if event_type in ("follow", "join"):
            # มีคนแอดบอท / เชิญบอทเข้ากลุ่ม -> ลงทะเบียนรับแจ้งเตือน
            add_recipient(target_id)
            await asyncio.to_thread(
                reply_message, reply_token,
                "✅ ลงทะเบียนรับแจ้งเตือน Heltect แล้ว",
            )

        elif event_type in ("unfollow", "leave"):
            # มีคนบล็อกบอท / บอทออกจากกลุ่ม -> เลิกส่ง
            remove_recipient(target_id)

        elif event_type == "message":
            # พิมพ์ "id" เพื่อดู ID ของตัวเอง/กลุ่ม (เอาไปใส่ LINE_TO ได้)
            text = event.get("message", {}).get("text", "").strip().lower()
            if text in ("id", "/id"):
                await asyncio.to_thread(reply_message, reply_token, f"ID: {target_id}")

    # ต้องตอบ 200 เสมอ ไม่งั้น LINE จะถือว่า webhook พัง
    return {"status": "ok"}