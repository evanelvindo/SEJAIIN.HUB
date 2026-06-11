# DOKUMEN PENGUJIAN SISTEM (TEST CASE)
### Kelompok 4 — Sistem SEJAIIN

---

## 1. TEST CASE POSITIVE (Jalur Sukses)

> Menguji apakah sistem memberikan *output* yang benar ketika menerima *input* dan alur yang valid sesuai fungsionalitas aslinya.

| ID Test Case | Kategori | Skenario Pengujian | Test Data | Expected Result | Actual Result | Status | Bukti Screenshot |
|:---:|:---:|---|---|---|---|:---:|:---:|
| **TC-P-01** | POSITIVE | Pendaftaran akun Mitra baru melalui form Web | Nama: `Udin` · NIK: `1234567890123456` · WA: `6283171906109` | Data calon mitra tersimpan di database dengan status **MENUNGGU** sebelum diverifikasi penuh oleh admin. | ✅ Akun pendaftar baru atas nama "udin" berhasil terekam ke tabel mitra dengan `status_verifikasi = 'MENUNGGU'` dan `status_kerja = 'NONAKTIF'`. | ✅ PASS | *(Gambar 1)* |
| **TC-P-02** | POSITIVE | Pelanggan memesan jasa dan mengirimkan lokasi | Jasa: Cleaning & Ganti Thermal Paste (HUB 2) · Total: `Rp50.000` | Bot menampilkan rincian pesanan, total transfer, nomor rekening pembayaran resmi BCA, serta meminta unggah bukti transfer. | ✅ Transaksi "Order #1 Berhasil Dibuat!" dengan nominal transfer `Rp50.000` ke rekening BCA `1234567890` a.n. **SEJAIIN OFFICIAL** berhasil di-render oleh bot secara instan. | ✅ PASS | *(Gambar 2)* |
| **TC-P-03** | POSITIVE | Admin memvalidasi bukti pembayaran pelanggan | Klik tombol verifikasi pada transaksi pembayaran Order #2 | Sistem otomatis menyebarkan pesan *Broadcast/Blast Order* ke seluruh Telegram Mitra aktif. | ✅ Sistem admin memicu log otomatis: *"Order #2 berhasil diverifikasi dan disebarkan"* dan melakukan broadcast: *"Jasa: Cleaning & Ganti Thermal Paste, Status: ✅ Terkirim ke mitra aktif."* | ✅ PASS | *(Gambar 3)* |
| **TC-P-04** | POSITIVE | Mitra mengklaim order (Klaim Berhasil) | Mitra Evan menekan tombol `[⚡ Ambil Order]` | Mitra Evan menerima notifikasi pekerjaan diambil, koordinat Google Maps, tombol hubungi via WhatsApp, dan tombol kirim bukti selesai. | ✅ Bot mengirim konfirmasi *"Pekerjaan Diambil! Anda telah resmi mengambil Order #1"* lengkap dengan rincian tugas dan koordinat GPS `-1.597783, 103.506776`. | ✅ PASS | *(Gambar 4)* |
| **TC-P-05** | POSITIVE | Admin QC menyetujui foto bukti pengerjaan mitra | Klik tombol `[✅ Setujui]` pada foto kerja di Topik #SERVICES | Pelanggan menerima pesan "Pekerjaan Selesai" dan tombol konfirmasi *Rating*. | ✅ Sistem memproses verifikasi kualitas kerja mitra dan memperbarui status pesanan menjadi **SELESAI** pada basis data. | ✅ PASS | *(Gambar 5)* |

---

## 2. TEST CASE NEGATIVE (Jalur Gagal / Error Handling)

> Menguji ketahanan sistem (*robustness*) ketika menerima *input* yang tidak valid atau melanggar aturan logika bisnis.

| ID Test Case | Kategori | Skenario Pengujian | Test Data | Expected Result | Actual Result | Status | Bukti Screenshot |
|:---:|:---:|---|---|---|---|:---:|:---:|
| **TC-N-01** | NEGATIVE | Registrasi Mitra dengan NIK kurang dari 16 digit pada Web | Nama: `udin` · NIK: `12345678` (8 digit) | Input dibatalkan, form memunculkan tanda bahaya merah dan teks peringatan error. | ✅ Validasi frontend mendeteksi kesalahan input NIK dan memunculkan notifikasi merah: **"NIK valid harus berupa 16 digit angka."** serta memblokir tombol daftar. | ✅ PASS | *(Gambar 6)* |
| **TC-N-02** | NEGATIVE | Admin menolak bukti transfer pelanggan yang salah | Bukti Transfer: BSI BYOND (Order #5) · Pengirim: `@NoUsername` | Sistem menyediakan tombol penolakan `[❌ Tolak]` di panel admin untuk menolak bukti transfer tidak valid. | ❌ Saat simulasi pengunggahan bukti pembayaran BSI yang salah pada Order #5, sistem chatbot **tidak memunculkan** tombol `[❌ Tolak]` di chat grup Admin. Admin terpaksa memproses pesanan tanpa opsi penolakan sistematis. | ❌ FAIL | *(Gambar 7)* |
| **TC-N-03** | NEGATIVE | Mitra terlambat mengklaim order (Klaim Gagal) | Mitra B (Zahra) mengklik tombol klaim setelah Mitra A | Sistem menolak klaim Mitra B dan mengirimkan pesan penolakan bahwa pekerjaan telah diambil. | ✅ Mitra B menerima pesan penolakan instan secara *real-time*: **"❌ Maaf, Anda Kurang Cepat! Pekerjaan ini baru saja diambil oleh mitra lain. Tetap pantau chat bot untuk peluang kerja berikutnya!"** | ✅ PASS | *(Gambar 8)* |
| **TC-N-04** | NEGATIVE | Akses menu bot tanpa `/start` | Mengetik pesan acak saat pertama kali berinteraksi | Bot menolak input asing dan membalas dengan instruksi menekan tombol `/start`. | ✅ Sistem tidak mengalami *hang* atau *crash* dan berhasil mengarahkan pengguna kembali ke alur menu utama. | ✅ PASS | *(Gambar 9)* |

---

## 3. TEST CASE EDGE (Kasus Ekstrem)

> Menguji stabilitas sistem pada kondisi batas (*boundary*), volume berlebih, atau serangan siber (kasus ekstrem).

| ID Test Case | Kategori | Skenario Pengujian | Test Data | Expected Result | Actual Result | Status | Bukti Screenshot |
|:---:|:---:|---|---|---|---|:---:|:---:|
| **TC-E-01** | EDGE | *Race Condition* — Klaim order di milidetik bersamaan | Mitra Evan (`id=1`) dan Mitra Zahra (`id=2`) menekan tombol secara serentak. | Hanya transaksi tercepat yang sukses, tidak terjadi penetapan ganda (*double-assign*). | ✅ Melalui *Row-level locking* database, hanya satu query `UPDATE` tercepat yang sukses. Mitra `id=1` (Evan) mengunci order menjadi status **KERJA**, transaksi Zahra ditolak sistem secara aman. | ✅ PASS | *(Gambar 10)* |
| **TC-E-02** | EDGE | *XSS Script Injection* pada Input Lokasi | Alamat: `<img src="x" onerror="alert('XSS')">` | Sistem melakukan *sanitasi* teks input tanpa mengeksekusi skripnya. | ✅ Teks injeksi berhasil disaring, bot membalas *"✅ Lokasi disimpan."* secara aman tanpa mengeksekusi perintah `alert`, dan menyimpan payload sebagai string aman di database dengan status **PROSES**. | ✅ PASS | *(Gambar 11)* |
| **TC-E-03** | EDGE | Teks alamat terlalu panjang (*Volume Test*) | Memasukkan teks alamat sepanjang **> 5000 karakter** huruf. | Sistem menolak input karena melebihi kapasitas field database, atau memotong teks secara aman dengan memunculkan pesan peringatan batas karakter. | ❌ Bot Telegram mengalami *unhandled exception* (freeze/timeout). Database MySQL menolak query dengan error: **`Data too long for column 'lokasi_pengguna'`** karena belum adanya fungsi *string truncation/validation* di kode Python bot. | ❌ FAIL | *(Gambar 12)* |
| **TC-E-04** | EDGE | Pengunggahan dokumen non-foto saat bukti transfer | Mengirimkan file `Laporan Pengujian Fungsional.pdf` | Sistem mengenali tipe dokumen dan menolaknya dengan pesan: *"Harap kirimkan bukti berupa Foto/Gambar (JPG/PNG)..."* | ❌ Bot SEJAIIN tetap menerima file PDF tanpa saringan format ekstensi yang ketat. Saat sistem mencoba membaca berkas untuk proses verifikasi gambar, bot mengalami ***unhandled crash*** karena tidak dapat mengonversi dokumen PDF menjadi visual bukti bayar. | ❌ FAIL | *(Gambar 13)* |

---

## Ringkasan Hasil Pengujian

| Kategori | Total | ✅ PASS | ❌ FAIL |
|:---:|:---:|:---:|:---:|
| Positive | 5 | 5 | 0 |
| Negative | 4 | 3 | 1 |
| Edge | 4 | 2 | 2 |
| **Total** | **13** | **10** | **3** |
