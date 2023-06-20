from pyrogram import Client, filters
from pyrogram.types import Message
from plugins.helper.admin_check import admin_filter



@Client.on_message(filters.command("pin") & admin_fliter)
async def pin_command(client: Client, message: Message):
    if not message.reply_to_message:
        await message.reply_text("Please reply to a message to pin.")
        return

    try:
        await client.pin_chat_message(
            chat_id=message.chat.id,
            message_id=message.reply_to_message.message_id
        )
        await message.reply_text("Successfully pinned the message.")
    except Exception as e:
        await message.reply_text(f"An error occurred while pinning the message: {e}")


@Client.on_message(filters.command("unpin") & admin_fliter)
async def unpin_command(client: Client, message: Message):
    if not message.reply_to_message:
        await message.reply_text("Please reply to a message to unpin.")
        return

    try:
        await client.unpin_chat_message(
            chat_id=message.chat.id,
            message_id=message.reply_to_message.message_id
        )
        await message.reply_text("Successfully unpinned the message.")
    except Exception as e:
        await message.reply_text(f"An error occurred while unpinning the message: {e}")

