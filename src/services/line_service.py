# Line sending messsage system 

import httpx

from src.config import LINE_CHANNEL_ACCESS_TOKEN
from src.services.subscriber_service import get_subscribers


LINE_PUSH_URL = "https://api.line.me/v2/bot/message/push"


async def send_line_message(user_id: str, message: str):

    headers = {
        "Authorization": f"Bearer {LINE_CHANNEL_ACCESS_TOKEN}",
        "Content-Type": "application/json",
    }

    payload = {
        "to": user_id,
        "messages": [
            {
                "type": "text",
                "text": message
            }
        ]
    }

    async with httpx.AsyncClient(timeout=15) as client:
        response = await client.post(
            LINE_PUSH_URL,
            headers=headers,
            json=payload
        )

    response.raise_for_status()

    return response.json() if response.content else {}


async def send_alert_to_all(message: str):

    subscribers = get_subscribers()

    if not subscribers:
        return {
            "success": False,
            "message": "No LINE subscribers found"
        }

    results = []

    for user_id in subscribers:
        try:
            await send_line_message(user_id, message)

            results.append({
                "user_id": user_id,
                "success": True
            })

        except httpx.HTTPError as error:
            results.append({
                "user_id": user_id,
                "success": False,
                "error": str(error)
            })

    return {
        "success": all(item["success"] for item in results),
        "total": len(subscribers),
        "results": results
    }
