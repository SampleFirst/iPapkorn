import asyncio
from pyrogram import Client, filters, types
from plugins.helper.admin_check import admin_check


@Client.on_message(filters.command("purge") & (filters.group | filters.channel))
async def purge(client, message):
    if message.chat.type not in (types.ChatType.SUPERGROUP, types.ChatType.CHANNEL):
        return
    is_admin = await admin_check(client, message)
    if not is_admin:
        return

    status_message = await message.reply_text("...", quote=True)
    await message.delete()
    message_ids = []
    count_deletions = 0

    if message.reply_to_message:
        for message_id in range(message.reply_to_message.message_id, message.message_id):
            message_ids.append(message_id)
            if len(message_ids) == 100:
                await client.delete_messages(
                    chat_id=message.chat.id,
                    message_ids=message_ids,
                    revoke=True
                )
                count_deletions += len(message_ids)
                message_ids = []
        if len(message_ids) > 0:
            await client.delete_messages(
                chat_id=message.chat.id,
                message_ids=message_ids,
                revoke=True
            )
            count_deletions += len(message_ids)
    await status_message.edit_text(f"Deleted {count_deletions} messages")
    await asyncio.sleep(5)
    await status_message.delete()
