"""
Package Database
Menyediakan akses terpusat ke koneksi database dan fungsi-fungsi operasional untuk SEJAIIN-BOT.
"""

# Import fungsi koneksi utama
from .conn import get_db_connection

# Modul Orders: Menangani siklus hidup pesanan, keuangan, dan manajemen layanan
from .orders import (
    create_order,
    get_order_details,
    update_order_status,
    save_bukti_kerja,
    save_finance_report,
    update_payout_status,
    get_active_orders,
    get_pending_payouts,  # Digunakan oleh dashboard admin
    get_all_services,     # Digunakan untuk daftar layanan di bot
    auto_complete_orders,
    save_review,
    save_report,          # BARU: Diperlukan oleh feedback_ops.py untuk laporan kendala
    get_sales_data        # BARU: Diperlukan oleh finance_ops.py untuk laporan admin
)

# Modul Mitra: Menangani profil, registrasi, dan verifikasi mitra
from .mitra import (
    get_mitra_by_id,
    get_mitra_by_telegram_id,
    get_eligible_workers,
    update_mitra_status,
    save_registration_attempt,
    get_pending_mitra,
    approve_mitra,        # Menghilangkan ImportError pada mitra_ops.py
    reject_mitra          # Fungsi pendukung verifikasi admin
)

# Mendefinisikan public API (Export List)
# Hal ini mempermudah penggunaan: 'from database import save_report'
__all__ = [
    'get_db_connection',
    
    # Orders, Finance, & Feedback API
    'create_order',
    'get_order_details',
    'update_order_status',
    'save_bukti_kerja',
    'save_finance_report',
    'update_payout_status',
    'get_active_orders',
    'get_pending_payouts',
    'get_all_services',
    'auto_complete_orders',
    'save_review',
    'save_report',         # Didaftarkan agar bisa diakses oleh handler user
    'get_sales_data',      # Didaftarkan agar bisa diakses secara publik
    
    # Mitra API
    'get_mitra_by_id',
    'get_mitra_by_telegram_id',
    'get_eligible_workers',
    'update_mitra_status',
    'save_registration_attempt',
    'get_pending_mitra',
    'approve_mitra',
    'reject_mitra'
]