import logging
from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.ext import ContextTypes
from database.mitra import assign_worker, get_mitra_by_telegram_id
from database.orders import get_order_details
from config import GROUP_ID, TOPIC_ORDER_TAKEN

# Setup logging
logging.basicConfig(level=logging.ERROR, format='%(asctime)s - %(message)s')

async def worker_take_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Menangani aksi ketika mitra menekan tombol 'Ambil Pekerjaan'.
    Mengunci order di database, memberi tahu pengguna, dan mencatat log di grup admin.
    """
    query = update.callback_query
    await query.answer("Sedang memverifikasi pengambilan order...")
    
    try:
        # 1. Parsing Data
        # Callback data format: 'take_{order_id}'
        order_id = query.data.split('_')[1]
        worker_id = update.effective_user.id
        
        # 2. Transaksi Database (Atomic Operation)
        # assign_worker harus mengembalikan False jika status order sudah bukan 'MENUNGGU_MITRA'
        if assign_worker(order_id, worker_id):
            order = get_order_details(order_id)
            mitra = get_mitra_by_telegram_id(worker_id)
            
            if not order or not mitra:
                await query.edit_message_text("❌ Terjadi kesalahan sinkronisasi data. Hubungi admin.")
                return

            # Simpan ID order di context agar bot tahu foto yang dikirim nanti adalah bukti untuk order ini
            context.user_data['active_order_id'] = order_id

            # 3. Antarmuka untuk Mitra
            user_wa = order.get('no_whatsapp_user', '')
            # Normalisasi nomor WA (menghapus tanda + atau spasi jika ada)
            wa_clean = ''.join(filter(str.isdigit, user_wa))
            
            kb_mitra = [
                [InlineKeyboardButton("💬 Hubungi User (WhatsApp)", url=f"https://wa.me/{wa_clean}")],
                [InlineKeyboardButton("📷 Kirim Bukti Selesai", callback_data=f"send_proof_{order_id}")]
            ]
            
            await query.edit_message_text(
                f"✅ **Pekerjaan Diambil!**\n\n"
                f"Anda telah resmi mengambil **Order #{order_id}**.\n"
                f"━━━━━━━━━━━━━━━━━━━━\n"
                f"🛠 **Tugas:** {order.get('jenis_jasa')}\n"
                f"📍 **Lokasi:** {order.get('lokasi_pengguna')}\n\n"
                f"Silakan hubungi pelanggan dan segera selesaikan tugas Anda. "
                f"Jika sudah selesai, kirimkan **Foto Bukti Kerja** di chat ini.",
                reply_markup=InlineKeyboardMarkup(kb_mitra),
                parse_mode='Markdown'
            )
            
            # 4. Notifikasi Otomatis ke Pengguna
            mitra_wa = mitra.get('no_whatsapp', '')
            mitra_wa_clean = ''.join(filter(str.isdigit, mitra_wa))
            kb_user = [[InlineKeyboardButton("💬 Chat Mitra via WA", url=f"https://wa.me/{mitra_wa_clean}")]]
            
            try:
                await context.bot.send_message(
                    chat_id=order['telegram_id_pengguna'],
                    text=(
                        f"✨ **Kabar Baik! Mitra Ditemukan.**\n\n"
                        f"Pesanan Anda `#{order_id}` telah diambil oleh **{mitra['nama_lengkap']}**.\n"
                        f"Beliau akan segera menghubungi Anda atau Anda bisa memulai chat melalui tombol di bawah."
                    ),
                    reply_markup=InlineKeyboardMarkup(kb_user),
                    parse_mode='Markdown'
                )
            except Exception as e:
                logging.error(f"Gagal notifikasi user {order['telegram_id_pengguna']}: {e}")
            
            # 5. Laporan ke Grup Admin (Topic Order Taken)
            await context.bot.send_message(
                chat_id=GROUP_ID, 
                message_thread_id=TOPIC_ORDER_TAKEN,
                text=(
                    f"🏃‍♂️ **ORDER DIAMBIL MITRA**\n"
                    f"━━━━━━━━━━━━━━━━━━━━\n"
                    f"🆔 **Order ID:** `#{order_id}`\n"
                    f"👤 **Mitra:** {mitra['nama_lengkap']}\n"
                    f"📱 **ID Mitra:** `{worker_id}`\n"
                    f"📊 **Status:** Progres Pengerjaan"
                ),
                parse_mode='Markdown'
            )
        else:
            # Jika assign_worker mengembalikan False karena order sudah diambil orang lain
            await query.edit_message_text(
                "❌ **Maaf, Anda Kurang Cepat!**\n\n"
                "Pekerjaan ini baru saja diambil oleh mitra lain. "
                "Tetap pantau chat bot untuk peluang kerja berikutnya!"
            )

    except Exception as e:
        logging.error(f"Error di worker_take_handler: {e}")
        await query.message.reply_text("❌ Sistem gagal memproses pengambilan order.")