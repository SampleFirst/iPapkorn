from pyrogram import Client, filters
from database.ia_filterdb import Media
from pyrogram.types import InlineKeyboardButton, InlineKeyboardMarkup
import re
from info import CHANNELS, ADMINS

# Initialize the Telegram bot
bot = Client("my_bot")

@Client.on_message(filters.command('findfiles') & filters.user(ADMINS))
async def find_files(bot, message):
    """Find files in the database based on search criteria"""
    search_query = " ".join(message.command[1:])  # Extract the search query from the command

    # Build the MongoDB query to search for files
    query = {
        'file_name': {"$regex": f".*{re.escape(search_query)}.*", "$options": "i"}
    }

    # Fetch the matching files from the database
    results = await Media.collection.find(query).to_list(length=None)

    if results:
        result_message = f'{len(results)} files found matching the search query "{search_query}" in the database:\n\n'
        for result in results:
            result_message += f'File ID: {result["_id"]}\n'
            result_message += f'File Name: {result["file_name"]}\n'
            result_message += f'File Size: {result["file_size"]}\n\n'
    else:
        result_message = f'No files found matching the search query "{search_query}" in the database'

    await message.reply_text(result_message, quote=True)

@Client.on_message(filters.command('deletename') & filters.user(ADMINS))
async def delete_name(bot, message):
    """Delete files with a specific name from the database"""
    file_name = " ".join(message.command[1:])  # Extract the file name from the command

    result = await Media.collection.count_documents({
        'file_name': {"$regex": f".*{re.escape(file_name)}.*", "$options": "i"}
    })

    if result > 0:
        confirmation_message = f'{result} files found with the name "{file_name}" in the database.\n'
        confirmation_message += 'Are you sure you want to delete them?'

        keyboard = InlineKeyboardMarkup(
            [
                [
                    InlineKeyboardButton(
                        text="YES", callback_data=f"delete_files:{file_name}"
                    )
                ],
                [
                    InlineKeyboardButton(
                        text="CANCEL", callback_data="cancel_delete"
                    )
                ],
            ]
        )

        await message.reply_text(confirmation_message, quote=True, reply_markup=keyboard)
    else:
        await message.reply_text(f'No files found with the name "{file_name}" in the database', quote=True)

@bot.on_callback_query(filters.regex(r'^delete_files:(.*)'))
async def delete_name_confirm(bot, callback_query):
    file_name = callback_query.matches[0].group(1)

    result = await Media.collection.delete_many({
        'file_name': {"$regex": f".*{re.escape(file_name)}.*", "$options": "i"}
    })

    if result.deleted_count:
        await callback_query.answer(text=f'Successfully deleted all related files with names "{file_name}" from the database')
        await callback_query.message.edit_text("Files deleted.")
    else:
        await callback_query.answer(text=f'No files found with the name "{file_name}" in the database')
        await callback_query.message.edit_text("Deletion failed.")

# Other command handlers and functions can be added here
