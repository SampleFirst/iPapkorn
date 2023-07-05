from pyrogram import Client, filters
from plugins.helper.admin_check import admin_check
from plugins.helper.extract import extract_time, extract_user
import re

@Client.on_message(filters.command("ban"))
async def ban_user(_, message):
    is_admin = await admin_check(message)
    if not is_admin:
        return
    user_id, user_first_name = extract_user(message)
    try:
        await message.chat.ban_member(user_id=user_id)
    except Exception as error:
        await message.reply_text(str(error))
    else:
        if str(user_id).lower().startswith("@"):
            await message.reply_text(f"Someone else is dusting off..! \n{user_first_name} \nIs forbidden.")
        else:
            await message.reply_text(f"Someone else is dusting off..! \n<a href='tg://user?id={user_id}'>{user_first_name}</a> Is forbidden")


@Client.on_message(filters.command("tban"))
async def temp_ban_user(_, message):
    is_admin = await admin_check(message)
    if not is_admin:
        return
    if not len(message.command) > 1:
        return
    user_id, user_first_name = extract_user(message)
    until_date_val = extract_time(message.command[1])
    if until_date_val is None:
        return await message.reply_text(
            text=f"Invalid time type specified. \nExpected m, h, or d, Got it: {message.command[1][-1]}")
    try:
        await message.chat.ban_member(user_id=user_id, until_date=until_date_val)
    except Exception as error:
        await message.reply_text(str(error))
    else:
        if str(user_id).lower().startswith("@"):
            await message.reply_text(f"Someone else is dusting off..!\n{user_first_name}\nbanned for {message.command[1]}!")
        else:
            await message.reply_text(f"Someone else is dusting off..!\n<a href='tg://user?id={user_id}'>Lavane</a>\n banned for {message.command[1]}!")


@Client.on_message(filters.group & ~filters.command(["ban", "tban"]))
async def auto_temp_ban_links(client, message):
    is_admin = await admin_check(message)
    if not is_admin:
        return
    user_id = message.from_user.id
    user_first_name = message.from_user.first_name
    if re.search(r"http[s]?://", message.text):
        until_date_val = extract_time("1d")  # Set ban duration to 1 day
        try:
            await message.chat.ban_member(user_id=user_id, until_date=until_date_val)
        except Exception as error:
            await message.reply_text(str(error))
        else:
            await message.reply_text(f"Auto-temp-banned <a href='tg://user?id={user_id}'>{user_first_name}</a> for sending links.")


@Client.on_message(filters.group & ~filters.command(["ban", "tban"]))
async def auto_ban_non_english_messages(client, message):
    is_admin = await admin_check(message)
    if not is_admin:
        return
    user_id = message.from_user.id
    user_first_name = message.from_user.first_name
    if not re.search(r"[\u0900-\u097F\u0980-\u09FF]+", message.text):
        try:
            await message.chat.ban_member(user_id=user_id)
        except Exception as error:
            await message.reply_text(str(error))
        else:
            await message.reply_text(f"Auto-banned <a href='tg://user?id={user_id}'>{user_first_name}</a> for sending non-English messages.")


@Client.on_message(filters.group & ~filters.command(["ban", "tban"]))
async def auto_ban_emojis(client, message):
    is_admin = await admin_check(message)
    if not is_admin:
        return
    user_id = message.from_user.id
    user_first_name = message.from_user.first_name
    if re.search(r"\p{Emoji}", message.text):
        until_date_val = extract_time("1d")  # Set ban duration to 1 day
        try:
            await message.chat.ban_member(user_id=user_id, until_date=until_date_val)
        except Exception as error:
            await message.reply_text(str(error))
        else:
            await message.reply_text(f"Auto-temp-banned <a href='tg://user?id={user_id}'>{user_first_name}</a> for sending emojis.")


