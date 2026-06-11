import logging
from telegram import Update
from telegram.ext import ContextTypes
from handlers.admin.dashboard import is_admin
from database.services import update_service_price

# Setup logging
logging.basicConfig(level=logging.ERROR, format='%(asctime)s - %(message)s')

async def edit_harga_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Handler untuk perintah /edit_harga [ID] [HARGA].
    Memungkinkan admin mengubah harga layanan secara instan melalui chat.
    """
    user_id = update.effective_user.id

    # 1. Validasi Keamanan: Cek apakah user adalah Admin
    if not is_admin(user_id):
        logging.warning(f"Akses ditolak: User {user_id} mencoba menggunakan /edit_harga.")
        return

    # 2. Validasi Input Argumen
    args = context.args
    if len(args) != 2:
        await update.message.reply_text(
            "⚠️ **Format Salah!**\n\n"
            "Gunakan format: `/edit_harga [ID_Layanan] [Harga_Baru]`\n"
            "Contoh: `/edit_harga 1 75000`",
            parse_mode='Markdown'
        )
        return
    
    id_layanan = args[0]
    harga_raw = args[1]

    # 3. Validasi Tipe Data
    if not harga_raw.isdigit():
        await update.message.reply_text("⚠️ **Error:** Harga harus berupa angka tanpa titik atau koma (Contoh: 50000).")
        return
    
    try:
        new_price = float(harga_raw)
        service_id = int(id_layanan)
    except ValueError:
        await update.message.reply_text("⚠️ **Error:** ID dan Harga harus berupa angka valid.")
        return

    # 4. Eksekusi Update melalui Database Layer
    # Menggunakan fungsi yang sudah ada di database/services.py agar konsisten
    success = update_service_price(service_id, new_price)

    if success:
        await update.message.reply_text(
            f"✅ **Update Berhasil!**\n\n"
            f"🆔 ID Layanan: `{service_id}`\n"
            f"💰 Harga Baru: **Rp{new_price:,.0f}**",
            parse_mode='Markdown'
        )
    else:
        await update.message.reply_text(
            "⚠️ **Gagal Update!**\n"
            "ID Layanan tidak ditemukan di database. Cek daftar ID di Dashboard Admin.",
            parse_mode='Markdown'
        )