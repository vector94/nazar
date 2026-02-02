import httpx
from shared.config import SLACK_WEBHOOK_URL


async def send_slack_alert(severity: str, message: str):
    if not SLACK_WEBHOOK_URL:
        return

    color = "#ff0000" if severity == "critical" else "#ffcc00"
    payload = {
        "attachments": [
            {
                "color": color,
                "title": f"Alert: {severity.upper()}",
                "text": message,
            }
        ]
    }

    async with httpx.AsyncClient() as client:
        try:
            await client.post(SLACK_WEBHOOK_URL, json=payload)
        except Exception as e:
            print(f"Failed to send Slack notification: {e}")