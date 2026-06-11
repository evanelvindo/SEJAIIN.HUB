import logging
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes
from config import GROUP_ID, TOPIC_SUBMISSION 
from database.orders import save_bukti_kerja, get_order_details
from database.mitra import get_mitra_by_telegram_id

# Setup logging
logging.basicConfig(level=logging.ERROR, format='%(asctime)s - %(message)s')

async def worker_send_bukti(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Handler untuk menerima foto bukti kerja dari Mitra dan mengirimnya ke Admin
    di topik verifikasi khusus (TOPIC_SUBMISSION).
    """
    # 1. Validasi: Pastikan yang dikirim adalah foto
    if not update.message.photo:
        # Kita abaikan jika pesan bukan foto agar tidak mengganggu chat lain
        return

    # 2. Validasi: Pastikan ada order_id di context
    # Ini diambil dari saat mitra menekan tombol 'Ambil Order'
    order_id = context.user_data.get('active_order_id')
    
    if not order_id:
        await update.message.reply_text(
            "⚠️ **Tidak Ada Order Aktif**\n\n"
            "Sistem tidak mendeteksi order yang sedang Anda kerjakan. "
            "Pastikan Anda sudah menekan tombol 'Ambil Pekerjaan' sebelum mengirimkan bukti."
        )
        return

    # 3. Ambil data pendukung
    order = get_order_details(order_id)
    mitra = get_mitra_by_telegram_id(update.effective_user.id)
    
    if not order:
        await update.message.reply_text("❌ Data order tidak ditemukan di sistem database.")
        return

    # 4. Ambil file_id foto (kualitas tertinggi)
    photo_file = update.message.photo[-1].file_id
    
    # 5. Simpan ke database
    try:
        # Pastikan fungsi ini mengupdate status order menjadi 'MENUNGGU_VERIFIKASI' atau sejenisnya
        save_bukti_kerja(order_id, photo_file)
    except Exception as e:
        logging.error(f"Gagal simpan bukti kerja Order #{order_id}: {e}")
        await update.message.reply_text(f"❌ Gagal menyimpan bukti ke database: {e}")
        return

    mitra_nama = mitra['nama_lengkap'] if mitra else update.effective_user.full_name
    user_id_pelanggan = order.get('telegram_id_pengguna')
    mitra_id = update.effective_user.id
    
    # 6. Tombol verifikasi untuk Admin
    kb_admin = [
        [
            InlineKeyboardButton("✅ Setujui", callback_data=f"verify_proof_{order_id}"),
            InlineKeyboardButton("❌ Tolak", callback_data=f"reject_proof_{order_id}")
        ],
        [
            # Link chat langsung menggunakan protocol tg://user?id= (Gambar 4)
            InlineKeyboardButton("💬 Chat Mitra", url=f"tg://user?id={mitra_id}"),
            InlineKeyboardButton("👤 Chat Pelanggan", url=f"tg://user?id={user_id_pelanggan}")
        ]
    ]
    
    # 7. Kirim ke Grup Admin di Topik SUBMISSION
    try:
        await context.bot.send_photo(
            chat_id=GROUP_ID, 
            message_thread_id=TOPIC_SUBMISSION,
            photo=photo_file,
            caption=(
                f"📸 **VERIFIKASI BUKTI KERJA**\n"
                f"━━━━━━━━━━━━━━━━━━━━\n"
                f"🆔 **Order ID:** `#{order_id}`\n"
                f"👤 **Mitra:** {mitra_nama}\n"
                f"📞 **Customer ID:** `{user_id_pelanggan}`\n"
                f"━━━━━━━━━━━━━━━━━━━━\n"
                f"Admin, silakan periksa bukti kerja di atas. Gunakan tombol di bawah untuk komunikasi atau konfirmasi penyelesaian."
            ),
            reply_markup=InlineKeyboardMarkup(kb_admin),
            parse_mode='Markdown'
        )
        
        # 8. Feedback ke Mitra & Bersihkan State
        await update.message.reply_text(
            "✅ **Bukti kerja berhasil terkirim!**\n\n"
            "Admin akan melakukan verifikasi. Anda akan menerima notifikasi jika pekerjaan ini telah disetujui (Selesai). "
            "Terima kasih atas kerja kerasnya!"
        )
        
        # Opsional: Jangan clear context dulu jika Anda ingin mitra bisa kirim >1 foto
        # context.user_data.pop('active_order_id', None)

    except Exception as e:
        logging.error(f"Error mengirim submission ke admin: {e}")
        await update.message.reply_text("❌ Gagal mengirim bukti ke Admin. Silakan coba kirim ulang foto.")