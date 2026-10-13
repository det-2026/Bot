import sqlite3
import string
import random
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes

# Apna Telegram Bot Token yahan daalein
TOKEN = "8500116657:AAH8jJWprCxZw4Rbft5iy9yBUQ3VXNVbFPA"
ADMIN_ID = 8270379920  # Apna Telegram User ID yahan daalein (admin ke liye)

# Database Setup
def init_db():
    conn = sqlite3.connect('files_bot.db')
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS files (
            id TEXT PRIMARY KEY,
            file_id TEXT,
            file_type TEXT,
            caption TEXT
        )
    ''')
    conn.commit()
    conn.close()

init_db()

# Random Unique Code Generator (jaise: aBc12X)
def generate_code(length=6):
    characters = string.ascii_letters + string.digits
    return ''.join(random.choice(characters) for _ in range(length))

# 1. /start Command Handler
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    args = context.args
    if args:
        # Agar user kisi special link se aaya hai (jaise: /start abC12X)
        file_code = args[0]
        
        conn = sqlite3.connect('files_bot.db')
        cursor = conn.cursor()
        cursor.execute('SELECT file_id, file_type, caption FROM files WHERE id = ?', (file_code,))
        row = cursor.fetchone()
        conn.close()
        
        if row:
            file_id, file_type, caption = row
            caption_text = caption if caption else ""
            
            # File type ke hisaab se send karein
            if file_type == 'document':
                await update.message.document.send(file_id, caption=caption_text)
            elif file_type == 'photo':
                await update.message.photo.send(file_id, caption=caption_text)
            elif file_type == 'video':
                await update.message.video.send(file_id, caption=caption_text)
            elif file_type == 'audio':
                await update.message.audio.send(file_id, caption=caption_text)
        else:
            await update.message.reply_text("❌ Yeh file link invalid hai ya expired ho chuki hai.")
    else:
        await update.message.reply_text("👋 Welcome! File access karne ke liye diye gaye special link ka use karein.")

# 2. Admin ke liye File save karke Special Link banane ka tarika
async def handle_file(update: Update, context: ContextTypes.DEFAULT_TYPE):
    # Check karein ki message bhejne wala admin hi hai
    if update.effective_user.id != ADMIN_ID:
        await update.message.reply_text("⚠️ Aapko yeh file upload karne ki permission nahi hai.")
        return

    message = update.message
    file_id = None
    file_type = None
    caption = message.caption or ""

    # Detect file type
    if message.document:
        file_id = message.document.file_id
        file_type = 'document'
    elif message.photo:
        file_id = message.photo[-1].file_id  # Highest resolution photo
        file_type = 'photo'
    elif message.video:
        file_id = message.video.file_id
        file_type = 'video'
    elif message.audio:
        file_id = message.audio.file_id
        file_type = 'audio'

    if file_id:
        # Unique code generate karein
        code = generate_code()
        
        # Database me save karein
        conn = sqlite3.connect('files_bot.db')
        cursor = conn.cursor()
        cursor.execute('INSERT INTO files (id, file_id, file_type, caption) VALUES (?, ?, ?, ?)',
                       (code, file_id, file_type, caption))
        conn.commit()
        conn.close()

        # Bot ka username nikalein
        bot_username = context.bot.username
        special_link = f"https://t.me/{bot_username}?start={code}"

        await update.message.reply_text(
            f"✅ **File Successfully Stored!**\n\n"
            f"🔗 **Special Link:**\n`{special_link}`",
            parse_mode="Markdown"
        )
    else:
        await update.message.reply_text("❌ Please koi valid file (Document, Photo, Video, Audio) bhejein.")

def main():
    # Application initialize karein
    app = Application.builder().token(TOKEN).build()

    # Handlers add karein
    app.add_handler(CommandHandler("start", start))
    
    # Admin jab bhi koi file bhejega, yeh handler use catch karega
    file_filter = filters.DOCUMENT | filters.PHOTO | filters.VIDEO | filters.AUDIO
    app.add_handler(MessageHandler(file_filter & ~filters.COMMAND, handle_file))

    print("🤖 Bot is running...")
    app.run_polling()

if __name__ == '__main__':
    main()
  
