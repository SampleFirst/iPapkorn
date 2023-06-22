import os
import requests
import wget
from pyrogram import Client, filters


def get_text(message):
    if message.reply_to_message and message.reply_to_message.text:
        return message.reply_to_message.text
    elif len(message.command) > 1:
        return message.text.split(None, 1)[1]
    else:
        return ''


@Client.on_message(filters.command(["reels", "insta"]) & filters.private)
async def download_reels(_, message):
    user_id = message.from_user.id
    user_name = message.from_user.first_name
    rpk = "[" + user_name + "](tg://user?id=" + str(user_id) + ")"
    link = get_text(message)
    m = await message.reply(f"**Downloading content from {link}**")
    try:
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0;Win64) AppleWebkit/537.36 (KHTML, like Gecko) Chrome/89.0.4389.82 Safari/537.36',
            'Accept-Language': 'en-US,en;q=0.5',
            'Referer': 'https://www.instagram.com/',
        }
        response = requests.get(link, headers=headers)
        if response.status_code == 200:
            content = response.text
            video_url = ''
            image_url = ''
            if 'video_url' in content:
                video_url = content.split('video_url": "')[1].split('"')[0]
            if 'display_url' in content:
                image_url = content.split('display_url": "')[1].split('"')[0]
            if video_url and link.startswith('https://www.instagram.com/reel/'):
                video_file = wget.download(video_url)
                await app.send_video(
                    chat_id=message.chat.id,
                    video=video_file,
                    caption=f"**Reels downloaded from {link}**",
                    quote=False,
                    supports_streaming=True
                )
                os.remove(video_file)
                await m.delete()
            elif image_url and link.startswith('https://www.instagram.com/p/'):
                image_file = wget.download(image_url)
                await app.send_photo(
                    chat_id=message.chat.id,
                    photo=image_file,
                    caption=f"**Instagram photo downloaded from {link}**",
                    quote=False
                )
                os.remove(image_file)
                await m.delete()
            else:
                await m.edit("Unable to find content in the provided link.")
        else:
            await m.edit("Invalid link or unable to access the provided URL.")
    except Exception as e:
        await m.edit(f"An error occurred while downloading content: {str(e)}")


