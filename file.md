# DOKUMEN PENGUJIAN SISTEM

---

## TEST CASE POSITIVE (Jalur Sukses)

Menguji apakah sistem memberikan *output* yang benar ketika menerima *input* dan alur yang valid.

| ID Test Case | Kategori | Skenario Pengujian | Test Data | Expected Result | Actual Result | Status | Bukti (Screenshot) |
|---|---|---|---|---|---|---|---|
| TC-P-01 | POSITIVE | Pendaftaran akun Mitra baru melalui form Web | Nama: Budi Santoso NIK: 1500293847561029 WA: 0812345678 Upload: ktp_budi.jpg | Data tersimpan di database dengan status MENUNGGU. Notifikasi masuk ke Telegram Admin Topik #RECRUITMENT. | PASS | PASS | |
| TC-P-02 | POSITIVE | Pelanggan memesan jasa dan kirim lokasi | Menu: HUB 2 (Cuci Sepatu) Lokasi: Kost Orange Kamar 3 | Bot menampilkan rincian pesanan, harga (Rp25.000), dan meminta *upload* bukti transfer. | PASS | PASS |  |
| TC-P-03 | POSITIVE | Admin memvalidasi bukti pembayaran | Klik tombol [✅ Sah (ACC)] pada Topik #FINANCE | Sistem otomatis mengirim pesan *BlastOrder* ke seluruh telegram mitra yang berstatus aktif. | PASS | PASS | |
| TC-P-04 | POSITIVE | Mitra mengklaim order (Tercepat) | Mitra A menekan tombol [⚡ Ambil Order] pertama kali | Mitra A menerima notifikasi "Order Berhasil Diambil" beserta detail alamat pelanggan. | saat mitra menekan tombol ambil order mitra mendapatkan notifikasi order berhasil di ambil | PASS |  |
| TC-P-05 | POSITIVE | Admin QC menyetujui foto bukti kerja | Klik tombol [✅ Setujui] pada foto kerja di Topik #SERVICES | Pelanggan menerima pesan "Pekerjaan Selesai" dan tombol konfirmasi *Rating*. |disaat admin menyetujui bukti kerja pelanggan menerima pesan pekerjaan selesai dan dapat memberikan rating bintang| PASS |  |

---

## TEST CASE NEGATIVE (Jalur Gagal / Error Handling)

Menguji ketahanan sistem (*robustness*) ketika menerima *input* yang salah atau melanggar aturan bisnis.

| ID Test Case | Kategori | Skenario Pengujian | Test Data | Expected Result | Actual Result | Status | Bukti (Screenshot) |
|---|---|---|---|---|---|---|---|
| TC-N-01 | NEGATIVE | Registrasi Mitra dengan NIK kurang dari 16 digit | Nama: Joko NIK: 12345 (Hanya 5 digit) WA: 0812 | Sistem menolak *input*, form memunculkan pesan error "NIK harus 16 digit angka". Data tidak masuk ke database. | disaat di tes dengan no nik yang kurang dari 16 digit ada notifikasi nik harus berupa 16 digit angka | PASS | |
| TC-N-02 | NEGATIVE | Admin menolak bukti transfer pelanggan | Klik tombol [❌ Tolak] pada Topik #FINANCE | Sistem *tidak* melakukan blast order. Pelanggan menerima pesan: "Mohon maaf, foto bukti pembayaran kurang jelas. Mari kirimkan ulang." | - | [PASS/FAIL] | |
| TC-N-03 | NEGATIVE | Mitra terlambat mengklaim order | Mitra B menekan tombol [⚡ Ambil Order] setelah Mitra A | Sistem menolak klaim Mitra B dan memunculkan notifikasi: "Maaf, Order sudah diambil oleh mitra lain!". | - | [PASS/FAIL] |  |

---

## TEST CASE EDGE (Kasus Ekstrem)

Menguji stabilitas sistem pada kondisi batas (*boundary*), volume berlebih, atau logika yang tidak lazim (kasus ekstrem).

| ID Test Case | Kategori | Skenario Pengujian | Test Data | Expected Result | Actual Result | Status | Bukti (Screenshot) |
|---|---|---|---|---|---|---|---|
| TC-E-01 | EDGE | *Race Condition* (Klaim order bersamaan) | Mitra A dan Mitra B menekan tombol [⚡ Ambil Order] di milidetik yang persis sama. | Sistem hanya memproses satu pemenang berdasarkan urutan masuk database (Locking/Timestamp). Tidak ada order yang ter-assign ganda (*Double assign*). | - | [PASS/FAIL] |  |
| TC-E-02 | EDGE | *Input Injection* pada Lokasi Pelanggan | Lokasi diisi dengan script: `<script>alert('hack')</script>` atau `' OR 1=1;--` | Sistem melakukan sanitasi teks. Bot dan Database tetap aman, teks disimpan sebagai *string* biasa, sistem tidak teretas (*SQL/XSS Injection gagal*). | bot dan database tetap aman,namun text tersimpan sesuai dengan  yang pengguna masukan  | FAIL |  |
| TC-E-03 | EDGE | Pengiriman file bukan gambar saat upload bukti bayar | Mengirimkan file berekstensi .pdf, .exe, atau audio .mp3 ke bot. | Bot menolak file dan menampilkan pesan peringatan: "Harap kirimkan bukti berupa Foto/Gambar (JPG/PNG), bukan dokumen/file lain." | bot tidak merespon ketika pelanggan mengirim bukti tranfer berektensi .pdf,.exe,bot hanya merespon ketika pengguna mengirim berupa foto/gambar | FAIL |  |
