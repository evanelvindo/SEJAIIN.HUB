import logging
from telegram import (
    InlineKeyboardButton, 
    InlineKeyboardMarkup, 
    ReplyKeyboardMarkup, 
    ReplyKeyboardRemove, 
    KeyboardButton, 
    Update
)
from telegram.ext import ContextTypes, ConversationHandler, MessageHandler, filters

# Import database dan konfigurasi
from database.orders import create_order
from utils import get_address_from_coords
from config import (
    PAYMENT_INFO, 
    GROUP_ID, 
    TOPIC_SERVICES, 
    TOPIC_FINANCE, 
    ADMIN_ID
)
from handlers.admin.dashboard import admin_menu_handler

# Import konstanta lokal
from handlers.conversation.states import (
    SERVICE, 
    ASK_LOCATION, 
    WAITING_LOCATION, 
    WAITING_CONTACT, 
    WAITING_PHOTO,
    WAITING_TITIPIAN
)
from handlers.conversation.data import LAYANAN

# Setup logging
logging.basicConfig(level=logging.ERROR, format='%(asctime)s - %(message)s')

# --- Helper Admin ---
async def handle_admin_button(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Mengarahkan admin langsung ke dashboard admin."""
    await admin_menu_handler(update, context)
    return ConversationHandler.END


# --- HANDLER BARU UNTUK MENU TAMBAHAN ---

async def daftar_mitra_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Menampilkan informasi pendaftaran mitra dan link form registrasi."""
    # Teks informasi disesuaikan dengan alur karir teknisi kosan/mahasiswa
    teks_mitra = (
        "🤝 **Gabung Menjadi Mitra Sejaiin**\n\n"
        "Punya keahlian di bidang servis AC, kelistrikan, saluran air, atau kebersihan? "
        "Mari bergabung menjadi bagian dari teknisi andalan Sejaiin Hub!\n\n"
        "📌 **Keuntungan:**\n"
        "• Jam kerja fleksibel (cocok untuk mahasiswa/freelancer).\n"
        "• Pendapatan transparan per orderan.\n"
        "• Komunitas teknisi yang solid.\n\n"
        "📋 **Formulir Pendaftaran:**\n"
        "Silakan isi formulir registrasi mitra melalui tautan di bawah ini:\n"
        "[Klik di Sini untuk Mengisi Form Registrasi](https://sejaiin.com/registrasi-mitra)\n\n"
        "_Tim kami akan melakukan verifikasi berkas dan menghubungi Anda via WhatsApp._"
    )
    
    # Menambahkan tombol inline agar user tinggal klik langsung menuju form web
    keyboard = [[InlineKeyboardButton("📝 Isi Form Registrasi Web", url="https://sejaiin.com/registrasi-mitra")]]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await update.message.reply_text(teks_mitra, reply_markup=reply_markup, parse_mode='Markdown', disable_web_page_preview=False)
    return ConversationHandler.END

async def informasi_sejaiin_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Menampilkan profil singkat aplikasi dan mengarahkan ke dashboard utama Sejaiin."""
    teks_info = (
        "ℹ️ **Tentang Sejaiin Hub**\n\n"
        "Sejaiin Hub adalah platform digital manajemen operasional pangkalan terintegrasi, "
        "sekaligus penyedia jasa kebutuhan mahasiswa Sistem Informasi dan lingkungan kosan sekitar Mendalo.\n\n"
        "🌐 **Dashboard & Informasi Utama:**\n"
        "Akses situs resmi kami untuk melihat visual tracking, monitoring dashboard, serta daftar layanan lengkap kami di:\n"
        "[Kunjungi Website Sejaiin](https://sejaiin.com)\n\n"
        "🚀 _Sistem ini dioptimalkan dengan Escrow System untuk keamanan transaksi dana titipan Anda._"
    )
    
    keyboard = [[InlineKeyboardButton("🖥 Buka Dashboard Web", url="https://sejaiin.com")]]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await update.message.reply_text(teks_info, reply_markup=reply_markup, parse_mode='Markdown')
    return ConversationHandler.END


# --- Handler Alur Pesanan ---

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Menu Utama Sejaiin Hub (Sudah Diperbarui Layout Tombolnya)."""
    current_user_id = update.effective_user.id
    
    # PERUBAHAN: Menata ulang susunan baris keyboard agar lebih seimbang dan rapi
    keyboard = [
        ["🛒 Pesan Jasa"],
        ["🤝 Daftar Mitra", "ℹ️ Informasi Sejaiin"], # Menu baru yang diminta
        ["⚠️ Laporkan Masalah", "💡 Beri Rekomendasi Jasa"],
        ["🔄 Refresh"]
    ]
    
    is_user_admin = False
    if isinstance(ADMIN_ID, (list, tuple)):
        is_user_admin = int(current_user_id) in [int(i) for i in ADMIN_ID]
    else:
        is_user_admin = int(current_user_id) == int(ADMIN_ID)

    if is_user_admin:
        keyboard.append(["🛠 Admin Panel"])
        
    reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
    await update.message.reply_text(
        "👋 **Selamat datang di Sejaiin Hub!**\n\n"
        "Solusi kebutuhan mahasiswa IS dan layanan kosan.\n"
        "Silakan pilih menu di bawah ini untuk memulai:",
        reply_markup=reply_markup,
        parse_mode='Markdown'
    )
    return ConversationHandler.END

async def pilih_kategori(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Tahap 1: Memilih Kategori (HUB)."""
    categories = [[cat] for cat in LAYANAN.keys()]
    categories.append(["❌ Batal"])
    
    await update.message.reply_text(
        "📂 **Pilih Kategori Layanan (HUB):**",
        reply_markup=ReplyKeyboardMarkup(categories, one_time_keyboard=True, resize_keyboard=True),
        parse_mode='Markdown'
    )
    return SERVICE

async def pilih_jasa(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Tahap 2: Memilih Jasa Spesifik dalam Kategori."""
    category = update.message.text
    
    if category == "❌ Batal":
        await update.message.reply_text("Pesanan dibatalkan.", reply_markup=ReplyKeyboardRemove())
        return await start(update, context)

    if category not in LAYANAN:
        await update.message.reply_text("⚠️ Kategori tidak valid. Silakan pilih kembali:")
        return SERVICE
        
    context.user_data['cat'] = category
    services = [[s] for s in LAYANAN[category]]
    services.append(["⬅️ Kembali ke Kategori"])
    
    await update.message.reply_text(
        "🛠 **Layanan Tersedia:**",
        reply_markup=ReplyKeyboardMarkup(services, one_time_keyboard=True, resize_keyboard=True),
        parse_mode='Markdown'
    )
    return ASK_LOCATION

async def minta_lokasi(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Tahap 3: Interseptor Deteksi Kategori & Meminta Lokasi Pengerjaan."""
    text = update.message.text
    if text == "⬅️ Kembali ke Kategori":
        return await pilih_kategori(update, context)
        
    context.user_data['jasa'] = text
    kategori_terpilih = context.user_data.get('cat', '')

    if "HUB 1" in kategori_terpilih or kategori_terpilih == "HUB 1":
        await update.message.reply_text(
            "💰 **Estimasi Modal Belanja / Titipan**\n\n"
            "Layanan Jastip memerlukan dana awal untuk membeli barang belanjaan Anda.\n"
            "Silakan ketik nominal estimasi harga barang belanjaan Anda:\n"
            "_(Ketik angka saja tanpa titik/Rp, contoh: `25000`)_",
            reply_markup=ReplyKeyboardRemove(),
            parse_mode='Markdown'
        )
        return WAITING_TITIPIAN
    
    context.user_data['uang_titipan'] = 0.0
    return await prompt_minta_lokasi(update, context)

async def terima_uang_titipan(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Tahap Tambahan HUB 1: Menangkap nominal titipan belanja."""
    input_text = update.message.text.strip()
    
    try:
        nominal = float(input_text.replace('.', '').replace(',', ''))
        context.user_data['uang_titipan'] = nominal
    except ValueError:
        await update.message.reply_text(
            "⚠️ Format input salah. Mohon masukkan angka murni tanpa simbol Rp atau titik.\n"
            "Contoh: `35000`"
        )
        return WAITING_TITIPIAN

    return await prompt_minta_lokasi(update, context)

async def prompt_minta_lokasi(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Fungsi pembantu guna memunculkan UI form lokasi alamat."""
    button = KeyboardButton("📍 Kirim Lokasi GPS Saya", request_location=True)
    markup = ReplyKeyboardMarkup([[button], ["🏠 Tulis Alamat Manual"]], one_time_keyboard=True, resize_keyboard=True)
    
    await update.message.reply_text(
        "📍 **Dimana lokasi pengerjaan / pengantaran?**\n\n"
        "Gunakan tombol GPS atau ketik alamat lengkap Anda secara manual.",
        reply_markup=markup,
        parse_mode='Markdown'
    )
    return WAITING_LOCATION

async def simpan_lokasi_dan_bank(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Tahap 4: Menyimpan Lokasi dan Meminta Kontak."""
    if update.message.location:
        lat, lon = update.message.location.latitude, update.message.location.longitude
        alamat_geocoded = get_address_from_coords(lat, lon)
        context.user_data['lokasi'] = f"{alamat_geocoded} (📍 http://maps.google.com/?q={lat},{lon})"
    else:
        context.user_data['lokasi'] = update.message.text

    button = KeyboardButton("📱 Bagikan Kontak WhatsApp", request_contact=True)
    markup = ReplyKeyboardMarkup([[button]], one_time_keyboard=True, resize_keyboard=True)
    
    await update.message.reply_text(
        "✅ Lokasi disimpan.\n\n"
        "Terakhir, mohon klik tombol di bawah untuk membagikan nomor WhatsApp Anda agar tim kami dapat berkoordinasi.",
        reply_markup=markup,
        parse_mode='Markdown'
    )
    return WAITING_CONTACT

async def proses_kontak_dan_order(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Tahap 5: Finalisasi Order dengan Akumulasi Hitungan Rekening Admin."""
    if not update.message.contact:
        await update.message.reply_text("⚠️ Anda harus menekan tombol **'Bagikan Kontak WhatsApp'**!")
        return WAITING_CONTACT

    no_wa = update.message.contact.phone_number
    jasa = context.user_data.get('jasa')
    lokasi = context.user_data.get('lokasi')
    uang_titipan = float(context.user_data.get('uang_titipan', 0.0))
    user_id = update.message.from_user.id
    
    try:
        order_id, harga_jasa = create_order(user_id, jasa, lokasi, no_wa, uang_titipan)
        context.user_data['order_id'] = order_id
        
        total_transfer = harga_jasa + uang_titipan
        
        rincian_user = (
            f"✅ **Order #{order_id} Berhasil Dibuat!**\n\n"
            f"🛠 **Layanan:** `{jasa}`\n"
            f"💵 **Biaya Jasa:** Rp{harga_jasa:,.0f}\n"
        )
        if uang_titipan > 0:
            rincian_user += f"💰 **Deposit Uang Titipan:** Rp{uang_titipan:,.0f}\n"
            
        rincian_user += f"━━━━━━━━━━━━━━━━━━\n"
        rincian_user += f"🚨 **TOTAL TRANSFER:** **Rp{total_transfer:,.0f}**"
        
        await update.message.reply_text(rincian_user, parse_mode='Markdown')
        await update.message.reply_text(PAYMENT_INFO, parse_mode='Markdown', reply_markup=ReplyKeyboardRemove())
        
        kb_admin = [[InlineKeyboardButton("✅ Verifikasi Pembayaran", callback_data=f"verify_{order_id}")]]
        
        admin_text = (
            f"🔔 **PESANAN BARU MASUK (ESCROW SYSTEM)**\n\n"
            f"🆔 **Order:** #{order_id}\n"
            f"🛠 **Jasa:** {jasa}\n"
            f"💵 **Harga Jasa:** Rp{harga_jasa:,.0f}\n"
        )
        if uang_titipan > 0:
            admin_text += f"💰 **Uang Titipan Belanja:** Rp{uang_titipan:,.0f}\n"
            
        admin_text += (
            f"🧮 **Wajib Transfer:** Rp{total_transfer:,.0f}\n"
            f"📍 **Lokasi:** {lokasi}\n"
            f"📞 **WhatsApp:** [Hubungi](https://wa.me/{no_wa})"
        )
        
        await context.bot.send_message(
            chat_id=GROUP_ID, 
            message_thread_id=TOPIC_SERVICES,
            text=admin_text,
            reply_markup=InlineKeyboardMarkup(kb_admin),
            parse_mode='Markdown',
            disable_web_page_preview=True
        )
        return WAITING_PHOTO
        
    except Exception as e:
        logging.error(f"Gagal membuat order: {e}", exc_info=True)
        await update.message.reply_text("❌ Terjadi kesalahan teknis saat membuat pesanan. Silakan coba lagi nanti.")
        return ConversationHandler.END

async def terima_bukti(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Tahap Akhir: Menerima Foto Bukti Transfer Pengguna."""
    if not update.message.photo:
        await update.message.reply_text("⚠️ Silakan kirimkan **FOTO/SCREENSHOT** bukti transfer Anda.")
        return WAITING_PHOTO

    order_id = context.user_data.get('order_id', 'N/A')
    photo_file_id = update.message.photo[-1].file_id
    
    await context.bot.send_photo(
        chat_id=GROUP_ID, 
        message_thread_id=TOPIC_FINANCE,
        photo=photo_file_id, 
        caption=f"📸 **BUKTI PEMBAYARAN**\n🆔 Order: #{order_id}\n👤 User: @{update.effective_user.username or 'NoUsername'}"
    )
    
    await update.message.reply_text(
        "✅ **Bukti Pembayaran Terkirim!**\n\n"
        "Admin akan segera memverifikasi pembayaran Anda. Pesanan akan segera diproses setelah dana masuk. Terima kasih! 🙏",
        parse_mode='Markdown'
    )
    return ConversationHandler.END


# --- RE-REGISTRASI ROUTER UTAMA CONVERSATION (DAN INDEPENDENT HANDLER) ---

order_conversation_handler = ConversationHandler(
    entry_points=[MessageHandler(filters.Text(["🛒 Pesan Jasa"]), pilih_kategori)],
    states={
        SERVICE: [MessageHandler(filters.TEXT & ~filters.COMMAND, pilih_jasa)],
        ASK_LOCATION: [MessageHandler(filters.TEXT & ~filters.COMMAND, minta_lokasi)],
        WAITING_TITIPIAN: [MessageHandler(filters.TEXT & ~filters.COMMAND, terima_uang_titipan)],
        WAITING_LOCATION: [MessageHandler(filters.LOCATION | (filters.TEXT & ~filters.COMMAND), simpan_lokasi_dan_bank)],
        WAITING_CONTACT: [MessageHandler(filters.CONTACT, proses_kontak_dan_order)],
        WAITING_PHOTO: [MessageHandler(filters.PHOTO, terima_bukti)]
    },
    fallbacks=[MessageHandler(filters.Text(["❌ Batal"]), start)]
)

