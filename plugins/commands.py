import os
import logging
import random
import asyncio
from Script import script
from pyrogram import Client, filters, enums
from pyrogram.errors import ChatAdminRequired, FloodWait
from pyrogram.types import InlineKeyboardButton, InlineKeyboardMarkup
from database.ia_filterdb import Media, get_file_details, unpack_new_file_id
from database.users_chats_db import db
from info import CHANNELS, ADMINS, AUTH_CHANNEL, LOG_CHANNEL, PICS, BATCH_FILE_CAPTION, CUSTOM_FILE_CAPTION, PROTECT_CONTENT, START_MESSAGE, FORCE_SUB_TEXT, SUPPORT_CHAT
from utils import get_settings, get_size, is_subscribed, save_group_settings, temp
from database.connections_mdb import active_connection
import re
import json
import base64
logger = logging.getLogger(__name__)

BATCH_FILES = {}

@Client.on_message(filters.command("start") & filters.incoming)
async def start(client, message):
    if message.chat.type in [enums.ChatType.GROUP, enums.ChatType.SUPERGROUP]:
        buttons = [[           
            InlineKeyboardButton('📢 𝚄𝙿𝙳𝙰𝚃𝙴𝚂 📢', url=f'https://t.me/{SUPPORT_CHAT}')
            ],[
            InlineKeyboardButton('ℹ️ 𝙷𝙴𝙻𝙿 ℹ️', url=f"https://t.me/{temp.U_NAME}?start=help")
            ]]
        await message.reply(START_MESSAGE.format(user=message.from_user.mention if message.from_user else message.chat.title, bot=temp.B_LINK), reply_markup=InlineKeyboardMarkup(buttons), disable_web_page_preview=True)                    
        await asyncio.sleep(2) 
        if not await db.get_chat(message.chat.id):
            total=await client.get_chat_members_count(message.chat.id)
            await client.send_message(LOG_CHANNEL, script.LOG_TEXT_G.format(a=message.chat.title, b=message.chat.id, c=message.chat.username, d=total, f=temp.B_LINK, e="Unknown"))       
            await db.add_chat(message.chat.id, message.chat.title, message.chat.username)
        return 
    if not await db.is_user_exist(message.from_user.id):
        await db.add_user(message.from_user.id, message.from_user.first_name)
        await client.send_message(LOG_CHANNEL, script.LOG_TEXT_P.format(message.from_user.id, message.from_user.mention, message.from_user.username, temp.U_NAME))
    if len(message.command) != 2:
        buttons = [[
            InlineKeyboardButton('➕️ ᴀᴅᴅ ᴍᴇ ᴛᴏ ʏᴏᴜʀ ɢʀᴏᴜᴘs ➕️', url=f'http://t.me/{temp.U_NAME}?startgroup=true')
        ],[
            InlineKeyboardButton('🔍 sᴇᴀʀᴄʜ', switch_inline_query_current_chat=''),
            InlineKeyboardButton('📢 ᴜᴘᴅᴀᴛᴇ', url='https://t.me/iPapkornUpdate')
        ],[
            InlineKeyboardButton('ℹ️ ʜᴇʟᴘ', callback_data='help'),
            InlineKeyboardButton('😊 ᴀʙᴏᴜᴛ', callback_data='about')
        ],[
            InlineKeyboardButton('🔥 ᴊᴏɪɴ ᴡɪᴛʜ ʏᴏᴜᴛᴜʙᴇ 🔥', url='https://youtube.com/@InvisibleYTV')
        ]]
        reply_markup = InlineKeyboardMarkup(buttons)
        await message.reply_chat_action(enums.ChatAction.TYPING)
        m=await message.reply_sticker("CAACAgUAAxkBAAIFNGJSlfOErbkSeLt9SnOniU-58UUBAAKaAAPIlGQULGXh4VzvJWoeBA")
        await asyncio.sleep(1)
        await m.delete()
        await message.reply_photo(
            photo=random.choice(PICS),
            caption=START_MESSAGE.format(user=message.from_user.mention, bot=temp.B_LINK),
            reply_markup=reply_markup,
            parse_mode=enums.ParseMode.HTML
        )
        return
    if AUTH_CHANNEL and not await is_subscribed(client, message):
        try:
            invite_link = await client.create_chat_invite_link(int(AUTH_CHANNEL))
        except ChatAdminRequired:
            logger.error("Make sure Bot is admin in Forcesub channel")
            return
        btn = [
            [
                InlineKeyboardButton(
                    "🔥 𝙹𝙾𝙸𝙽 𝚈𝙾𝚄𝚃𝚄𝙱𝙴 𝙲𝙷𝙰𝙽𝙽𝙴𝙻 🔥", url='https://youtube.com/@InvisibleYTV'
                )
            ],[
                InlineKeyboardButton(
                    "📢 𝙹𝙾𝙸𝙽 𝚄𝙿𝙳𝙰𝚃𝙴𝚂 𝙲𝙷𝙰𝙽𝙽𝙴𝙻 📢", url=invite_link.invite_link
                )
            ]
        ]

        if message.command[1] != "subscribe":
            try:
                kk, file_id = message.command[1].split("_", 1)
                pre = 'checksubp' if kk == 'filep' else 'checksub' 
                btn.append([InlineKeyboardButton(" 🔄 Try Again", callback_data=f"{pre}#{file_id}")])
            except (IndexError, ValueError):
                btn.append([InlineKeyboardButton(" 🔄 Try Again", url=f"https://t.me/{temp.U_NAME}?start={message.command[1]}")])
        await client.send_message(
            chat_id=message.from_user.id,
            text=FORCE_SUB_TEXT,
            reply_markup=InlineKeyboardMarkup(btn),
            parse_mode=enums.ParseMode.DEFAULT
            )
        return
    if len(message.command) == 2 and message.command[1] in ["subscribe", "error", "okay", "help"]:
        buttons = [[
            InlineKeyboardButton('➕️ ᴀᴅᴅ ᴍᴇ ᴛᴏ ʏᴏᴜʀ ɢʀᴏᴜᴘs ➕️', url=f'http://t.me/{temp.U_NAME}?startgroup=true')
        ],[
            InlineKeyboardButton('🔍 sᴇᴀʀᴄʜ', switch_inline_query_current_chat=''),
            InlineKeyboardButton('📢 ᴜᴘᴅᴀᴛᴇ', url='https://t.me/iPapkornUpdate')
        ],[
            InlineKeyboardButton('ℹ️ ʜᴇʟᴘ', callback_data='help'),
            InlineKeyboardButton('😊 ᴀʙᴏᴜᴛ', callback_data='about')
        ],[
            InlineKeyboardButton('🔥 ᴊᴏɪɴ ᴡɪᴛʜ ʏᴏᴜᴛᴜʙᴇ 🔥', url='https://youtube.com/@InvisibleYTV')
        ]]
        reply_markup = InlineKeyboardMarkup(buttons)
        await message.reply_chat_action(enums.ChatAction.TYPING)
        m=await message.reply_sticker("CAACAgUAAxkBAAIFNGJSlfOErbkSeLt9SnOniU-58UUBAAKaAAPIlGQULGXh4VzvJWoeBA")
        await asyncio.sleep(1)
        await m.delete()
        await message.reply_photo(
            photo=random.choice(PICS),
            caption=START_MESSAGE.format(user=message.from_user.mention, bot=temp.B_LINK),
            reply_markup=reply_markup,
            parse_mode=enums.ParseMode.HTML
        )
        return
    data = message.command[1]
    try:
        pre, file_id = data.split('_', 1)
    except:
        file_id = data
        pre = ""
    if data.split("-", 1)[0] == "BATCH":
        sts = await message.reply("Please wait")
        file_id = data.split("-", 1)[1]
        msgs = BATCH_FILES.get(file_id)
        if not msgs:
            file = await client.download_media(file_id)
            try: 
                with open(file) as file_data:
                    msgs=json.loads(file_data.read())
            except:
                await sts.edit("FAILED")
                return await client.send_message(LOG_CHANNEL, "UNABLE TO OPEN FILE.")
            os.remove(file)
            BATCH_FILES[file_id] = msgs
        for msg in msgs:
            title = msg.get("title")
            size=get_size(int(msg.get("size", 0)))
            f_caption=msg.get("caption", "")
            if BATCH_FILE_CAPTION:
                try:
                    f_caption=BATCH_FILE_CAPTION.format(mention=message.from_user.mention, file_name= '' if title is None else title, file_size='' if size is None else size, file_caption='' if f_caption is None else f_caption)
                except Exception as e:
                    logger.exception(e)
                    f_caption=f_caption
            if f_caption is None:
                f_caption = f"{title}"
            try:
                await client.send_cached_media(
                    chat_id=message.from_user.id,
                    file_id=msg.get("file_id"),
                    caption=f_caption,
                    protect_content=msg.get('protect', False),
                    )
            except FloodWait as e:
                await asyncio.sleep(e.x)
                logger.warning(f"Floodwait of {e.x} sec.")
                await client.send_cached_media(
                    chat_id=message.from_user.id,
                    file_id=msg.get("file_id"),
                    caption=f_caption,
                    protect_content=msg.get('protect', False),
                    )
            except Exception as e:
                logger.warning(e, exc_info=True)
                continue
            await asyncio.sleep(1) 
        await sts.delete()
        return
    elif data.split("-", 1)[0] == "DSTORE":
        sts = await message.reply("Please wait")
        b_string = data.split("-", 1)[1]
        decoded = (base64.urlsafe_b64decode(b_string + "=" * (-len(b_string) % 4))).decode("ascii")
        try:
            f_msg_id, l_msg_id, f_chat_id, protect = decoded.split("_", 3)
        except:
            f_msg_id, l_msg_id, f_chat_id = decoded.split("_", 2)
            protect = "/pbatch" if PROTECT_CONTENT else "batch"
        diff = int(l_msg_id) - int(f_msg_id)
        async for msg in client.iter_messages(int(f_chat_id), int(l_msg_id), int(f_msg_id)):
            if msg.media:
                media = getattr(msg, msg.media)
                if BATCH_FILE_CAPTION:
                    try:
                        f_caption=BATCH_FILE_CAPTION.format(mention=message.from_user.mention, file_name=getattr(media, 'file_name', ''), file_size=getattr(media, 'file_size', ''), file_caption=getattr(msg, 'caption', ''))
                    except Exception as e:
                        logger.exception(e)
                        f_caption = getattr(msg, 'caption', '')
                else:
                    media = getattr(msg, msg.media)
                    file_name = getattr(media, 'file_name', '')
                    f_caption = getattr(msg, 'caption', file_name)
                try:
                    await msg.copy(message.chat.id, caption=f_caption, protect_content=True if protect == "/pbatch" else False)
                except FloodWait as e:
                    await asyncio.sleep(e.x)
                    await msg.copy(message.chat.id, caption=f_caption, protect_content=True if protect == "/pbatch" else False)
                except Exception as e:
                    logger.exception(e)
                    continue
            elif msg.empty:
                continue
            else:
                try:
                    await msg.copy(message.chat.id, protect_content=True if protect == "/pbatch" else False)
                except FloodWait as e:
                    await asyncio.sleep(e.x)
                    await msg.copy(message.chat.id, protect_content=True if protect == "/pbatch" else False)
                except Exception as e:
                    logger.exception(e)
                    continue
            await asyncio.sleep(1) 
        return await sts.delete()
        

    files_ = await get_file_details(file_id)           
    if not files_:
        pre, file_id = ((base64.urlsafe_b64decode(data + "=" * (-len(data) % 4))).decode("ascii")).split("_", 1)
        try:
            msg = await client.send_cached_media(
                chat_id=message.from_user.id,
                file_id=file_id,
                protect_content=True if pre == 'filep' else False,
                )
            filetype = msg.media
            file = getattr(msg, filetype)
            title = file.file_name
            size=get_size(file.file_size)
            f_caption = f"<code>{title}</code>"
            if CUSTOM_FILE_CAPTION:
                try:
                    f_caption=CUSTOM_FILE_CAPTION.format(mention=message.from_user.mention, file_name= '' if title is None else title, file_size='' if size is None else size, file_caption='')
                except:
                    return
            await msg.edit_caption(f_caption)
            return
        except:
            pass
        return await message.reply('No such file exist.')
    files = files_[0]
    title = files.file_name
    size=get_size(files.file_size)
    f_caption=files.caption
    if CUSTOM_FILE_CAPTION:
        try:
            f_caption=CUSTOM_FILE_CAPTION.format(mention=message.from_user.mention, file_name= '' if title is None else title, file_size='' if size is None else size, file_caption='' if f_caption is None else f_caption)
        except Exception as e:
            logger.exception(e)
            f_caption=f_caption
    if f_caption is None:
        f_caption = f"{files.file_name}"
    await client.send_cached_media(
        chat_id=message.from_user.id,
        file_id=file_id,
        caption=f_caption,
        protect_content=True if pre == 'filep' else False,
        )
                    

@Client.on_message(filters.command('channel') & filters.user(ADMINS))
async def channel_info(bot, message):
           
    """Send basic information of channel"""
    if isinstance(CHANNELS, (int, str)):
        channels = [CHANNELS]
    elif isinstance(CHANNELS, list):
        channels = CHANNELS
    else:
        raise ValueError("Unexpected type of CHANNELS")

    text = '📑 **Indexed channels/groups**\n'
    for channel in channels:
        chat = await bot.get_chat(channel)
        if chat.username:
            text += '\n@' + chat.username
        else:
            text += '\n' + chat.title or chat.first_name

    text += f'\n\n**Total:** {len(CHANNELS)}'

    if len(text) < 4096:
        await message.reply(text)
    else:
        file = 'Indexed channels.txt'
        with open(file, 'w') as f:
            f.write(text)
        await message.reply_document(file)
        os.remove(file)

@Client.on_message(filters.command('findfiles') & filters.user(ADMINS))
async def find_files(client, message):
    """Find files in the database based on search criteria"""
    search_query = " ".join(message.command[1:])  # Extract the search query from the command

    if not search_query:
        return await message.reply('✨ Please provide a name.\n\nExample: /findfiles Kantara.', quote=True)

    # Build the MongoDB query to search for files
    query = {
        'file_name': {"$regex": f".*{re.escape(search_query)}.*", "$options": "i"}
    }

    # Fetch the matching files from the database
    results = await Media.collection.find(query).to_list(length=None)

    if len(results) > 0:
        # Sort results alphabetically by file name
        results.sort(key=lambda x: x['file_name'])

        confirmation_message = f'✨ {len(results)} files found matching the search query "{search_query}" in the database:\n\n'
        starting_query = {
            'file_name': {"$regex": f"^{re.escape(search_query)}", "$options": "i"}
        }
        starting_results = await Media.collection.find(starting_query).to_list(length=None)

        starting_results.sort(key=lambda x: x['file_name'])

        confirmation_message += f'✨ {len(starting_results)} files found starting with "{search_query}" in the database.\n\n'
        confirmation_message += '✨ Please select the option for easier searching:'

        keyboard = InlineKeyboardMarkup(
            [
                [
                    InlineKeyboardButton("🌟 Find Related Name Files", callback_data=f"related_files:1:{search_query}")
                ],
                [
                    InlineKeyboardButton("🌟 Find Starting Name Files", callback_data=f"starting_files:1:{search_query}")
                ],
                [
                    InlineKeyboardButton("❌ Cancel", callback_data="cancel")
                ]
            ]
        )

        await message.reply_text(confirmation_message, reply_markup=keyboard)
    else:
        await message.reply_text(f'😎 No files found matching the search query "{search_query}" in the database')


@Client.on_callback_query(filters.regex('^related_files'))
async def find_related_files(client, callback_query):
    data = callback_query.data.split(":")
    page = int(data[1])
    search_query = data[2]
    query = {
        'file_name': {"$regex": f".*{re.escape(search_query)}.*", "$options": "i"}
    }
    results = await Media.collection.find(query).to_list(length=None)

    total_results = len(results)
    num_pages = total_results // RESULTS_PER_PAGE + 1

    # Sort results alphabetically by file name
    results.sort(key=lambda x: x['file_name'])

    start_index = (page - 1) * RESULTS_PER_PAGE
    end_index = start_index + RESULTS_PER_PAGE
    current_results = results[start_index:end_index]

    result_message = f'{len(current_results)} files found with related names to "{search_query}" in the database:\n\n'
    for result in current_results:
        file_size = format_file_size(result['file_size'])
        result_message += f'File Name: {result["file_name"]}\n'
        result_message += f'File Size: {file_size}\n\n'

    buttons = []

    if page > 1:
        buttons.append(InlineKeyboardButton("⬅️ Back", callback_data=f"related_files:{page - 1}:{search_query}"))

    if page < num_pages:
        buttons.append(InlineKeyboardButton("Next ➡️", callback_data=f"related_files:{page + 1}:{search_query}"))

    buttons.append(InlineKeyboardButton("🔚 Cancel", callback_data="cancel_find"))

    # Create button groups with two buttons each
    button_groups = [buttons[i:i + 2] for i in range(0, len(buttons), 2)]
    keyboard = InlineKeyboardMarkup(button_groups)

    await callback_query.message.edit_text(result_message, reply_markup=keyboard)
    await callback_query.answer()


@Client.on_callback_query(filters.regex('^starting_files'))
async def find_starting_files(client, callback_query):
    data = callback_query.data.split(":")
    page = int(data[1])
    search_query = data[2]
    query = {
        'file_name': {"$regex": f"^{re.escape(search_query)}", "$options": "i"}
    }
    results = await Media.collection.find(query).to_list(length=None)

    total_results = len(results)
    num_pages = total_results // RESULTS_PER_PAGE + 1

    # Sort results alphabetically by file name
    results.sort(key=lambda x: x['file_name'])

    start_index = (page - 1) * RESULTS_PER_PAGE
    end_index = start_index + RESULTS_PER_PAGE
    current_results = results[start_index:end_index]

    result_message = f'{len(current_results)} files found with names starting "{search_query}" in the database:\n\n'
    for result in current_results:
        file_size = format_file_size(result['file_size'])
        result_message += f'File Name: {result["file_name"]}\n'
        result_message += f'File Size: {file_size}\n\n'

    buttons = []

    if page > 1:
        buttons.append(InlineKeyboardButton("⬅️ Back", callback_data=f"starting_files:{page - 1}:{search_query}"))

    if page < num_pages:
        buttons.append(InlineKeyboardButton("Next ➡️", callback_data=f"starting_files:{page + 1}:{search_query}"))

    buttons.append(InlineKeyboardButton("🔚 Cancel", callback_data="cancel_find"))

    # Create button groups with two buttons each
    button_groups = [buttons[i:i + 2] for i in range(0, len(buttons), 2)]
    keyboard = InlineKeyboardMarkup(button_groups)

    await callback_query.message.edit_text(result_message, reply_markup=keyboard)
    await callback_query.answer()


def format_file_size(size_in_bytes):
    """Format file size in bytes to human-readable format (MB or GB)"""
    size_in_mb = size_in_bytes / (1024 * 1024)
    size_in_gb = size_in_bytes / (1024 * 1024 * 1024)

    if size_in_gb >= 1:
        return f'{size_in_gb:.2f} GB'
    else:
        return f'{size_in_mb:.2f} MB'



                   
@Client.on_message(filters.command("findpixels") & filters.user(ADMINS))
async def find_pixels_command(bot, message):
    keyboard = InlineKeyboardMarkup(
        [
            [
                InlineKeyboardButton("480p", callback_data="findpixels_pixel_480p_1"),
                InlineKeyboardButton("720p", callback_data="findpixels_pixel_720p_1"),
            ],
            [
                InlineKeyboardButton("1080p", callback_data="findpixels_pixel_1080p_1"),
                InlineKeyboardButton("4K", callback_data="findpixels_pixel_4k_1"),
            ],
            [
                InlineKeyboardButton("Cancel", callback_data="findpixels_cancel"),
            ]
        ]
    )

    await message.reply_text(
        "🔍 Select a pixel resolution to find related files:\n\n"
        "• '480p': Find files related to 480p resolution.\n"
        "• '720p': Find files related to 720p resolution.\n"
        "• '1080p': Find files related to 1080p resolution.\n"
        "• '4K': Find files related to 4K resolution.\n"
        "• 'Cancel': Cancel the process.",
        reply_markup=keyboard,
        quote=True
    )

@Client.on_callback_query(filters.user(ADMINS) & filters.regex(r"^findpixels_pixel_(\d+p)_(\d+)$"))
async def find_pixels_callback(bot, callback_query):
    pixel_resolution = callback_query.data.split("_")[1]
    page_num = int(callback_query.data.split("_")[2])
    per_page = 10  # Number of files per page

    files = await Media.find({"pixels": pixel_resolution}).to_list(length=None)
    total_files = len(files)
    total_pages = (total_files + per_page - 1) // per_page

    start_index = (page_num - 1) * per_page
    end_index = start_index + per_page

    file_list = ""
    for file in files[start_index:end_index]:
        file_name = file["name"]
        file_size_mb = round(file["size"] / (1024 * 1024), 2)
        file_list += f"• {file_name} ({file_size_mb} MB)\n"

    if file_list:
        keyboard = InlineKeyboardMarkup(
            [
                [
                    InlineKeyboardButton("Back", callback_data=f"findpixels_pixel_{pixel_resolution}_{page_num - 1}"),
                    InlineKeyboardButton("Next", callback_data=f"findpixels_pixel_{pixel_resolution}_{page_num + 1}"),
                ]
            ]
        )

        text = f"📋 List of files related to {pixel_resolution} resolution:\n\n{file_list}"
        if page_num < total_pages:
            text += "\n\nUse 'Next' button to view the next page."

        await callback_query.message.edit_text(text, reply_markup=keyboard)
    else:
        await callback_query.message.edit_text(f"❎ No files found related to {pixel_resolution} resolution.")

@Client.on_callback_query(filters.user(ADMINS) & filters.regex(r"^findpixels_cancel$"))
async def find_pixels_cancel_callback(bot, callback_query):
    await callback_query.message.edit_text("❌ Process canceled.")
    await callback_query.answer()




@Client.on_message(filters.command('delete') & filters.user(ADMINS))
async def delete(bot, message):
    """Delete file from database"""
    reply = message.reply_to_message
    if reply and reply.media:
        msg = await message.reply("Processing...⏳", quote=True)
    else:
        await message.reply('Reply to file with /delete which you want to delete', quote=True)
        return

    for file_type in ("document", "video", "audio"):
        media = getattr(reply, file_type, None)
        if media is not None:
            break
    else:
        await msg.edit('This is not supported file format')
        return
    
    file_id, file_ref = unpack_new_file_id(media.file_id)

    result = await Media.collection.delete_one({
        '_id': file_id,
    })
    if result.deleted_count:
        await msg.edit('File is successfully deleted from database')
    else:
        file_name = re.sub(r"(_|\-|\.|\+)", " ", str(media.file_name))
        result = await Media.collection.delete_many({
            'file_name': file_name,
            'file_size': media.file_size,
            'mime_type': media.mime_type
            })
        if result.deleted_count:
            await msg.edit('File is successfully deleted from database')
        else:
            # files indexed before https://github.com/EvamariaTG/EvaMaria/commit/f3d2a1bcb155faf44178e5d7a685a1b533e714bf#diff-86b613edf1748372103e94cacff3b578b36b698ef9c16817bb98fe9ef22fb669R39 
            # have original file name.
            result = await Media.collection.delete_many({
                'file_name': media.file_name,
                'file_size': media.file_size,
                'mime_type': media.mime_type
            })
            if result.deleted_count:
                await msg.edit('File is successfully deleted from database')
            else:
                await msg.edit('File not found in database')


@Client.on_message(filters.command('deleteall') & filters.user(ADMINS))
async def delete_all_index(bot, message):
    await message.reply_text(
        'This will delete all indexed files.\nDo you want to continue??',
        reply_markup=InlineKeyboardMarkup(
            [
                [
                    InlineKeyboardButton(
                        text="YES", callback_data="autofilter_delete"
                    )
                ],
                [
                    InlineKeyboardButton(
                        text="CANCEL", callback_data="close_data"
                    )
                ],
            ]
        ),
        quote=True,
    )


@Client.on_callback_query(filters.regex(r'^autofilter_delete'))
async def delete_all_index_confirm(bot, message):
    await Media.collection.drop()
    await message.answer('Piracy Is Crime')
    await message.message.edit('Succesfully Deleted All The Indexed Files.')

@Client.on_message(filters.command("deletefiletype") & filters.user(ADMINS))
async def delete_file_type_command(bot, message):
    """Command handler for deleting files of a specific type from the database"""
    keyboard = InlineKeyboardMarkup(
        [
            [
                InlineKeyboardButton("📥 Document", callback_data="delete_filetype_document"),
                InlineKeyboardButton("🎬 Video", callback_data="delete_filetype_video"),
            ],
            [
                InlineKeyboardButton("🎧 Audio", callback_data="delete_filetype_audio"),
                InlineKeyboardButton("❎ Cancel", callback_data="dft_cancel"),
            ]
        ]
    )

    await message.reply(
        "🗑 Select the type of files you want to delete!\n\n🗑 This will delete related files from the database:",
        reply_markup=keyboard,
        quote=True,
    )

@Client.on_callback_query(filters.user(ADMINS) & filters.regex(r"^delete_filetype_(document|video|audio)$"))
async def delete_file_type_callback(bot, callback_query):
    """Callback handler for deleting files of a specific type"""
    file_type = callback_query.data.replace("delete_filetype_", "")

    total_files = await Media.count_documents({"file_type": file_type})

    if total_files > 0:
        keyboard = InlineKeyboardMarkup(
            [
                [
                    InlineKeyboardButton("🗑 Delete", callback_data=f"confirm_delete_{file_type}"),
                ],
                [
                    InlineKeyboardButton("🏠 Home", callback_data="deletefiletype"),
                ]
            ]
        )

        await callback_query.message.edit_text(
            f"✅ Found {total_files} {file_type}(s) in the database.\n\n"
            "Please select an action:",
            reply_markup=keyboard,
        )
    else:
        keyboard = InlineKeyboardMarkup(
            [
                [
                    InlineKeyboardButton("🏠 Home", callback_data="deletefiletype"),
                    InlineKeyboardButton("❎ Cancel", callback_data="dft_cancel"),
                ]
            ]
        )

        await callback_query.message.edit_text(f"No {file_type}s found in the database.", reply_markup=keyboard)

@Client.on_callback_query(filters.user(ADMINS) & filters.regex(r"^confirm_delete_document$"))
async def confirm_delete_document_callback(bot, callback_query):
    """Callback handler for confirming the deletion of document files"""
    result = await Media.collection.delete_many({"file_type": "document"})

    if result.deleted_count:
        keyboard = InlineKeyboardMarkup(
            [
                [
                    InlineKeyboardButton("🏠 Home", callback_data="deletefiletype"),
                    InlineKeyboardButton("❎ Cancel", callback_data="dft_cancel"),
                ]
            ]
        )

        await callback_query.message.edit_text(
            "🗑 All document files have been successfully deleted from the database.",
            reply_markup=keyboard,
        )
    else:
        keyboard = InlineKeyboardMarkup(
            [
                [
                    InlineKeyboardButton("🏠 Home", callback_data="deletefiletype"),
                    InlineKeyboardButton("❎ Cancel", callback_data="dft_cancel"),
                ]
            ]
        )

        await callback_query.message.edit_text(
            "❎ No document files found in the database.",
            reply_markup=keyboard,
        )

@Client.on_callback_query(filters.user(ADMINS) & filters.regex(r"^confirm_delete_video$"))
async def confirm_delete_video_callback(bot, callback_query):
    """Callback handler for confirming the deletion of video files"""
    result = await Media.collection.delete_many({"file_type": "video"})

    if result.deleted_count:
        keyboard = InlineKeyboardMarkup(
            [
                [
                    InlineKeyboardButton("🏠 Home", callback_data="deletefiletype"),
                    InlineKeyboardButton("❎ Cancel", callback_data="dft_cancel"),
                ]
            ]
        )

        await callback_query.message.edit_text(
            "🗑 All video files have been successfully deleted from the database.",
            reply_markup=keyboard,
        )
    else:
        keyboard = InlineKeyboardMarkup(
            [
                [
                    InlineKeyboardButton("🏠 Home", callback_data="deletefiletype"),
                    InlineKeyboardButton("❎ Cancel", callback_data="dft_cancel"),
                ]
            ]
        )

        await callback_query.message.edit_text(
            "🗑 No video files found in the database.",
            reply_markup=keyboard,
        )

@Client.on_callback_query(filters.user(ADMINS) & filters.regex(r"^confirm_delete_audio$"))
async def confirm_delete_audio_callback(bot, callback_query):
    """Callback handler for confirming the deletion of audio files"""
    result = await Media.collection.delete_many({"file_type": "audio"})

    if result.deleted_count:
        keyboard = InlineKeyboardMarkup(
            [
                [
                    InlineKeyboardButton("🏠 Home", callback_data="deletefiletype"),
                    InlineKeyboardButton("❎ Cancel", callback_data="dft_cancel"),
                ]
            ]
        )

        await callback_query.message.edit_text(
            "🗑 All audio files have been successfully deleted from the database.",
            reply_markup=keyboard,
        )
    else:
        keyboard = InlineKeyboardMarkup(
            [
                [
                    InlineKeyboardButton("🏠 Home", callback_data="deletefiletype"),
                    InlineKeyboardButton("❎ Cancel", callback_data="dft_cancel"),
                ]
            ]
        )

        await callback_query.message.edit_text(
            "❎ No audio files found in the database.",
            reply_markup=keyboard,
        )

@Client.on_callback_query(filters.user(ADMINS) & filters.regex(r"^dft_cancel$"))
async def delete_file_type_cancel_callback(bot, callback_query):
    """Callback handler for canceling the delete file type operation"""
    await callback_query.message.edit_text("Delete file type operation canceled.")
    await callback_query.answer()
    

@Client.on_message(filters.command('settings'))
async def settings(client, message):
    userid = message.from_user.id if message.from_user else None
    if not userid:
        return await message.reply(f"You are anonymous admin. Use /connect {message.chat.id} in PM")
    chat_type = message.chat.type

    if chat_type == enums.ChatType.PRIVATE:
        grpid = await active_connection(str(userid))
        if grpid is not None:
            grp_id = grpid
            try:
                chat = await client.get_chat(grpid)
                title = chat.title
            except:
                await message.reply_text("Make sure I'm present in your group!!", quote=True)
                return
        else:
            await message.reply_text("I'm not connected to any groups!", quote=True)
            return

    elif chat_type in [enums.ChatType.GROUP, enums.ChatType.SUPERGROUP]:
        grp_id = message.chat.id
        title = message.chat.title

    else:
        return

    st = await client.get_chat_member(grp_id, userid)
    if (
            st.status != enums.ChatMemberStatus.ADMINISTRATOR
            and st.status != enums.ChatMemberStatus.OWNER
            and str(userid) not in ADMINS
    ):
        return

    settings = await get_settings(grp_id)
    if settings is not None:
        buttons = [[
            ],[            
            InlineKeyboardButton('𝐁𝐔𝐓𝐓𝐎𝐍 𝐒𝐓𝐘𝐋𝐄', callback_data=f'setgs#button#{settings["button"]}#{str(grp_id)}'),
            InlineKeyboardButton('𝐒𝐈𝐍𝐆𝐋𝐄' if settings["button"] else '𝐃𝐎𝐔𝐁𝐋𝐄',  callback_data=f'setgs#button#{settings["button"]}#{str(grp_id)}')
            ],[
            InlineKeyboardButton('𝐁𝐎𝐓 𝐏𝐌', callback_data=f'setgs#botpm#{settings["botpm"]}#{str(grp_id)}'),
            InlineKeyboardButton('✅ 𝐘𝐄𝐒' if settings["botpm"] else '🚫 𝐍𝐎', callback_data=f'setgs#botpm#{settings["botpm"]}#{str(grp_id)}')
            ],[                
            InlineKeyboardButton('𝐅𝐈𝐋𝐄 𝐒𝐄𝐂𝐔𝐑𝐄', callback_data=f'setgs#file_secure#{settings["file_secure"]}#{str(grp_id)}'),
            InlineKeyboardButton('✅ 𝐘𝐄𝐒' if settings["file_secure"] else '🚫 𝐍𝐎',  callback_data=f'setgs#file_secure#{settings["file_secure"]}#{str(grp_id)}')
            ],[
            InlineKeyboardButton('𝐈𝐌𝐃𝐁', callback_data=f'setgs#imdb#{settings["imdb"]}#{str(grp_id)}'),
            InlineKeyboardButton('✅ 𝐘𝐄𝐒' if settings["imdb"] else '🚫 𝐍𝐎', callback_data=f'setgs#imdb#{settings["imdb"]}#{str(grp_id)}')
            ],[
            InlineKeyboardButton('𝐒𝐏𝐄𝐋𝐋 𝐂𝐇𝐄𝐂𝐊', callback_data=f'setgs#spell_check#{settings["spell_check"]}#{str(grp_id)}'),
            InlineKeyboardButton('✅ 𝐘𝐄𝐒' if settings["spell_check"] else '🚫 𝐍𝐎', callback_data=f'setgs#spell_check#{settings["spell_check"]}#{str(grp_id)}')
            ],[
            InlineKeyboardButton('𝐖𝐄𝐋𝐂𝐎𝐌𝐄', callback_data=f'setgs#welcome#{settings["welcome"]}#{str(grp_id)}'),
            InlineKeyboardButton('✅ 𝐘𝐄𝐒' if settings["welcome"] else '🚫 𝐍𝐎', callback_data=f'setgs#welcome#{settings["welcome"]}#{str(grp_id)}')               
        ]]
        reply_markup = InlineKeyboardMarkup(buttons)
        await message.reply_text(
            text=f"<b>Change Your Settings for {title} As Your Wish ⚙</b>",
            reply_markup=reply_markup,
            disable_web_page_preview=True,
            parse_mode=enums.ParseMode.HTML,
            reply_to_message_id=message.id
        )



@Client.on_message(filters.command('set_template'))
async def save_template(client, message):
    sts = await message.reply("Checking template")
    userid = message.from_user.id if message.from_user else None
    if not userid:
        return await message.reply(f"You are anonymous admin. Use /connect {message.chat.id} in PM")
    chat_type = message.chat.type

    if chat_type == enums.ChatType.PRIVATE:
        grpid = await active_connection(str(userid))
        if grpid is not None:
            grp_id = grpid
            try:
                chat = await client.get_chat(grpid)
                title = chat.title
            except:
                await message.reply_text("Make sure I'm present in your group!!", quote=True)
                return
        else:
            await message.reply_text("I'm not connected to any groups!", quote=True)
            return

    elif chat_type in [enums.ChatType.GROUP, enums.ChatType.SUPERGROUP]:
        grp_id = message.chat.id
        title = message.chat.title

    else:
        return

    st = await client.get_chat_member(grp_id, userid)
    if (
            st.status != enums.ChatMemberStatus.ADMINISTRATOR
            and st.status != enums.ChatMemberStatus.OWNER
            and str(userid) not in ADMINS
    ):
        return

    if len(message.command) < 2:
        return await sts.edit("No Input!!")
    template = message.text.split(" ", 1)[1]
    await save_group_settings(grp_id, 'template', template)
    await sts.edit(f"Successfully changed template for {title} to\n\n{template}")


@Client.on_message(filters.command("usend") & filters.user(ADMINS))
async def send_msg(bot, message):
    if message.reply_to_message:
        target_id = message.text
        command = ["/usend"]
        for cmd in command:
            if cmd in target_id:
                target_id = target_id.replace(cmd, "")
        success = False
        try:
            user = await bot.get_users(int(target_id))
            await message.reply_to_message.copy(int(user.id))
            success = True
        except Exception as e:
            await message.reply_text(f"<b>Eʀʀᴏʀ :- <code>{e}</code></b>")
        if success:
            await message.reply_text(f"<b>Yᴏᴜʀ Mᴇssᴀɢᴇ Hᴀs Bᴇᴇɴ Sᴜᴄᴇssғᴜʟʟʏ Sᴇɴᴅ To {user.mention}.</b>")
        else:
            await message.reply_text("<b>Aɴ Eʀʀᴏʀ Oᴄᴄᴜʀʀᴇᴅ !</b>")
    else:
        await message.reply_text("<b>Cᴏᴍᴍᴀɴᴅ Iɴᴄᴏᴍᴘʟᴇᴛᴇ...</b>")

@Client.on_message(filters.command("gsend") & filters.user(ADMINS))
async def send_chatmsg(bot, message):
    if message.reply_to_message:
        target_id = message.text
        command = ["/gsend"]
        for cmd in command:
            if cmd in target_id:
                target_id = target_id.replace(cmd, "")
        success = False
        try:
            chat = await bot.get_chat(int(target_id))
            await message.reply_to_message.copy(int(chat.id))
            success = True
        except Exception as e:
            await message.reply_text(f"<b>Eʀʀᴏʀ :- <code>{e}</code></b>")
        if success:
            await message.reply_text(f"<b>Yᴏᴜʀ Mᴇssᴀɢᴇ Hᴀs Bᴇᴇɴ Sᴜᴄᴇssғᴜʟʟʏ Sᴇɴᴅ To {chat.id}.</b>")
        else:
            await message.reply_text("<b>Aɴ Eʀʀᴏʀ Oᴄᴄᴜʀʀᴇᴅ !</b>")
    else:
        await message.reply_text("<b>Cᴏᴍᴍᴀɴᴅ Iɴᴄᴏᴍᴘʟᴇᴛᴇ...</b>")







