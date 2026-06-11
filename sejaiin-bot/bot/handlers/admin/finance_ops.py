"""
File handler Modular untuk Manajemen Keuangan, Laporan Bisnis, dan Payout Mitra.
Mendukung cetak dokumen PDF serta sistem notifikasi otomatis ke akun Telegram Mitra.
Last Update: 2026-05-23 (Fix Agregasi & SINKRONISASI STRUKTUR PAYOUTS)
"""

import os
import logging
from fpdf import FPDF
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes
# Import variabel dari config
from config import GROUP_ID, TOPIC_FINANCE, TOPIC_PAYOUT, PROFIT_MARGIN 
from database.orders import get_order_details, update_payout_status, get_sales_data
from database.mitra import get_mitra_by_id

# Setup logging
logging.basicConfig(level=logging.ERROR, format='%(asctime)s - %(message)s')

# --- 1. LOGIKA TAMPILAN LAPORAN (PREVIEW) ---
async def show_report_logic(update, context, is_callback=False):
    """Menampilkan ringkasan teks laporan keuangan di Telegram secara akurat."""
    data = get_sales_data()
    
    if not data:
        msg = "⚠️ Tidak ada data transaksi di tabel keuangan (payouts) yang ditemukan."
        if is_callback: await update.callback_query.edit_message_text(msg)
        else: await update.message.reply_text(msg)
        return

    total_omzet = 0
    total_payout = 0
    total_margin = 0
    clean_transactions = []

    for row in data:
        # Hanya hitung finansial dari order yang sudah sukses dibayar (PAID)
        if row.get('status_bayar') == 'PAID':
            harga = float(row.get('harga_final', 0))
            margin = float(row.get('keuntungan_admin', 0))
            payout = float(row.get('gaji_mitra', 0))
            
            total_omzet += harga
            total_payout += payout
            total_margin += margin

        # Tetap masukkan ke list riwayat untuk preview (menampilkan Order ID asli)
        clean_transactions.append({
            'order_id': row.get('order_id', '?'),
            'profit': float(row.get('keuntungan_admin', 0)),
            'status': row.get('status_bayar', 'PENDING')
        })

    text = (
        "📊 **LAPORAN KEUANGAN SEJAIIN**\n"
        f"*(Status: PAID / Sukses Selesai)*\n"
        "━━━━━━━━━━━━━━━━━━\n"
        f"💰 Total Omzet: *Rp{total_omzet:,.0f}*\n"
        f"🤝 Payout Mitra: *Rp{total_payout:,.0f}*\n"
        f"📈 Net Margin: *Rp{total_margin:,.0f}*\n"
        "━━━━━━━━━━━━━━━━━━\n"
        "**5 Transaksi Terakhir:**\n"
    )
    
    # Tampilkan 5 riwayat transaksi teratas
    for t in clean_transactions[:5]:
        status_icon = "🟢" if t['status'] == 'PAID' else "🟡"
        text += f"• {status_icon} #{t['order_id']} | Margin Hub: Rp{t['profit']:,.0f}\n"

    keyboard = [[InlineKeyboardButton("📥 Cetak PDF Lengkap", callback_data="admin_report_pdf")]]
    reply_markup = InlineKeyboardMarkup(keyboard)

    if is_callback:
        await update.callback_query.answer()
        await update.callback_query.edit_message_text(text, parse_mode='Markdown', reply_markup=reply_markup)
    else:
        await update.message.reply_text(text, parse_mode='Markdown', reply_markup=reply_markup)

# --- 2. GENERATOR PDF ---
def create_sales_report_pdf(data):
    """Membuat dokumen PDF untuk laporan detail menggunakan library FPDF."""
    pdf = FPDF(orientation='L', unit='mm', format='A4')
    pdf.add_page()
    
    # Header Laporan
    pdf.set_font("Arial", 'B', 16)
    pdf.cell(0, 10, txt="LAPORAN LABA RUGI SEJAIIN HUB", ln=True, align='C')
    pdf.set_font("Arial", '', 10)
    pdf.cell(0, 10, txt=f"Skema Profit Margin Default: {PROFIT_MARGIN * 100:.0f}%", ln=True, align='C')
    pdf.ln(5)

    # Tabel Header
    pdf.set_font("Arial", 'B', 10)
    pdf.set_fill_color(230, 230, 230)
    pdf.cell(25, 10, "Order ID", 1, 0, 'C', True)
    pdf.cell(55, 10, "Tanggal", 1, 0, 'C', True)
    pdf.cell(45, 10, "Omzet (Rp)", 1, 0, 'C', True)
    pdf.cell(45, 10, "Payout Mitra (Rp)", 1, 0, 'C', True)
    pdf.cell(45, 10, "Margin Hub (Rp)", 1, 0, 'C', True)
    pdf.cell(35, 10, "Status", 1, 1, 'C', True)

    # Isi Tabel
    pdf.set_font("Arial", '', 10)
    t_omzet, t_payout, t_margin = 0, 0, 0
    
    for row in data:
        r_id = str(row.get('order_id', '-'))
        r_date = str(row.get('created_at', '-'))
        harga = float(row.get('harga_final', 0))
        margin = float(row.get('keuntungan_admin', 0))
        payout = float(row.get('gaji_mitra', 0))
        status = str(row.get('status_bayar', 'PENDING'))
        
        pdf.cell(25, 10, f"#{r_id}", 1, 0, 'C')
        pdf.cell(55, 10, r_date, 1, 0, 'L')
        pdf.cell(45, 10, f"{harga:,.0f}", 1, 0, 'R')
        pdf.cell(45, 10, f"{payout:,.0f}", 1, 0, 'R')
        pdf.cell(45, 10, f"{margin:,.0f}", 1, 0, 'R')
        pdf.cell(35, 10, status, 1, 1, 'C')
        
        if status == 'PAID':
            t_omzet += harga
            t_payout += payout
            t_margin += margin

    # Footer Total
    pdf.set_font("Arial", 'B', 10)
    pdf.set_fill_color(245, 245, 245)
    pdf.cell(80, 10, "GRAND TOTAL (PAID ONLY)", 1, 0, 'R', True)
    pdf.cell(45, 10, f"{t_omzet:,.0f}", 1, 0, 'R', True)
    pdf.cell(45, 10, f"{t_payout:,.0f}", 1, 0, 'R', True)
    pdf.cell(45, 10, f"{t_margin:,.0f}", 1, 0, 'R', True)
    pdf.cell(35, 10, "", 1, 1, 'C', True)

    file_name = "laporan_keuangan_sejaiin.pdf"
    pdf.output(file_name)
    return file_name

# --- 3. HANDLER COMMAND & CALLBACK ---

async def admin_report_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await show_report_logic(update, context, is_callback=False)

async def admin_report_preview_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await show_report_logic(update, context, is_callback=True)

async def admin_report_pdf_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer("Menyusun file PDF...")
    
    data = get_sales_data()
    if not data: return
    
    file_path = create_sales_report_pdf(data)
    
    with open(file_path, 'rb') as doc:
        await context.bot.send_document(
            chat_id=query.message.chat_id, 
            document=doc, 
            caption=f"✅ **Laporan Keuangan Detail**\n*(Tabel Payouts Terintegrasi)*",
            parse_mode='Markdown'
        )
    
    if os.path.exists(file_path): 
        os.remove(file_path)

async def admin_payout_done_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    
    try:
        order_id = query.data.split('_')[2]
        
        order = get_order_details(order_id)
        if not order:
            return await query.edit_message_text("❌ Error: Data order tidak ditemukan.")
        
        m_id_internal = order.get('mitra_id') or order.get('worker_id')

        mitra_data = get_mitra_by_id(m_id_internal)
        if not mitra_data:
            return await query.edit_message_text(f"❌ Error: Data profil mitra (ID DB: {m_id_internal}) tidak ditemukan.")

        target_chat_id = mitra_data.get('telegram_id_mitra')
        nama_mitra = mitra_data.get('nama_lengkap', 'Mitra')
        
        if not target_chat_id:
            return await query.edit_message_text(f"❌ Error: ID Telegram Mitra kosong di database.")

        success = update_payout_status(order_id, 'PAID')

        if success:
            try:
                msg = (
                    f"✅ **GAJI DITRANSFER**\n\n"
                    f"Halo {nama_mitra},\n"
                    f"Gaji untuk Order **#{order_id}** telah dikirim oleh Admin ke rekening Anda.\n\n"
                    f"Silakan dicek ya. Terima kasih!"
                )
                await context.bot.send_message(chat_id=target_chat_id, text=msg, parse_mode='Markdown')
                await query.edit_message_text(f"✅ Payout Berhasil. Notifikasi terkirim ke {nama_mitra}.")
            except Exception as e:
                await query.edit_message_text(f"⚠️ DB Update OK, tapi Notif Telegram Gagal dikirim: {e}")
        else:
            await query.edit_message_text("❌ Gagal memperbarui status pembayaran di database.")

    except Exception as e:
        logging.error(f"Error Payout: {e}")
        await query.edit_message_text(f"❌ Terjadi kesalahan sistem: {e}")