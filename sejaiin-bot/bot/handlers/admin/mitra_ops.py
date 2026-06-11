import logging
import re
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes
# Import fungsi database sesuai struktur proyek Anda
from database.mitra import approve_mitra, get_mitra_by_id, get_db_connection

# Setup logging
logger = logging.getLogger(__name__)

def escape_markdown(text):
    """
    Menghapus atau melarikan karakter khusus Markdown agar tidak menyebabkan error
    'Can't parse entities'. Sangat penting untuk username yang mengandung underscore.
    """
    if not text:
        return ""
    # Karakter yang diproses oleh parse_mode='Markdown'
    parse_chars = r"_*`["
    return re.sub(f"([{re.escape(parse_chars)}])", r"\\\1", str(text))

def reject_mitra(mitra_id):
    """Mengubah status verifikasi mitra menjadi DITOLAK di database."""
    conn = get_db_connection()
    if not conn:
        logger.error("Gagal koneksi database di reject_mitra")
        return False
    try:
        cursor = conn.cursor()
        cursor.execute(
            "UPDATE mitra SET status_verifikasi = 'DITOLAK' WHERE id = %s", 
            (mitra_id,)
        )
        conn.commit()
        return cursor.rowcount > 0
    except Exception as e:
        logger.error(f"DB Error saat reject: {e}")
        return False
    finally:
        if 'cursor' in locals(): cursor.close()
        if conn: conn.close()

async def admin_mitra_detail_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Menampilkan detail lengkap mitra sebelum keputusan.
    """
    query = update.callback_query
    await query.answer()

    try:
        data_parts = query.data.split('_')
        mitra_id = int(data_parts[2])
        mitra = get_mitra_by_id(mitra_id)
        
        if not mitra:
            await query.edit_message_text("❌ Data mitra tidak ditemukan.")
            return

        # Ambil data peminatan, jika tidak ada di DB tampilkan Software Engineering sebagai default
        spesialisasi = mitra.get('peminatan') or mitra.get('bidang') or "Software Engineering"

        # Gunakan backtick (`) untuk NIK agar bisa di-copy dengan sekali klik
        text = (
            f"📋 **DETAIL CALON MITRA**\n"
            f"━━━━━━━━━━━━━━━━━━━━\n"
            f"👤 **Nama:** {escape_markdown(mitra.get('nama_lengkap'))}\n"
            f"🆔 **NIK:** `{mitra.get('nik', '-')}`\n"
            f"📱 **WhatsApp:** {escape_markdown(mitra.get('no_whatsapp'))}\n"
            f"🏦 **No. Rekening:** {escape_markdown(mitra.get('no_rekening', '-'))}\n"
            f"🛠 **Spesialisasi:** {escape_markdown(spesialisasi)}\n"
            f"━━━━━━━━━━━━━━━━━━━━\n"
            f"Silakan tentukan verifikasi untuk mitra ini:"
        )

        keyboard = InlineKeyboardMarkup([
            [
                InlineKeyboardButton("✅ Setujui", callback_data=f"acc_mitra_{mitra_id}"),
                InlineKeyboardButton("❌ Tolak", callback_data=f"dec_mitra_{mitra_id}")
            ],
            [InlineKeyboardButton("⬅️ Kembali ke Daftar", callback_data="admin_mitra")]
        ])
        
        await query.edit_message_text(text, reply_markup=keyboard, parse_mode='Markdown')
        
    except Exception as e:
        logger.error(f"Error detail handler: {e}")
        await query.edit_message_text(f"❌ Terjadi kesalahan teknis: {escape_markdown(str(e))}")

async def admin_mitra_decision_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Memproses aksi Setujui/Tolak.
    """
    query = update.callback_query
    await query.answer()
    
    try:
        data_parts = query.data.split('_')
        action = data_parts[0]    # 'acc' atau 'dec'
        target_db_id = int(data_parts[2]) 
    except (IndexError, ValueError):
        return

    mitra_data = get_mitra_by_id(target_db_id)
    if not mitra_data:
        await query.edit_message_text("❌ Data sudah tidak tersedia di database.")
        return

    tele_id = mitra_data.get('telegram_id_mitra')
    nama = mitra_data.get('nama_lengkap', 'Mitra')
    
    # Ambil identitas admin dan amankan dengan escape_markdown
    admin_name = update.effective_user.username or update.effective_user.first_name
    safe_admin = escape_markdown(admin_name)
    safe_nama = escape_markdown(nama)

    if action == "acc":
        if approve_mitra(target_db_id):
            await query.edit_message_text(
                f"✅ **MITRA DISETUJUI**\n\n"
                f"👤 Nama: {safe_nama}\n"
                f"👮 Admin: @{safe_admin}",
                parse_mode='Markdown'
            )
            # Notif ke Mitra
            try:
                await context.bot.send_message(
                    chat_id=tele_id,
                    text=f"🎉 Selamat {safe_nama}!\nPendaftaran Anda di **Sejaiin Hub** telah disetujui. Silakan gunakan /start.",
                    parse_mode='Markdown'
                )
            except Exception as e:
                logger.warning(f"Gagal mengirim notif persetujuan ke mitra: {e}")
        else:
            await query.edit_message_text("⚠️ Gagal memperbarui status di database.")

    elif action == "dec":
        if reject_mitra(target_db_id):
            await query.edit_message_text(
                f"❌ **PENDAFTARAN DITOLAK**\n\n"
                f"👤 Nama: {safe_nama}\n"
                f"👮 Admin: @{safe_admin}",
                parse_mode='Markdown'
            )
            # Notif ke Mitra
            try:
                await context.bot.send_message(
                    chat_id=tele_id,
                    text=f"⚠️ Mohon maaf {safe_nama}, pendaftaran Anda di Sejaiin Hub belum dapat kami setujui saat ini."
                )
            except Exception as e:
                logger.warning(f"Gagal mengirim notif penolakan ke mitra: {e}")

# ==========================================================
# EXPORT HANDLER (Sesuai main.py)
# ==========================================================
admin_mitra_detail_handler = admin_mitra_detail_handler
admin_mitra_decision_handler = admin_mitra_decision_handler

# Menambahkan alias approve_mitra_handler agar tidak error saat dipanggil __init__.py
approve_mitra_handler = admin_mitra_decision_handler