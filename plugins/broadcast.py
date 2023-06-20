import logging
from pyrogram.errors import InputUserDeactivated, UserIsBlocked, PeerIdInvalid
from pyrogram.types import Message
from pyrogram import Client, filters
import datetime
import time
import os
from database.users_chats_db import db
from info import ADMINS
import asyncio

logging.basicConfig(level=logging.INFO)

@Client.on_message(filters.command("broadcast") & filters.user(ADMINS) & filters.reply)
async def broadcast(bot, message):
    users = await db.get_all_users()
    b_msg = message.reply_to_message
    sts = await message.reply_text('Broadcasting your messages...')
    start_time = time.time()
    total_users = await db.total_users_count()
    done = 0
    blocked = 0
    deleted = 0
    failed = 0
    success = 0
    for user in users:
        pti, sh = await broadcast_messages(int(user['id']), b_msg)
        if pti:
            success += 1
        elif pti is False:
            if sh == "Blocked":
                blocked += 1
            elif sh == "Deleted":
                deleted += 1
            elif sh == "Error":
                failed += 1
        done += 1
        if not done % 20:
            await sts.edit(
                f"Broadcast in progress:\n\nTotal Users {total_users}\nCompleted: {done} / {total_users}\nSuccess: {success}\nBlocked: {blocked}\nDeleted: {deleted}"
            )
    time_taken = datetime.timedelta(seconds=int(time.time() - start_time))
    await sts.delete()
    await bot.send_message(
        message.chat.id,
        f"Broadcast Completed:\nCompleted in {time_taken} seconds.\n\nTotal Users {total_users}\nCompleted: {done} / {total_users}\nSuccess: {success}\nBlocked: {blocked}\nDeleted: {deleted}",
    )


@Client.on_message(filters.command("clear_junk") & filters.user(ADMINS))
async def remove_junkuser__db(bot, message):
    if message.chat.type == "private":
        users = await db.get_all_users()
        b_msg = message
        sts = await message.reply_text("In progress...")
        start_time = time.time()
        total_users = await db.total_users_count()
        blocked = 0
        deleted = 0
        failed = 0
        done = 0
        for user in users:
            pti, sh = await clear_junk(int(user["id"]), b_msg)
            if pti is False:
                if sh == "Blocked":
                    blocked += 1
                elif sh == "Deleted":
                    deleted += 1
                elif sh == "Error":
                    failed += 1
            done += 1
            if not done % 20:
                await sts.edit(
                    f"In progress:\n\nTotal Users {total_users}\nCompleted: {done} / {total_users}\nBlocked: {blocked}\nDeleted: {deleted}"
                )
        time_taken = datetime.timedelta(seconds=int(time.time() - start_time))
        await sts.delete()
        await bot.send_message(
            message.chat.id,
            f"Completed:\nCompleted in {time_taken} seconds.\n\nTotal Users {total_users}\nCompleted: {done} / {total_users}\nBlocked: {blocked}\nDeleted: {deleted}",
        )
    else:
        await message.reply_text("This command can only be used in private chats.")

@Client.on_message(filters.private & filters.command("unblock") & filters.user(ADMINS))
async def unblock_all_blocked(bot, message):
    blocked_users = await db.get_blocked_users()
    for user in blocked_users:
        await bot.unblock_user(user["id"])
    await message.reply_text("All blocked users have been unblocked.")

# Additional helper functions if needed

async def broadcast_messages(user_id, message):
    try:
        await bot.send_message(user_id, message)
        return True, None
    except UserIsBlocked:
        return False, "Blocked"
    except InputUserDeactivated:
        return False, "Deleted"
    except Exception as e:
        logging.error(f"Error broadcasting message to user {user_id}: {e}")
        return False, "Error"

async def clear_junk(user_id, message):
    try:
        await bot.send_message(user_id, message)
        return True, None
    except UserIsBlocked:
        return False, "Blocked"
    except InputUserDeactivated:
        return False, "Deleted"
    except Exception as e:
        logging.error(f"Error sending message to user {user_id}: {e}")
        return False, "Error"


@Client.on_message(filters.command("group_broadcast") & filters.user(ADMINS) & filters.reply)
async def broadcast_group(bot, message):
    groups = await db.get_all_chats()
    b_msg = message.reply_to_message
    sts = await message.reply_text(text='Broadcasting your messages To Groups...')
    start_time = time.time()
    total_groups = await db.total_chat_count()
    done = 0
    failed = ""
    success = 0
    deleted = 0
    for group in groups:
        pti, sh, ex = await broadcast_messages_group(int(group['id']), b_msg)
        if pti == True:
            if sh == "Success":
                success += 1
        elif pti == False:
            if sh == "Deleted":
                deleted += 1
                failed += ex
                try:
                    await bot.leave_chat(int(group['id']))
                except Exception as e:
                    print(f"{e} > {group['id']}")
        done += 1
        if not done % 20:
            await sts.edit(f"Broadcast in progress:\n\nTotal Groups {total_groups}\nCompleted: {done} / {total_groups}\nSuccess: {success}\nDeleted: {deleted}")
    time_taken = datetime.timedelta(seconds=int(time.time()-start_time))
    await sts.delete()
    try:
        await message.reply_text(f"Broadcast Completed:\nCompleted in {time_taken} seconds.\n\nTotal Groups {total_groups}\nCompleted: {done} / {total_groups}\nSuccess: {success}\nDeleted: {deleted}\n\nFiled Reason:- {failed}")
    except MessageTooLong:
        with open('reason.txt', 'w+') as outfile:
            outfile.write(failed)
        await message.reply_document('reason.txt', caption=f"Completed:\nCompleted in {time_taken} seconds.\n\nTotal Groups {total_groups}\nCompleted: {done} / {total_groups}\nSuccess: {success}\nDeleted: {deleted}")
        os.remove("reason.txt")

      
@Client.on_message(filters.command(["junk_group", "clear_junk_group"]) & filters.user(ADMINS))
async def junk_clear_group(bot, message):
    groups = await db.get_all_chats()
    b_msg = message
    sts = await message.reply_text(text='In progress...')
    start_time = time.time()
    total_groups = await db.total_chat_count()
    done = 0
    failed = ""
    deleted = 0
    for group in groups:
        pti, sh, ex = await clear_junk_group(int(group['id']), b_msg)        
        if pti == False:
            if sh == "Deleted":
                deleted += 1
                failed += ex
                try:
                    await bot.leave_chat(int(group['id']))
                except Exception as e:
                    print(f"{e} > {group['id']}")
        done += 1
        if not done % 20:
            await sts.edit(f"In progress:\n\nTotal Groups {total_groups}\nCompleted: {done} / {total_groups}\nDeleted: {deleted}")
    time_taken = datetime.timedelta(seconds=int(time.time()-start_time))
    await sts.delete()
    try:
        await bot.send_message(message.chat.id, f"Completed:\nCompleted in {time_taken} seconds.\n\nTotal Groups {total_groups}\nCompleted: {done} / {total_groups}\nDeleted: {deleted}\n\nFiled Reason:- {failed}")
    except MessageTooLong:
        with open('junk.txt', 'w+') as outfile:
            outfile.write(failed)
        await message.reply_document('junk.txt', caption=f"Completed:\nCompleted in {time_taken} seconds.\n\nTotal Groups {total_groups}\nCompleted: {done} / {total_groups}\nDeleted: {deleted}")
        os.remove("junk.txt")

async def broadcast_messages_group(chat_id, message):
    try:
        await message.copy(chat_id=chat_id)
        return True, "Success", 'mm'
    except FloodWait as e:
        await asyncio.sleep(e.x)
        return await broadcast_messages_group(chat_id, message)
    except Exception as e:
        await db.delete_chat(int(chat_id))
        logging.info(f"{chat_id} - PeerIdInvalid")
        return False, "Deleted", f'{e}\n\n'

async def clear_junk_group(chat_id, message):
    try:
        kk = await message.copy(chat_id=chat_id)
        await kk.delete(True)
        return True, "Success", 'mm'
    except FloodWait as e:
        await asyncio.sleep(e.x)
        return await clear_junk_group(chat_id, message)
    except Exception as e:
        await db.delete_chat(int(chat_id))
        logging.info(f"{chat_id} - PeerIdInvalid")
        return False, "Deleted", f'{e}\n\n'

async def clear_junk(user_id, message):
    try:
        key = await message.copy(chat_id=user_id)
        await key.delete(True)
        return True, "Success"
    except FloodWait as e:
        await asyncio.sleep(e.x)
        return await clear_junk(user_id, message)
    except InputUserDeactivated:
        await db.delete_user(int(user_id))
        logging.info(f"{user_id}-Removed from Database, since deleted account.")
        return False, "Deleted"
    except UserIsBlocked:
        logging.info(f"{user_id} -Blocked the bot.")
        return False, "Blocked"
    except PeerIdInvalid:
        await db.delete_user(int(user_id))
        logging.info(f"{user_id} - PeerIdInvalid")
        return False, "Error"
    except Exception as e:
        return False, "Error"

async def broadcast_messages(user_id, message):
    try:
        await message.copy(chat_id=user_id)
        return True, "Success"
    except FloodWait as e:
        await asyncio.sleep(e.x)
        return await broadcast_messages(user_id, message)
    except InputUserDeactivated:
        await db.delete_user(int(user_id))
        logging.info(f"{user_id}-Removed from Database, since deleted account.")
        return False, "Deleted"
    except UserIsBlocked:
        logging.info(f"{user_id} -Blocked the bot.")
        return False, "Blocked"
    except PeerIdInvalid:
        await db.delete_user(int(user_id))
        logging.info(f"{user_id} - PeerIdInvalid")
        return False, "Error"
    except Exception as e:
        return False, "Error"
