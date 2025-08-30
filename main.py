
import os
from fastapi import FastAPI, Request, Header, HTTPException
from pydantic import BaseModel
import httpx
from datetime import datetime
from zoneinfo import ZoneInfo

BOT_TOKEN = os.getenv("BOT_TOKEN")
SECRET_TOKEN = os.getenv("SECRET_TOKEN", "changeme")  # یک رشته تصادفی قوی بگذارید
TELEGRAM_API = f"https://api.telegram.org/bot{BOT_TOKEN}"
TEHRAN_TZ = ZoneInfo("Asia/Tehran")

app = FastAPI(title="Tehran Time Bot")

# --- کمک‌تابع‌ها ---

def wants_time(txt: str) -> bool:
    if not txt:
        return False
    # یکنواخت‌سازی حروف عربی/فارسی و حذف نشانه پرسش
    t = (
        txt.replace("?", "").replace("؟", "").strip()
        .replace("ي", "ی").replace("ك", "ک")
    )
    triggers = [
        "ساعت چند",
        "ساعت چنده",
        "ساعت چند الان",
        "ساعت الان",
        "ساعت",
    ]
    if any(tr in t for tr in triggers):
        return True
    # فرمان برای حالت Privacy Mode روشن
    if t.startswith("/time") or t == "time":
        return True
    return False


def tehran_time_str() -> str:
    now = datetime.now(TEHRAN_TZ)
    return now.strftime("%H:%M")


async def tg_send_message(chat_id: int, text: str) -> None:
    async with httpx.AsyncClient(timeout=10) as client:
        await client.post(
            f"{TELEGRAM_API}/sendMessage",
            data={"chat_id": chat_id, "text": text, "disable_notification": True},
        )


# --- مدل ورودی وبهوک (اختیاری/ساده) ---
class Update(BaseModel):
    update_id: int | None = None
    message: dict | None = None
    edited_message: dict | None = None


@app.get("/")
async def index():
    return {"message": "Tehran time bot is running."}


@app.get("/health")
async def health():
    return {"status": "ok"}


@app.post("/webhook/{secret}")
async def webhook(
    secret: str,
    request: Request,
    x_telegram_bot_api_secret_token: str | None = Header(default=None),
):
    # تطبیق مسیر و هدر امنیتی (اختیاری ولی توصیه‌شده)
    if secret != SECRET_TOKEN:
        raise HTTPException(status_code=401, detail="Bad secret path")
    if x_telegram_bot_api_secret_token and x_telegram_bot_api_secret_token != SECRET_TOKEN:
        raise HTTPException(status_code=401, detail="Bad secret header")

    payload = await request.json()
    u = Update(**payload)
    msg = u.message or u.edited_message or None
    if not msg:
        return {"ok": True}

    chat = msg.get("chat", {})
    chat_id = chat.get("id")
    text = msg.get("text") or ""

    if chat_id and wants_time(text):
        reply = f"⏰ ساعت: {tehran_time_str()}\n\nگروه بچه‌های ایرون @iran9897"
        await tg_send_message(chat_id, reply)

    return {"ok": True}


@app.get("/set_webhook")
async def set_webhook(request: Request):
    if not BOT_TOKEN:
        raise HTTPException(status_code=500, detail="BOT_TOKEN not set")

    # ساخت آدرس بیرونی بر اساس دامنه سرویس (Render)
    base_url = str(request.base_url).rstrip("/")
    webhook_url = f"{base_url}/webhook/{SECRET_TOKEN}"

    async with httpx.AsyncClient(timeout=10) as client:
        r = await client.get(
            f"{TELEGRAM_API}/setWebhook",
            params={
                "url": webhook_url,
                "secret_token": SECRET_TOKEN,
                "drop_pending_updates": True,
            },
        )
        data = r.json()

    return {"set_webhook_to": webhook_url, "telegram_response": data}
