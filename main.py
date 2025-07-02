import os
import subprocess
from pyrogram import Client, filters
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton, Message

# 🔐 Load credentials from environment (set these in Render’s Dashboard)
API_ID   = int(os.environ["API_ID"])
API_HASH = os.environ["API_HASH"]
BOT_TOKEN = os.environ["BOT_TOKEN"]

bot = Client("yt_quality_bot", api_id=API_ID, api_hash=API_HASH, bot_token=BOT_TOKEN)

@bot.on_message(filters.private & filters.command("start"))
async def start(client, message):
    await message.reply("👋 Send me any YouTube or live link, and I'll let you choose quality to download.")

@bot.on_message(filters.private & filters.text & ~filters.command("start"))
async def get_formats(client, message: Message):
    url = message.text.strip()
    if "youtube.com" not in url and "youtu.be" not in url:
        return await message.reply("❌ Invalid YouTube link.")

    status = await message.reply("🔍 Fetching available formats…")
    try:
        # List formats
        proc = subprocess.run(
            ["yt-dlp", "-F", url],
            stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True
        )
        output = proc.stdout
        # Parse only video formats with code
        lines = [
            l for l in output.splitlines()
            if l[:3].strip().isdigit() and "video only" not in l and "audio only" not in l
        ]

        # Build buttons (limit to first 10)
        buttons = []
        for line in lines[:10]:
            parts = line.split()
            code = parts[0]
            label = " ".join(parts[1:])
            buttons.append([InlineKeyboardButton(label, callback_data=f"{code}|{url}")])

        await status.edit_text("🎞 Select the quality:", reply_markup=InlineKeyboardMarkup(buttons))

    except Exception as e:
        await status.edit_text(f"❌ Failed to fetch formats:\n{e}")

@bot.on_callback_query()
async def download_choice(client, callback_query):
    data = callback_query.data
    if "|" not in data:
        return await callback_query.answer("Invalid selection.")

    fmt, url = data.split("|", 1)
    msg = await callback_query.message.edit_text(f"⏬ Downloading in `{fmt}`…")
    out_file = f"video_{fmt}.mp4"

    try:
        subprocess.run(
            ["yt-dlp", "-f", fmt, "-o", out_file, url],
            check=True
        )
        await msg.reply_video(out_file, caption=f"✅ Downloaded in `{fmt}`")
        os.remove(out_file)
    except Exception as e:
        await msg.edit_text(f"❌ Download failed:\n{e}")

bot.run()
