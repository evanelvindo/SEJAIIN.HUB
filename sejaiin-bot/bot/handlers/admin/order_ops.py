import logging
from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.ext import ContextTypes
from config import GROUP_ID, TOPIC_SERVICES, TOPIC_FINANCE, PROFIT_MARGIN
from database.orders import (
    get_order_details, 
    update_order_status, 
    update_payout_status
)
from database.mitra import get_mitra_by_id
from handlers.worker.broadcast import broadcast_to_workers
from handlers.admin.dashboard import get_back_kb

# Setup logging
logging.basicConfig(level=logging.ERROR, format='%(asctime)s - %(message)s')

# --- 1. Order Detail Handler ---
async def admin_order_detail_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Menampilkan detail lengkap pesanan di sisi admin."""
    query = update.callback_query
    await query.answer()
    
    try:
        # Callback format: order_detail_123
        order_id = query.data.split('_')[-1] 
        order = get_order_details(order_id)
        
        if not order:
            await query.edit_message_text("⚠️ Data order tidak ditemukan.", reply_markup=get_back_kb())
            return

        text = (
            f"📄 **Detail Order #{order['id']}**\n"
            f"━━━━━━━━━━━━━━━━━━\n"
            f"👤 **User ID:** `{order.get('telegram_id_pengguna')}`\n"
            f"🛠 **Jasa:** {order.get('jenis_jasa')}\n"
            f"📍 **Lokasi:** {order.get('lokasi_pengguna')}\n"
            f"💰 **Harga:** Rp{float(order.get('harga_final', 0)):,.0f}\n"
            f"📊 **Status:** `{order.get('status_order')}`\n"
            f"📅 **Waktu:** {order.get('created_at')}\n"
            f"━━━━━━━━━━━━━━━━━━"
        )
        
        kb = []
        if order['status_order'] == 'VERIFIKASI_ADMIN':
            kb.append([InlineKeyboardButton("✅ Verifikasi & Broadcast", callback_data=f"verify_{order_id}")])
        
        kb.append([InlineKeyboardButton("⬅️ Kembali", callback_data="admin_orders")])
        await query.edit_message_text(text, reply_markup=InlineKeyboardMarkup(kb), parse_mode='Markdown')

    except Exception as e:
        logging.error(f"Error admin_order_detail: {e}")
        await query.edit_message_text(f"❌ Error memuat detail: {str(e)}")

# --- 2. Order Lifecycle Handlers ---

async def admin_verify_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Memverifikasi order baru dan menyebarkannya ke mitra."""
    query = update.callback_query
    await query.answer()
    
    try:
        order_id = query.data.split('_')[1]
        order = get_order_details(order_id)
        
        if not order:
            await query.edit_message_text("⚠️ Gagal verifikasi: Order tidak ditemukan.")
            return
        
        update_order_status(order_id, 'PENDING')
        success = await broadcast_to_workers(context, order)
        
        status_broadcast = "✅ Terkirim ke mitra aktif." if success else "⚠️ Tidak ada mitra aktif saat ini."
        admin_log = (
            f"📣 **ORDER BROADCASTED**\n"
            f"🆔 Order: #{order_id}\n"
            f"🛠 Jasa: {order['jenis_jasa']}\n"
            f"📢 Status: {status_broadcast}"
        )
        
        await context.bot.send_message(
            chat_id=GROUP_ID,
            message_thread_id=TOPIC_SERVICES,
            text=admin_log,
            parse_mode='Markdown'
        )
        
        await query.edit_message_text(f"✅ Order #{order_id} berhasil diverifikasi dan disebarkan.")
        
    except Exception as e:
        logging.error(f"Error admin_verify: {e}")
        await query.edit_message_text(f"❌ Terjadi kesalahan verifikasi: {e}")

async def admin_verify_proof_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    
    try:
        order_id = query.data.split('_')[2] 
        order = get_order_details(order_id)
        
        if not order:
            await query.edit_message_caption(caption="⚠️ Data order tidak ditemukan.")
            return

        success = update_order_status(order_id, 'MENUNGGU_KONFIRMASI_USER')

        if success:
            await query.edit_message_caption(
                caption=f"{query.message.caption}\n\n✅ **DISETUJUI ADMIN**\nStatus: Menunggu konfirmasi pelanggan.",
                reply_markup=None 
            )

            user_id = order.get('telegram_id_pengguna')
            if user_id:
                try:
                    kb_user = [[InlineKeyboardButton("🏁 Pekerjaan Selesai", callback_data=f"finish_{order_id}")]]
                    await context.bot.send_message(
                        chat_id=user_id,
                        text=(
                            f"✅ **Bukti Kerja Disetujui!**\n\n"
                            f"Admin telah memverifikasi pekerjaan untuk Order **#{order_id}**.\n"
                            f"Silakan tekan tombol di bawah untuk menyelesaikan pesanan jika sudah sesuai."
                        ),
                        reply_markup=InlineKeyboardMarkup(kb_user),
                        parse_mode='Markdown'
                    )
                except Exception as e:
                    logging.error(f"Gagal kirim pesan ke user: {e}")

    except Exception as e:
        logging.error(f"Error admin_verify_proof: {e}")

async def admin_reject_proof_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    
    try:
        order_id = query.data.split('_')[2]
        order = get_order_details(order_id)
        
        m_id = order.get('mitra_id') or order.get('worker_id')
        mitra_data = get_mitra_by_id(m_id)
        
        if mitra_data:
            target_id = mitra_data.get('telegram_id_mitra') or mitra_data.get('telegram_id')
            if target_id:
                await context.bot.send_message(
                    chat_id=target_id, 
                    text=(
                        f"❌ **Bukti Kerja Ditolak Admin**\n"
                        f"Order: #{order_id}\n\n"
                        f"Bukti yang Anda kirimkan tidak valid. Silakan perbaiki dan kirim ulang."
                    )
                )
        
        status_text = f"❌ Bukti Order #{order_id} ditolak. Notifikasi telah dikirim ke mitra."
        if query.message.caption:
            await query.edit_message_caption(caption=status_text, reply_markup=None)
        else:
            await query.edit_message_text(status_text)

    except Exception as e:
        logging.error(f"Error admin_reject_proof: {e}")

async def admin_payout_done_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    
    try:
        # Ambil order_id dari callback_data: payout_done_{order_id}
        order_id = query.data.split('_')[2]
        
        # 1. Ambil data order untuk dapat mitra_id
        order = get_order_details(order_id)
        m_id = order.get('mitra_id')
        
        # 2. Ambil data mitra untuk dapat ID Telegram
        mitra = get_mitra_by_id(m_id)
        
        if not mitra or not mitra.get('telegram_id_mitra'):
            await query.edit_message_text(f"❌ Gagal: ID Telegram Mitra (ID:{m_id}) tidak ditemukan di DB!")
            return

        target_chat_id = mitra['telegram_id_mitra']

        # 3. Update status di tabel payouts (supaya tidak pending lagi)
        from database.orders import update_payout_status
        success = update_payout_status(order_id, 'PAID')

        if success:
            # 4. KIRIM NOTIFIKASI KE MITRA
            try:
                await context.bot.send_message(
                    chat_id=target_chat_id,
                    text=f"✅ **Gaji Cair!**\nPembayaran untuk Order #{order_id} telah dikirim ke rekening Anda. Silakan cek berkala. Terima kasih!"
                )
                await query.edit_message_text(f"✅ Payout Berhasil & Notifikasi terkirim ke Mitra.")
            except Exception as tg_err:
                logging.error(f"Telegram error: {tg_err}")
                await query.edit_message_text(f"⚠️ Payout di DB Berhasil, tapi Gagal kirim pesan ke Mitra: {tg_err}")
        else:
            await query.edit_message_text("❌ Gagal update status di database payouts.")

    except Exception as e:
        logging.error(f"Error admin_payout_done_handler: {e}")
        await query.edit_message_text(f"❌ Terjadi kesalahan: {e}")