# Line sending messsage system 
# บริการส่งข้อความ LINE: จัดการรายชื่อผู้รับ + ส่ง push/reply ไปที่ LINE API
import asyncio
import json
import threading
import uuid

import requests

from ..config import LINE_CHANNEL_ACCESS_TOKEN, LINE_TO, RECIPIENTS_FILE

PUSH_URL = "https://api.line.me/v2/bot/message/push"
REPLY_URL = "https://api.line.me/v2/bot/message/reply"
TIMEOUT = 5                       # วินาที กันระบบค้างถ้า LINE ตอบช้า

_lock = threading.Lock()  # กันสองคำขอเขียนไฟล์รายชื่อพร้อมกัน


def _headers():
    # header มาตรฐานที่ LINE API ต้องการ
    return {
        "Authorization": f"Bearer {LINE_CHANNEL_ACCESS_TOKEN}",
        "Content-Type": "application/json",
    }


# ---------- ระบบสำหรับจัดการรายชื่อผู้รับ ----------

def _read_saved_ids():
    # อ่าน ID ที่ลงทะเบียนผ่าน webhook จากไฟล์ 
    try:
        return json.loads(RECIPIENTS_FILE.read_text(encoding="utf-8"))
    except (FileNotFoundError, json.JSONDecodeError):
        return []


def _write_saved_ids(ids):
    # บันทึกรายชื่อลงไฟล์
    RECIPIENTS_FILE.parent.mkdir(parents=True, exist_ok=True)
    RECIPIENTS_FILE.write_text(json.dumps(ids, indent=2), encoding="utf-8")


def load_recipients():
    # รวมผู้รับจาก .env (LINE_TO) + จากไฟล์ โดยตัดตัวซ้ำออก
    return list(dict.fromkeys(LINE_TO + _read_saved_ids()))


def add_recipient(target_id):
    # เพิ่มผู้รับใหม่ (เรียกตอนมีคนแอดบอท หรือ เชิญบอทเข้ากลุ่ม)
    if not target_id:
        return
    with _lock:
        ids = _read_saved_ids()
        if target_id not in ids:
            ids.append(target_id)
            _write_saved_ids(ids)


def remove_recipient(target_id):
    # ลบผู้รับ (เรียกตอนมีคนบล็อกบอท หรือเตะบอทออกจากกลุ่ม)
    with _lock:
        ids = [i for i in _read_saved_ids() if i != target_id]
        _write_saved_ids(ids)


# ---------- ระบบการส่งข้อความ ----------

def push_message(to, text, retry_key=None):
    # ส่งข้อความหา 1 ผู้รับ แล้วคืนผลเป็น dict (messages = list ของข้อความ LINE)
    headers = _headers()
    if retry_key:
        headers["X-Line-Retry-Key"] = retry_key       # กันส่งซ้ำเวลา retry
    try:
        res = requests.post(
            PUSH_URL,
            headers=headers,
            json={"to": to, "messages": [{"type": "text", "text": text}]},
            timeout=TIMEOUT,
        )
    except requests.RequestException as err:
        return {"to": to, "ok": False, "status": None, "error": str(err)}

    ok = res.status_code in (200, 409)                # 409 = เคยส่งสำเร็จแล้ว
    return {"to": to, "ok": ok, "status": res.status_code,
            "error": None if ok else res.text}


def reply_message(reply_token, text):
    # ตอบกลับข้อความใน webhook (ฟรี ไม่นับโควตา push)
    try:
        requests.post(
            REPLY_URL,
            headers=_headers(),
            json={"replyToken": reply_token,
                  "messages": [{"type": "text", "text": text}]},
            timeout=TIMEOUT,
        )
    except requests.RequestException as err:
        print(f"[line_service] reply ไม่สำเร็จ: {err}")


def send_alert_to_all_sync(text, retry_key=None, messages=None):
    # ส่งข้อความหาผู้รับทุกคน (แบบ sync ใช้ในโค้ดที่ไม่ใช่ async)
    # if ไม่ส่ง messages มา -> จะส่ง normal text 

    if messages is None:
        messages = [{"type": "text", "text": text}]

    recipients = load_recipients()
    if not recipients:
        return {"success": False, "sent": 0, "failed": 0, "results": [],
                "error": "ยังไม่มีผู้รับ: ใส่ LINE_TO ใน .env หรือแอดบอทเป็นเพื่อน"}

    results = []
    for to in recipients:
        # retry key ต้องไม่ซ้ำกันในแต่ละผู้รับ เลยสร้างจาก key หลัก + ID ผู้รับ
        key = str(uuid.uuid5(uuid.UUID(retry_key), to)) if retry_key else None
        results.append(push_message(to, messages, key))

    sent = sum(r["ok"] for r in results)
    for r in results:
        if not r["ok"]:
            print(f"[line_service] ส่งไม่สำเร็จ {r['to']}: {r['status']} {r['error']}")

    return {"success": sent > 0, "sent": sent,
            "failed": len(results) - sent, "results": results}


async def send_alert_to_all(text, retry_key=None):
    # เวอร์ชัน async สำหรับใช้ใน route ของ FastAPI (ไม่บล็อกเซิร์ฟเวอร์)
    return await asyncio.to_thread(send_alert_to_all_sync, text, retry_key)