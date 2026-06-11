"""
Package Handlers
Pusat inisialisasi untuk semua modul penanganan pesan (handlers).
Memungkinkan akses modular melalui: from handlers import admin, worker, user, conversation
"""

from . import conversation
from . import admin
from . import worker
from . import user

# Mendefinisikan public API dari package handlers
# Hal ini memudahkan pengelolaan impor di file utama (main.py)
__all__ = [
    'conversation', # Menangani alur percakapan (Entry points & States)
    'admin',        # Menangani aksi administratif (Verifikasi, Laporan, Ops)
    'worker',       # Menangani operasional mitra (Ambil order, Bukti kerja, Registrasi)
    'user'          # Menangani fitur umum pengguna (Reporting, Help, Profile)
]