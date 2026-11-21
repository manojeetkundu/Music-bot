import os
import threading
from http.server import BaseHTTPRequestHandler, HTTPServer
import requests
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, filters, ContextTypes

# 🔑 Render ke Environment Variables se tokens lena
TELEGRAM_TOKEN = os.environ.get("TELEGRAM_TOKEN")
JAMENDO_CLIENT_ID = os.environ.get("JAMENDO_CLIENT_ID")

# 🌐 Render Free Web Service ko zinda rakhne ke liye dummy server
class HealthCheckHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.end_headers()
        self.wfile.write(b"Bot is running!")

def run_dummy_server():
    port = int(os.environ.get("PORT", 8080))
    server = HTTPServer(("0.0.0.0", port), HealthCheckHandler)
    server.serve_forever()

# 👋 Welcome Message
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    welcome_text = (
        "🎧 *Namaste! Music & Lyrics Bot mein aapka swagat hai!* ✨\n\n"
        "Main aapke liye do cool kaam kar sakta hoon:\n\n"
        "🎶 *1. Free MP3 Tracks:*\n"
        "Bas kisi bhi mood ya genre ka naam bhejein (jaise `piano`, `lofi`, `rock`) aur main copyright-free MP3 bhejunga.\n\n"
        "📜 *2. Song Lyrics:*\n"
        "Kisi bhi gaane ke lyrics ke liye likhein:\n"
        "`/lyrics Artist - Song Name`\n"
        "👉 *Example:* `/lyrics Coldplay - Yellow`"
    )
    await update.message.reply_text(welcome_text, parse_mode="Markdown")

# 🎵 Feature 1: Jamendo se MP3 Search karna
async def search_music(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.message.text
    status_msg = await update.message.reply_text(f"🔍 *'{query}'* ke liye mast track dhoondh raha hoon... 🎧", parse_mode="Markdown")

    url = "https://api.jamendo.com/v3.0/tracks/"
    params = {
        "client_id": JAMENDO_CLIENT_ID,
        "format": "json",
        "limit": 1,
        "search": query,
        "audioformat": "mp32"
    }

    try:
        response = requests.get(url, params=params).json()
        results = response.get("results", [])

        if not results:
            await status_msg.edit_text("😕 Is naam se koi free track nahi mila. Koi doosra keyword try karein!")
            return

        track = results[0]
        title = track.get("name")
        artist = track.get("artist_name")
        audio_url = track.get("audio")

        if audio_url:
            await status_msg.delete()
            await update.message.reply_audio(
                audio=audio_url,
                title=title,
                performer=artist,
                caption=(
                    f"🎵 *Track:* {title}\n"
                    f"🎤 *Artist:* {artist}\n"
                    f"✨ _Powered by Jamendo Creative Commons_"
                ),
                parse_mode="Markdown"
            )
        else:
            await status_msg.edit_text("⚠️ Is track ki audio file abhi available nahi hai.")

    except Exception as e:
        await status_msg.edit_text("🚨 Oops! Music search karte waqt koi technical error aa gaya.")
        print(f"Music Error: {e}")

# 📜 Feature 2: Lyrics.ovh API se Lyrics fetch karna
async def get_lyrics(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_input = " ".join(context.args)

    if "-" not in user_input:
        await update.message.reply_text(
            "🤔 *Format thoda galat hai!*\n\n"
            "Aise likhein: `/lyrics Artist - Song Name`\n"
            "💡 *Example:* `/lyrics Ed Sheeran - Perfect`",
            parse_mode="Markdown"
        )
        return

    artist, title = [part.strip() for part in user_input.split("-", 1)]
    status_msg = await update.message.reply_text(f"✍️ *{title}* ke lyrics likh raha hoon... ⏳", parse_mode="Markdown")

    url = f"https://api.lyrics.ovh/v1/{artist}/{title}"

    try:
        response = requests.get(url, timeout=10)
        if response.status_code == 200:
            data = response.json()
            lyrics = data.get("lyrics")

            if lyrics:
                if len(lyrics) > 3900:
                    lyrics = lyrics[:3900] + "\n\n✂️ _... (Lyrics zyada lambe hone ki wajah se cut kiye gaye)_"
                
                await status_msg.delete()
                await update.message.reply_text(
                    f"🎼 *{title.upper()}*\n"
                    f"👤 _by {artist}_\n"
                    f"━━━━━━━━━━━━━━━━━━\n\n"
                    f"{lyrics}",
                    parse_mode="Markdown"
                )
            else:
                await status_msg.edit_text("😕 Is gaane ke lyrics database mein nahi mile.")
        else:
            await status_msg.edit_text("❌ Lyrics nahi mile! Artist ya song ki spelling. ") 
