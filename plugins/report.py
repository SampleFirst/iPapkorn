import asyncio
from datetime import datetime, timedelta
import os
from pytz import timezone
from pyrogram import Client

from database.users_chats_db import db
from utils import temp
from info import SESSION, LOG_CHANNEL

TIMEZONE = os.environ.get("TIMEZONE", "Asia/Kolkata")


async def send_day_report(client: Client):
    users_count = await db.get_all_users_count()
    chat_count = await db.get_all_chats_count()

    curr = datetime.now(timezone(TIMEZONE))
    log_text = f"#𝐃𝐚𝐲𝐑𝐞𝐩𝐨𝐫𝐭\n<b>᚛› 𝐃𝐀𝐘 - {curr.strftime('%d %B, %Y')}</b>\n<b>᚛› 𝐓𝐈𝐌𝐄 - {curr.strftime('%I:%M:%S %p')}</b>\n<b>᚛› 𝐓𝐎𝐃𝐀𝐘 𝐔𝐒𝐄𝐑𝐒 - {users_count}</b>\n<b>᚛› 𝐓𝐎𝐃𝐀𝐘 𝐂𝐇𝐀𝐓𝐒 - {chat_count}</b>\nBy @{temp.B_LINK}"
    
    await client.send_message(LOG_CHANNEL, log_text)
    await db.reset_daily_data()


async def scheduler():
    while True:
        now = datetime.now(timezone(TIMEZONE))
        next_day = now.replace(hour=0, minute=0, second=0) + timedelta(days=1)
        delay = (next_day - now).total_seconds()
        await asyncio.sleep(delay)
        async with Client(session_name=SESSION) as client:
            await send_day_report(client)


if __name__ == '__main__':
    asyncio.run(scheduler())
