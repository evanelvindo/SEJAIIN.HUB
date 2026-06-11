import logging
from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.ext import ContextTypes
from config import PROFIT_MARGIN, GROUP_ID, TOPIC_FINANCE
from database.orders import update_order_status, get_order_details, save_finance_report
from database.mitra import get_mitra_by_id

# Gunakan print agar terlihat di terminal tanpa setting logging yang ribet
async def user_finish_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    
    print("\n--- [DEBUG] HANDLER USER_FINISH DIPANGGIL ---") # Ini PASTI muncul di terminal
    
    try:
        order_id = query.data.split('_')[1]
        print(f"DEBUG: Memproses Order ID: {order_id}")
        
        order = get_order_details(order_id)
        if not order:
            print("DEBUG: Order tidak ditemukan di database!")
            await query.edit_message_text("⚠️ Data order tidak ditemukan.")
            return

        m_id = order.get('mitra_id')
        print(f"DEBUG: Mitra ID dari Order: {m_id}")
        
        # 1. KALKULASI
        harga_total = float(order.get('harga_final') or 0)
        margin = harga_total * PROFIT_MARGIN
        gaji = harga_total - margin
        print(f"DEBUG: Harga: {harga_total}, Gaji: {gaji}")

        # 2. SIMPAN KE PAYOUTS (DATABASE)
        print("DEBUG: Mencoba simpan ke tabel payouts...")
        saved = save_finance_report(order_id, harga_total, margin, gaji)
        
        if saved:
            print("DEBUG: ✅ BERHASIL simpan ke tabel payouts.")
        else:
            print("DEBUG: ❌ GAGAL simpan ke tabel payouts. Cek fungsi save_finance_report!")

        # 3. UPDATE STATUS ORDER
        update_order_status(order_id, 'SELESAI')
        print("DEBUG: Status order diupdate ke SELESAI.")

        # 4. KIRIM KE GRUP FINANCE
        mitra = get_mitra_by_id(m_id)
        nama = mitra.get('nama_lengkap', 'Unknown') if mitra else 'Unknown'
        
        kb_finance = [[InlineKeyboardButton("✅ Konfirmasi Transfer", callback_data=f"payout_done_{order_id}")]]
        msg_finance = (
            f"💰 **PAYOUT REQUEST**\n"
            f"🆔 Order: `#{order_id}`\n"
            f"👷 Mitra: {nama} (ID: {m_id})\n"
            f"💸 Gaji: **Rp{gaji:,.0f}**"
        )
        
        await context.bot.send_message(
            chat_id=GROUP_ID,
            message_thread_id=TOPIC_FINANCE,
            text=msg_finance,
            reply_markup=InlineKeyboardMarkup(kb_finance),
            parse_mode='Markdown'
        )
        print("DEBUG: Pesan ke Grup Finance terkirim.")

        await query.edit_message_text("✅ Pesanan Selesai! Terima kasih.")

    except Exception as e:
        print(f"❌ CRASH DI HANDLER: {e}")
        logging.error(f"Error User Finish: {e}", exc_info=True)