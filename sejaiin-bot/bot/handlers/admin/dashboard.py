"""
File handler Utama untuk Dashboard Admin Sejaiin Hub (Command Center).
Menggabungkan menu operasional lama dan sistem finansial/mitra baru.
Last Update: 2026-05-23 (Optimized for MySQL Dictionary Cursor)
"""

import logging
from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.ext import ContextTypes
from config import ADMIN_ID
from database.orders import get_active_orders, get_pending_payouts, get_all_services
from database.mitra import get_pending_mitra

# --- Security Check ---
def is_admin(user_id):
    """Memastikan user yang mengakses adalah admin resmi."""
    try:
        if isinstance(ADMIN_ID, (list, tuple)):
            return int(user_id) in [int(i) for i in ADMIN_ID]
        return int(user_id) == int(ADMIN_ID)
    except (ValueError, TypeError):
        return False

# --- Keyboard Helpers ---
def get_admin_main_kb():
    """Menu utama dashboard admin terpadu."""
    return InlineKeyboardMarkup([
        [
            InlineKeyboardButton("📦 Order Aktif", callback_data="admin_orders"),
            InlineKeyboardButton("👥 Verifikasi Mitra", callback_data="admin_mitra")
        ],
        [
            InlineKeyboardButton("💰 Keuangan & Payout", callback_data="admin_finance"),
            InlineKeyboardButton("🛠 Edit Layanan", callback_data="admin_services")
        ],
        [
            InlineKeyboardButton("📢 Broadcast Pesan", callback_data="admin_broadcast_all"),
            InlineKeyboardButton("🚨 Laporan Masalah", callback_data="admin_view_reports")
        ],
        [
            InlineKeyboardButton("📊 Laporan Ringkas", callback_data="admin_report_preview"),
            InlineKeyboardButton("❌ Tutup Menu", callback_data="admin_close_menu")
        ]
    ])

def get_back_kb():
    """Tombol universal untuk kembali ke menu utama admin."""
    return InlineKeyboardMarkup([[InlineKeyboardButton("⬅️ Kembali ke Menu Utama", callback_data="admin_home")]])

# --- Main Menu Handler ---
async def admin_menu_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Entry point utama untuk dashboard admin."""
    user_id = update.effective_user.id
    if not is_admin(user_id):
        logging.warning(f"Akses ditolak: User {user_id} mencoba membuka menu admin.")
        if update.message:
            await update.message.reply_text("⛔ Akses Ditolak. Anda bukan administrator.")
        elif update.callback_query:
            await update.callback_query.answer("⛔ Akses Ditolak.", show_alert=True)
        return
        
    text = (
        "🤖 **SEJAIIN HUB - COMMAND CENTER**\n"
        "----------------------------------\n"
        "Selamat datang di pusat kendali operasional sistem.\n"
        "Silakan pilih menu manajemen di bawah ini:"
    )
    
    query = update.callback_query
    if query:
        try:
            await query.edit_message_text(text, reply_markup=get_admin_main_kb(), parse_mode='Markdown')
        except Exception as e:
            logging.debug(f"Pesan tidak diubah: {e}")
    else:
        await update.message.reply_text(text, reply_markup=get_admin_main_kb(), parse_mode='Markdown')

# --- Navigation Handler ---
async def admin_dashboard_navigation(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Mengelola navigasi interaktif antar menu dengan pembacaan key dictionary MySQL."""
    query = update.callback_query
    user_id = update.effective_user.id
    
    if not is_admin(user_id):
        await query.answer("❌ Anda tidak memiliki akses admin.", show_alert=True)
        return

    await query.answer()
    
    # Navigasi 1: Home
    if query.data == "admin_home":
        await admin_menu_handler(update, context)
        
    # Navigasi 2: Manajemen Order Aktif
    elif query.data == "admin_orders":
        orders = get_active_orders()
        if not orders:
            await query.edit_message_text("📦 Saat ini tidak ada order yang sedang aktif.", reply_markup=get_back_kb())
        else:
            kb = [[InlineKeyboardButton(f"Order #{o['id']} - {o['jenis_jasa']}", callback_data=f"order_detail_{o['id']}")] for o in orders]
            kb.append([InlineKeyboardButton("⬅️ Kembali ke Menu Utama", callback_data="admin_home")])
            await query.edit_message_text("📦 **Daftar Order Aktif:**\nPilih order untuk melihat detail atau verifikasi:", 
                                         reply_markup=InlineKeyboardMarkup(kb), parse_mode='Markdown')
            
    # Navigasi 3: Verifikasi Mitra
    elif query.data == "admin_mitra":
        mitra = get_pending_mitra()
        if not mitra:
            await query.edit_message_text("👥 Tidak ada pendaftaran mitra yang perlu diverifikasi.", reply_markup=get_back_kb())
        else:
            kb = [[InlineKeyboardButton(f"📝 {m['nama_lengkap']}", callback_data=f"det_mitra_{m['id']}")] for m in mitra]
            kb.append([InlineKeyboardButton("⬅️ Kembali ke Menu Utama", callback_data="admin_home")])
            await query.edit_message_text("👥 **Daftar Calon Mitra:**\nPilih nama untuk melihat detail & verifikasi:", 
                                         reply_markup=InlineKeyboardMarkup(kb), parse_mode='Markdown')

    # Navigasi 4: Keuangan & Payout
    elif query.data == "admin_finance":
        payouts = get_pending_payouts()
        if not payouts:
            await query.edit_message_text("💰 Tidak ada tagihan payout ke mitra yang pending.", reply_markup=get_back_kb())
        else:
            kb = [[InlineKeyboardButton(f"💳 Order #{o['id']} (Rp{o['harga_final']:,})", callback_data=f"payout_done_{o['id']}")] for o in payouts]
            kb.append([InlineKeyboardButton("⬅️ Kembali ke Menu Utama", callback_data="admin_home")])
            await query.edit_message_text("💰 **Payout Pending:**\nKlik tombol di bawah jika Anda sudah mentransfer gaji ke mitra:", 
                                         reply_markup=InlineKeyboardMarkup(kb), parse_mode='Markdown')
        
    # Navigasi 5: Manajemen Layanan (Services)
    elif query.data == "admin_services":
        services = get_all_services()
        text = "🛠 **Daftar Layanan Sistem:**\n\n"
        for s in services:
            text += f"ID: `{s['id']}` | **{s['nama_layanan']}**\n💰 Harga: Rp{s['harga']:,}\n\n"
        
        text += "💡 *Gunakan command:* `/edit_harga [id] [harga]`"
        await query.edit_message_text(text, reply_markup=get_back_kb(), parse_mode='Markdown')

    # Navigasi 6: Preview Laporan
    elif query.data == "admin_report_preview":
        await query.edit_message_text("📊 Fitur laporan penjualan sedang dalam pengembangan.", reply_markup=get_back_kb())

    # Navigasi 7: Laporan Masalah
    elif query.data == "admin_view_reports":
        await query.edit_message_text("🚨 Menampilkan laporan masalah dari user (Fitur pengembangan).", reply_markup=get_back_kb())

    # Navigasi 8: Broadcast Pesan
    elif query.data == "admin_broadcast_all":
        await query.edit_message_text("📢 Fitur broadcast pesan massal sedang disiapkan.", reply_markup=get_back_kb())

    # Navigasi 9: Tutup Menu
    elif query.data == "admin_close_menu":
        try:
            await query.message.delete()
        except Exception as e:
            logging.error(f"Gagal menghapus pesan menu admin: {e}")