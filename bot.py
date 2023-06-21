import os
import logging
import logging.config
import asyncio
from pyrogram import Client, __version__
from pyrogram.raw.all import layer
from database.ia_filterdb import Media
from database.users_chats_db import db
from info import SESSION, API_ID, API_HASH, BOT_TOKEN, LOG_CHANNEL, PORT, WEBHOOK
from utils import temp
from typing import Union, Optional, AsyncGenerator
from pyrogram import types
from datetime import datetime
from pytz import timezone
from pyrogram.errors import BadRequest, Unauthorized

if WEBHOOK:
    from plugins import web_server 
    from aiohttp import web

# Get logging configurations
logging.config.fileConfig("logging.conf")
logging.getLogger().setLevel(logging.INFO)
logging.getLogger("cinemagoer").setLevel(logging.ERROR)

LOGGER = logging.getLogger(__name__)
TIMEZONE = os.environ.get("TIMEZONE", "Asia/Kolkata")


class Bot(Client):
    def __init__(self):
        super().__init__(
            session_name=SESSION,
            api_id=API_ID,
            api_hash=API_HASH,
            bot_token=BOT_TOKEN,
            workers=300,
            plugins={"root": "plugins"},
            sleep_threshold=10,
        )

    async def start(self):
        b_users, b_chats = await db.get_banned()
        temp.BANNED_USERS = b_users
        temp.BANNED_CHATS = b_chats        
        await super().start()
        await Media.ensure_indexes()
        me = await self.get_me()
        temp.ME = me.id
        temp.U_NAME = me.username
        temp.B_NAME = me.first_name
        temp.B_LINK = me.mention
        self.username = '@' + me.username
        curr = datetime.now(timezone(TIMEZONE))
        date = curr.strftime('%d %B, %Y')
        time = curr.strftime('%I:%M:%S %p')
        if WEBHOOK:
            app = web.Application()
            app.add_routes([web.post("/", web_server)])
            runner = web.AppRunner(app)
            await runner.setup()
            bind_address = "0.0.0.0"
            site = web.TCPSite(runner, bind_address, PORT)
            await site.start()
        logging.info(f"{me.first_name} with Pyrogram v{__version__} (Layer {layer}) started on {me.username}.")
        if LOG_CHANNEL:
            try:
                await self.send_message(LOG_CHANNEL, f"<b>{me.mention} is restarted!</b>\n\n📅 Date: <code>{date}</code>\n⏰ Time: <code>{time}</code>\n🌐 Timezone: <code>{TIMEZONE}</code>\n\n🉐 Version: <code>v{__version__} (Layer {layer})</code>")
            except Unauthorized:
                LOGGER.warning("Bot isn't able to send message to LOG_CHANNEL")
            except BadRequest as e:
                LOGGER.error(e)

    async def stop(self, *args):
        await super().stop()
        me = await self.get_me()
        logging.info(f"{me.first_name} is restarting...")

    async def iter_messages(self, chat_id: Union[int, str], limit: int, offset: int = 0) -> Optional[AsyncGenerator["types.Message", None]]:
        current = offset
        while True:
            new_diff = min(200, limit - current)
            if new_diff <= 0:
                return
            messages = await self.get_messages(chat_id, list(range(current, current+new_diff+1)))
            for message in messages:
                yield message
                current += 1



async def send_day_report(client):
    if await db.get_all_users_count() > 0:
        users_count = await db.get_all_users_count()
        chat_count = await db.get_all_chats_count()

        curr = datetime.now(timezone(TIMEZONE))
        log_text = f"#𝐃𝐚𝐲𝐑𝐞𝐩𝐨𝐫𝐭\n<b>᚛› 𝐃𝐀𝐘 - {curr.strftime('%d %B, %Y')}</b>\n<b>᚛› 𝐓𝐈𝐌𝐄 - {curr.strftime('%I:%M:%S %p')}</b>\n<b>᚛› 𝐓𝐎𝐃𝐀𝐘 𝐔𝐒𝐄𝐑𝐒 - {users_count}</b>\n<b>᚛› 𝐓𝐎𝐃𝐀𝐘 𝐂𝐇𝐀𝐓𝐒 - {chat_count}</b>\nBy @{temp.B_LINK}"
        await client.send_message(LOG_CHANNEL, log_text)
        await db.reset_daily_data()


async def scheduler():
    while True:
        now = datetime.now()
        next_day = now.replace(hour=0, minute=0, second=0) + timedelta(days=1)
        delay = (next_day - now).total_seconds()
        await asyncio.sleep(delay)
        await send_day_report(app)


if __name__ == '__main__':
    asyncio.get_event_loop().create_task(scheduler())
    app.run()
    
