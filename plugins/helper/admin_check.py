from pyrogram.types import Message
from pyrogram import filters, types

async def admin_check(message: Message) -> bool:
    if not message.from_user:
        return False

    if message.chat.type not in (types.ChatType.GROUP, types.ChatType.SUPERGROUP):
        return False

    if message.from_user.id in (777000, 1087968824):  # Telegram Service Notifications, GroupAnonymousBot
        return True

    client = message._client
    chat_id = message.chat.id
    user_id = message.from_user.id

    check_status = await client.get_chat_member(chat_id=chat_id, user_id=user_id)
    admin_strings = [types.ChatMemberStatus.CREATOR, types.ChatMemberStatus.ADMINISTRATOR]
    
    if check_status.status not in admin_strings:
        return False
    else:
        return True

async def admin_filter_func(_, __, message: Message) -> bool:
    return await admin_check(message)

admin_filter = filters.create(func=admin_filter_func, name="AdminFilter")
