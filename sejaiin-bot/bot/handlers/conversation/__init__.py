"""
File inisialisasi package conversation.
Mendefinisikan router utama ConversationHandler untuk alur pemesanan (Client Side).
Last Update: 2026-05-16 (Sistem Perantara & Escrow HUB 1)
"""

from telegram.ext import ConversationHandler, MessageHandler, filters, CommandHandler
from .handlers import (
    start, 
    pilih_kategori, 
    pilih_jasa, 
    minta_lokasi, 
    terima_uang_titipan,  # <-- TAMBAHAN: Handler penangkap nominal titipan belanja
    simpan_lokasi_dan_bank, 
    proses_kontak_dan_order, 
    terima_bukti
)
from .states import (
    SERVICE, 
    ASK_LOCATION, 
    WAITING_TITIPIAN,     # <-- TAMBAHAN: State penampung jeda tunggu nominal uang
    WAITING_LOCATION, 
    WAITING_CONTACT, 
    WAITING_PHOTO
)

# Definisikan Conversation Handler untuk alur pemesanan (Client Side)
conv_handler = ConversationHandler(
    entry_points=[
        CommandHandler("start", start),
        MessageHandler(filters.Regex('^🛒 Pesan Jasa$'), pilih_kategori)
    ],
    states={
        # User memilih kategori jasa (HUB 1, HUB 2, HUB 3)
        SERVICE: [
            MessageHandler(filters.TEXT & ~filters.COMMAND, pilih_jasa)
        ],
        
        # User menentukan jasa spesifik dan sistem mengecek kebutuhan uang titipan
        ASK_LOCATION: [
            MessageHandler(filters.TEXT & ~filters.COMMAND, minta_lokasi)
        ],
        
        # UPGRADE: Menangkap nominal modal belanja jika kategori yang dipilih adalah HUB 1
        WAITING_TITIPIAN: [
            MessageHandler(filters.TEXT & ~filters.COMMAND, terima_uang_titipan)
        ],
        
        # User mengirim lokasi (Teks atau Share Location GPS)
        WAITING_LOCATION: [
            MessageHandler(filters.LOCATION, simpan_lokasi_dan_bank),
            MessageHandler(filters.TEXT & ~filters.COMMAND, simpan_lokasi_dan_bank)
        ],
        
        # User mengirim kontak/nomor HP untuk koordinasi lapangan
        WAITING_CONTACT: [
            MessageHandler(filters.CONTACT, proses_kontak_dan_order)
        ],
        
        # User mengirim foto bukti pembayaran total (Harga Jasa + Uang Titipan)
        WAITING_PHOTO: [
            MessageHandler(filters.PHOTO, terima_bukti)
        ]
    },
    fallbacks=[
        CommandHandler("start", start),
        MessageHandler(filters.Regex('^❌ Batal$'), start)  # Tambahan fallback fleksibel jika user membatalkan
    ],
    name="order_conversation",
    persistent=False  # Set ke True jika kamu nanti mengonfigurasi PicklePersistence di main.py
)