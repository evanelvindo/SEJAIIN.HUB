import logging
from telegram import InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes
from database.mitra import get_eligible_workers

# Setup logging
logging.basicConfig(level=logging.ERROR, format='%(asctime)s - %(message)s')

async def broadcast_to_workers(context: ContextTypes.DEFAULT_TYPE, order: dict):
    """
    Mengirimkan notifikasi order baru ke semua mitra yang sesuai dengan jenis jasa.
    Fungsi ini dipicu saat admin memverifikasi pembayaran user di Admin Panel.
    """
    # 1. Ekstraksi Data Order
    order_id = order.get('id')
    jasa = order.get('jenis_jasa') or order.get('jasa')
    # Menggunakan field lokasi yang konsisten dengan flow conversation/handlers.py
    lokasi = order.get('lokasi_pengguna') or order.get('lokasi', 'Lokasi tidak tersedia')
    
    # 2. Filter Mitra Berdasarkan Keahlian/Spesialisasi
    workers = get_eligible_workers(jasa)
    
    if not workers: 
        logging.warning(f"Broadcast Order #{order_id}: Tidak ada mitra ditemukan untuk spesialisasi {jasa}")
        return False
    
    count_sent = 0
    
    # 3. Iterasi dan Kirim Pesan Personal ke Setiap Mitra
    for worker in workers:
        try:
            # Mengakomodasi variasi nama kolom di database (telegram_id atau telegram_id_mitra)
            target_id = worker.get('telegram_id') or worker.get('telegram_id_mitra')
            
            if not target_id:
                continue

            # Keyboard untuk aksi mitra
            kb = [[InlineKeyboardButton("🛠 Ambil Pekerjaan Ini", callback_data=f"take_{order_id}")]]
            
            text_msg = (
                f"🔔 **ADA PELUANG KERJA BARU!**\n"
                f"━━━━━━━━━━━━━━━━━━━━\n"
                f"🆔 **Order ID:** `#{order_id}`\n"
                f"🛠 **Jasa:** {jasa}\n"
                f"📍 **Lokasi:** {lokasi}\n\n"
                f"Klik tombol di bawah secepatnya jika Anda siap mengerjakan ini. "
                f"Sistem menggunakan prinsip **'Siapa Cepat, Dia Dapat'**!"
            )
            
            await context.bot.send_message(
                chat_id=target_id, 
                text=text_msg, 
                reply_markup=InlineKeyboardMarkup(kb),
                parse_mode='Markdown'
            )
            count_sent += 1
            
        except Exception as e:
            logging.error(f"Gagal kirim broadcast ke mitra {worker.get('id', 'Unknown')}: {e}")
            continue
            
    logging.info(f"Broadcast Selesai: {count_sent} mitra telah dinotifikasi untuk Order #{order_id}.")
    
    # Mengembalikan True jika minimal ada 1 pesan yang berhasil terkirim
    return count_sent > 0