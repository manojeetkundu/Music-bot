import os
import threading
from http.server import BaseHTTPRequestHandler, HTTPServer
import requests
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, filters, ContextTypes

TELEGRAM_TOKEN = os.environ.get("TELEGRAM_TOKEN")
JAMENDO_CLIENT_ID = os.environ.get("JAMENDO_CLIENT_ID")

class HealthCheckHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.end_headers()
        self.wfile.write(b"Bot is running!")

def run_dummy_server():
    port = int(os.environ.get("PORT", 8080))
    server = HTTPServer(("0.0.0.0", port), HealthCheckHandler)
    server.serve_forever()

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    welcome_text = "🎧 *Namaste! Music & Lyrics Bot mein aapka swagat hai!* ✨\n\n🎶 *1. Free MP3 Tracks:*\nKisi bhi mood ya genre ka naam bhejein (jaise `piano`, `lofi`, `rock`).\n\n📜 *2. Song Lyrics:*\nLikhein: `/lyrics Artist - Song Name`\n👉 *Example:* `/lyrics Coldplay - Yellow`"
    await update.message.reply_text(welcome_text, parse_mode="Markdown")

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
            caption_text = f"🎵 *Track:* {title}\n🎤 *Artist:* {artist}\n✨ _Powered by Jamendo_"
            await update.message.reply_audio(audio=audio_url, title=title, performer=artist, caption=caption_text, parse_mode="Markdown")
        else:
            await status_msg.edit_text("⚠️ Is track ki audio file abhi available nahi hai.")
    except Exception as e:
        await status_msg.edit_text("🚨 Oops! Music search karte waqt koi technical error aa gaya.")
        print(f"Music Error: {e}")

async def get_lyrics(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_input = " ".join(context.args)
    if "-" not in user_input:
        await update.message.reply_text("🤔 *Format thoda galat hai!*\n\nAise likhein: `/lyrics Artist - Song Name`\n💡 *Example:* `/lyrics Ed Sheeran - Perfect`", parse_mode="Markdown")
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
                    lyrics = lyrics[:3900] + "\n\n✂️ _... (Lyrics cut due to length)_"
                await status_msg.delete()
                msg_text = f"🎼 *{title.upper()}*\n👤 _by {artist}_\n━━━━━━━━━━━━━━━━━━\n\n{lyrics}"
                await update.message.reply_text(msg_text, parse_mode="Markdown")
            else:
                await status_msg.edit_text("😕 Is gaane ke lyrics database mein nahi mile.")
        else:
            await status_msg.edit_text("❌ Lyrics nahi mile! Artist ya song ki spelling check karke dobara try karein.")
    except Exception as e:
        await status_msg.edit_text("🔌 Lyrics server se connect nahi ho pa raha. Thodi der baad try karein!")
        print(f"Lyrics Error: {e}")

if __name__ == "__main__":
    threading.Thread(target=run_dummy_server, daemon=True).start()
    app = ApplicationBuilder().token(TELEGRAM_TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("lyrics", get_lyrics))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, search_music))
    print("🤖 Bot live hai! 🎶")
    app.run_polling()
