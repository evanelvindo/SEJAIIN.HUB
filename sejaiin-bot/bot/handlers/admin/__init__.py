# Import semua handler operasional admin
from .dashboard import admin_menu_handler, admin_dashboard_navigation
from .order_ops import (
    admin_verify_handler, 
    admin_verify_proof_handler, 
    admin_reject_proof_handler, 
    admin_order_detail_handler
)
# Pastikan mengimpor nama fungsi yang benar-benar ada di mitra_ops.py
from .mitra_ops import admin_mitra_decision_handler, admin_mitra_detail_handler
from .finance_ops import admin_payout_done_handler
from .service_ops import edit_harga_command

# Mengelompokkan semua handler agar mudah didaftarkan di main.py
__all__ = [
    'admin_menu_handler',
    'admin_dashboard_navigation',
    'admin_verify_handler',
    'admin_verify_proof_handler',
    'admin_reject_proof_handler',
    'admin_order_detail_handler',
    'admin_mitra_decision_handler', # Update nama di sini
    'admin_mitra_detail_handler',   # Tambahkan detail handler di sini
    'admin_payout_done_handler',
    'edit_harga_command'
]

# Alias untuk kompatibilitas jika ada file lama yang mencari nama 'approve_mitra_handler'
approve_mitra_handler = admin_mitra_decision_handler

def get_admin_handlers():
    """
    Mengembalikan daftar handler admin untuk mempermudah pendaftaran.
    """
    return __all__