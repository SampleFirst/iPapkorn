from pyrogram.types import Message
from datetime import datetime, timedelta

def extract_user(message: Message) -> (int, str):
    """Extracts the user from a message"""
    user_id = None
    user_first_name = None

    if message.reply_to_message:
        user_id = message.reply_to_message.from_user.id
        user_first_name = message.reply_to_message.from_user.first_name
    elif len(message.command) > 1:
        if len(message.entities) > 1 and message.entities[1].type == "text_mention":
            required_entity = message.entities[1]
            user_id = required_entity.user.id
            user_first_name = required_entity.user.first_name
        else:
            user_id = message.command[1]
            user_first_name = user_id
        try:
            user_id = int(user_id)
        except ValueError:
            print("unknown")
    else:
        user_id = message.from_user.id
        user_first_name = message.from_user.first_name

    return user_id, user_first_name

def extract_time(time_val):
    if time_val.endswith(("s", "m", "h", "d")):
        unit = time_val[-1]
        time_num = time_val[:-1]
        if not time_num.isdigit():
            return None

        bantime = datetime.now()
        if unit == "s":
            bantime += timedelta(seconds=int(time_num))
        elif unit == "m":
            bantime += timedelta(minutes=int(time_num))
        elif unit == "h":
            bantime += timedelta(hours=int(time_num))
        elif unit == "d":
            bantime += timedelta(days=int(time_num))
        else:
            return None

        return bantime
    else:
        return None
