"""
File entry point utama untuk menjalankan Bot Telegram Sejaiin Hub.
Mengatur inisialisasi aplikasi, job queue otomatis, dan registrasi handler.
Last Update: 2026-05-22 (Sinkronisasi Menu Tambahan Registrasi & Informasi Web)
"""

import sys
import os
import logging
from telegram.ext import (
    Application, CommandHandler, MessageHandler, 
    CallbackQueryHandler, filters, ConversationHandler,
    PicklePersistence
)

# Setup path agar folder bot terbaca secara global dalam project
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from config import TOKEN 
# Mengimport conv_handler serta fungsi handler mandiri untuk menu baru
from handlers import conversation as conv
from handlers.conversation.handlers import (
    daftar_mitra_handler, 
    informasi_sejaiin_handler
)
from database.orders import auto_complete_orders 

# --- IMPORT MODULAR (Admin Command Center) ---
from handlers.admin.dashboard import admin_menu_handler, admin_dashboard_navigation
from handlers.admin.order_ops import (
    admin_order_detail_handler,
    admin_verify_handler,
    admin_verify_proof_handler,
    admin_reject_proof_handler
)
from handlers.admin.mitra_ops import admin_mitra_decision_handler, admin_mitra_detail_handler
from handlers.admin.finance_ops import (
    admin_payout_done_handler, 
    admin_report_command,
    admin_report_preview_handler,
    admin_report_pdf_callback
)
from handlers.admin.service_ops import edit_harga_command

# --- IMPORT MODULAR (User & Worker) ---
from handlers.user.feedback_ops import (
    user_finish_handler, 
    user_rate_handler, 
    user_save_rating_handler,
    user_report_handler 
)
from handlers.user.report import admin_resolve_report_handler

# Import Worker Handlers
from handlers.worker.order_ops import worker_take_handler
from handlers.worker.submission import worker_send_bukti

# --- IMPORT MODULAR (User Interaction) ---
from handlers.user_interaction import (
    report_start, report_finish, 
    recom_start, recom_finish, 
    refresh_handler, REPORT, RECOM
)

# Konfigurasi Logging - Set ke INFO agar bisa melihat aktivitas di terminal
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', 
    level=logging.INFO
)

async def error_handler(update, context):
    """Log error yang terjadi agar bot tidak mati mendadak."""
    logging.error(f"Update {update} menyebabkan error {context.error}")

async def job_auto_complete(context):
    """Fungsi otomatis pembersihan rutin order."""
    try:
        auto_complete_orders()
        logging.info("Job rutin: Membersihkan order kadaluarsa...")
    except Exception as e:
        logging.error(f"Gagal menjalankan auto_complete: {e}")

def main():
    # 0. Persistence (Menjaga data state tetap aman)
    my_persistence = PicklePersistence(filepath="sejaiin_bot_persistence.pickle")

    # 1. Inisialisasi Application
    app = Application.builder() \
        .token(TOKEN) \
        .persistence(my_persistence) \
        .build()

    # 2. JobQueue (Eksekusi otomatis berkala tiap 1 jam)
    if app.job_queue:
        app.job_queue.run_repeating(job_auto_complete, interval=3600, first=60)

    # 3. Conversation Handler Utama (Isi Pendaftaran Alur Belanja/Jasa)
    app.add_handler(conv.conv_handler)

    # 4. Interaction (Report/Recom)
    conv_user_interact = ConversationHandler(
        entry_points=[
            MessageHandler(filters.Regex('^⚠️ Laporkan Masalah$'), report_start),
            MessageHandler(filters.Regex('^💡 Beri Rekomendasi Jasa$'), recom_start)
        ],
        states={
            REPORT: [MessageHandler(filters.TEXT & ~filters.COMMAND, report_finish)],
            RECOM: [MessageHandler(filters.TEXT & ~filters.COMMAND, recom_finish)],
        },
        fallbacks=[CommandHandler("cancel", refresh_handler)],
        persistent=True,
        name="interaction_conversation"
    )
    app.add_handler(conv_user_interact)
    
    # 5. Global Commands & Text Buttons
    app.add_handler(CommandHandler("admin", admin_menu_handler))
    app.add_handler(MessageHandler(filters.Regex("^🛠 Admin Panel$"), admin_menu_handler))
    app.add_handler(CommandHandler("edit_harga", edit_harga_command))
    app.add_handler(CommandHandler("laporan", admin_report_command))
    app.add_handler(MessageHandler(filters.Regex('^🔄 Refresh$'), refresh_handler))

    # --- REGISTRASI HANDLER MENU BARU ---
    # Menangkap respon ketika user menekan tombol "🤝 Daftar Mitra" atau "ℹ️ Informasi Sejaiin"
    app.add_handler(MessageHandler(filters.Regex('^🤝 Daftar Mitra$'), daftar_mitra_handler))
    app.add_handler(MessageHandler(filters.Regex('^ℹ️ Informasi Sejaiin$'), informasi_sejaiin_handler))

    # --- KELOMPOK CALLBACK HANDLERS ---
    
    # Payout Admin (Paling krusial untuk manajemen keuangan)
    app.add_handler(CallbackQueryHandler(admin_payout_done_handler, pattern='^payout_done_'))

    # User Lifecycle (Selesai & Rating Feedback)
    app.add_handler(CallbackQueryHandler(user_finish_handler, pattern='^finish_'))
    app.add_handler(CallbackQueryHandler(user_rate_handler, pattern='^rate_'))
    app.add_handler(CallbackQueryHandler(user_save_rating_handler, pattern='^save_rate_'))
    app.add_handler(CallbackQueryHandler(user_report_handler, pattern='^report_'))

    # Verifikasi Bukti Kerja Lapangan
    app.add_handler(CallbackQueryHandler(admin_verify_proof_handler, pattern='^verify_proof_'))
    app.add_handler(CallbackQueryHandler(admin_reject_proof_handler, pattern='^reject_proof_'))
    app.add_handler(CallbackQueryHandler(admin_verify_handler, pattern='^verify_[0-9]+$'))

    # Worker & Mitra Operations
    app.add_handler(CallbackQueryHandler(worker_take_handler, pattern='^take_'))
    app.add_handler(CallbackQueryHandler(admin_mitra_detail_handler, pattern='^det_mitra_'))
    app.add_handler(CallbackQueryHandler(admin_mitra_decision_handler, pattern='^(acc|dec)_mitra_'))
    
    # Order Detail & Reports
    app.add_handler(CallbackQueryHandler(admin_order_detail_handler, pattern='^order_detail_'))
    app.add_handler(CallbackQueryHandler(admin_resolve_report_handler, pattern='^resolve_report_'))
    app.add_handler(CallbackQueryHandler(admin_report_preview_handler, pattern='^admin_report_preview$'))
    app.add_handler(CallbackQueryHandler(admin_report_pdf_callback, pattern='^admin_report_pdf$'))
    
    # Navigation Admin Terpadu
    # (Ditaruh paling bawah karena pola pattern '^admin_' menyapu bersih semua aksi panel admin)
    app.add_handler(CallbackQueryHandler(admin_dashboard_navigation, pattern='^admin_'))
    
    # 12. Media Handler (Upload Bukti Transfer atau Dokumentasi Kerja)
    app.add_handler(MessageHandler(filters.PHOTO, worker_send_bukti))

    # 13. Run Engine Polling
    app.add_error_handler(error_handler)
    
    print("\n" + "="*30)
    print("SEJAIIN HUB BOT IS RUNNING...")
    print("Check terminal for logs if you click buttons!")
    print("="*30 + "\n")
    
    app.run_polling()

if __name__ == '__main__':
    main()