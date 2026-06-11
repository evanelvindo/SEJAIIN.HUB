import logging
from telegram import Update
from telegram.ext import ContextTypes, ConversationHandler
from config import GROUP_ID, TOPIC_REPORT, TOPIC_REKOMENDASI

# Setup logging
logging.basicConfig(level=logging.ERROR, format='%(asctime)s - %(message)s')

# State untuk percakapan
REPORT, RECOM = range(2)

# --- REFRESH ---
async def refresh_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Menampilkan kembali menu utama. Mengarahkan user kembali ke fungsi start
    untuk memuat ulang keyboard menu sesuai role mereka.
    """
    from handlers.conversation import start
    await start(update, context) 

# --- LAPORAN MASALAH ---
async def report_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Memulai alur penginputan laporan masalah."""
    # Memberikan instruksi yang jelas agar user tidak bingung
    await update.message.reply_text(
        "📝 **Pusat Laporan Masalah**\n"
        "━━━━━━━━━━━━━━━━━━━━\n"
        "Silakan tuliskan keluhan atau masalah yang Anda alami secara detail.\n\n"
        " Contoh: _'Pembayaran saya belum diverifikasi meskipun sudah kirim bukti.'_\n\n"
        "Ketik /cancel untuk membatalkan."
    )
    return REPORT

async def report_finish(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Mengirim isi laporan ke grup admin dan mengakhiri state."""
    user = update.effective_user
    isi_laporan = update.message.text
    
    # Kirim ke grup admin (Topic Laporan)
    try:
        await context.bot.send_message(
            chat_id=GROUP_ID, 
            message_thread_id=TOPIC_REPORT,
            text=(
                f"⚠️ **LAPORAN MASALAH BARU**\n"
                f"━━━━━━━━━━━━━━━━━━━━\n"
                f"👤 **Dari:** {user.full_name} (@{user.username})\n"
                f"🆔 **ID:** `{user.id}`\n"
                f"📝 **Pesan:**\n\n{isi_laporan}"
            ),
            parse_mode='Markdown'
        )
        await update.message.reply_text("✅ **Laporan Terkirim.**\n\nAdmin akan segera meninjau laporan Anda. Terima kasih atas laporannya!")
    except Exception as e:
        logging.error(f"Gagal mengirim laporan dari {user.id}: {e}")
        await update.message.reply_text("❌ **Gagal mengirim laporan.**\nSilakan coba lagi nanti atau hubungi admin langsung.")
        
    return ConversationHandler.END

# --- REKOMENDASI JASA ---
async def recom_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Memulai alur penginputan rekomendasi jasa baru."""
    await update.message.reply_text(
        "💡 **Saran & Rekomendasi Jasa**\n"
        "━━━━━━━━━━━━━━━━━━━━\n"
        "Punya ide jasa baru yang dibutuhkan mahasiswa? Tuliskan ide Anda di sini!\n\n"
        "Ketik /cancel untuk membatalkan."
    )
    return RECOM

async def recom_finish(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Mengirim isi rekomendasi ke grup admin dan mengakhiri state."""
    user = update.effective_user
    isi_rekom = update.message.text
    
    # Kirim ke grup admin (Topic Rekomendasi)
    try:
        await context.bot.send_message(
            chat_id=GROUP_ID, 
            message_thread_id=TOPIC_REKOMENDASI,
            text=(
                f"💡 **REKOMENDASI JASA BARU**\n"
                f"━━━━━━━━━━━━━━━━━━━━\n"
                f"👤 **Dari:** {user.full_name} (@{user.username})\n"
                f"🆔 **ID:** `{user.id}`\n"
                f"📝 **Rekomendasi:**\n\n{isi_rekom}"
            ),
            parse_mode='Markdown'
        )
        await update.message.reply_text("✅ **Saran Diterima.**\n\nTerima kasih! Rekomendasi Anda sangat berharga bagi pengembangan Sejaiin ke depan.")
    except Exception as e:
        logging.error(f"Gagal mengirim rekomendasi dari {user.id}: {e}")
        await update.message.reply_text("❌ Gagal mengirim rekomendasi.")

    return ConversationHandler.END