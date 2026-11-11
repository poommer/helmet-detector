# use Webhok to collect LINE User ID and response test message 

import base64
import hashlib
import hmac
import json

from fastapi import APIRouter, Request, HTTPException
from fastapi.responses import JSONResponse

from src.config import LINE_CHANNEL_SECRET
from src.services.subscriber_service import (
    add_subscriber,
    remove_subscriber
)
from src.services.line_service import send_line_message


router = APIRouter()


def verify_line_signature(body: bytes, signature: str):
    digest = hmac.new(
        LINE_CHANNEL_SECRET.encode("utf-8"),
        body,
        hashlib.sha256
    ).digest()

    expected_signature = base64.b64encode(digest).decode("utf-8")

    return hmac.compare_digest(
        expected_signature,
        signature
    )


@router.post("/webhook/line")
async def line_webhook(request: Request):

    body = await request.body()

    signature = request.headers.get("x-line-signature")

    if not signature or not verify_line_signature(body, signature):
        raise HTTPException(
            status_code=401,
            detail="Invalid LINE signature"
        )

    try:
        data = json.loads(body)
    except json.JSONDecodeError:
        raise HTTPException(
            status_code=400,
            detail="Invalid JSON"
        )

    for event in data.get("events", []):

        event_type = event.get("type")

        source = event.get("source", {})
        user_id = source.get("userId")

        if not user_id:
            continue

        # User adds LINE OA as a friend
        if event_type == "follow":

            add_subscriber(user_id)

            print("New LINE subscriber:", user_id)

        # User blocks LINE OA
        elif event_type == "unfollow":

            remove_subscriber(user_id)

            print("LINE subscriber removed:", user_id)

        # User sends a message
        elif event_type == "message":

            message = event.get("message", {})

            if message.get("type") == "text":

                await send_line_message(
                    user_id,
                    "ระบบ PPE Alert พร้อมใช้งานแล้ว"
                )

    return JSONResponse({
        "status": "success"
    })

