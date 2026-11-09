# Amandemen 7 untuk Protokol Evaluasi v1.0 (DRAF, 9 November 2026)

STATUS: DRAF, belum dibekukan. Harus dibekukan (commit bertanda "dibekukan") SEBELUM pengambilan foto dimulai.
Melengkapi v1.0 dan amandemen 1-6; isinya tidak diubah. Menindaklanjuti amandemen 6.

## 1. Tujuan

Mengambil ulang foto serangan liveness dengan KAMERA DEPAN agar foto asli dan foto serangan berasal dari kamera yang
sama, lalu mengevaluasi ulang liveness. Hasil liveness lama (serangan kamera belakang) tidak dipakai memilih model
(amandemen 6) dan tetap disimpan sebagai catatan.

## 2. Lingkup

- Yang diulang: foto serangan saja. Per relawan: print 10 dan screen 10. Total 80 foto.
- Yang TIDAK diulang: foto asli liveness (80) dan enrollment; dipakai apa adanya.
- Replay video, topeng 3D, dan injeksi kamera virtual tetap tidak dikumpulkan dan tidak diuji (amandemen 1). Dicatat sebagai keterbatasan.
- Relawan dan ponsel sama dengan pengambilan foto asli (S01-S04, ponsel masing-masing).

## 3. Aturan pengambilan

- Kamera DEPAN ponsel relawan memotret hasil presentasi serangan (kertas cetak atau layar). Kamera belakang tidak dipakai untuk memotret presentasi serangan.
- Materi sumber serangan (foto potret relawan) boleh diambil dengan kamera berkualitas baik (protokol v1.0 bagian 3).
- Rasio foto 3:4, format JPEG (iPhone: Pengaturan > Kamera > Format > Paling Kompatibel).
- Print: A4 kertas biasa, ukuran wajah mendekati asli; 5 pencahayaan terang dan 5 redup (protokol v1.0 bagian 4).
- Screen: layar laptop; kecerahan layar dibuat tetap dan dicatat; pencahayaan dicatat per foto.
- Pencahayaan diatur fisik; foto tidak boleh diedit (protokol v1.0 bagian 11). Pengaturan cermin kamera depan sama dengan saat foto asli dan dicatat.
- Jarak sekitar sepanjang lengan, frontal. Tanpa blitz, tanpa mode kecantikan atau HDR agresif bila dapat dimatikan.
- Matikan sinkronisasi cloud galeri dan penandaan lokasi; pindahkan foto lewat kabel; hapus dari ponsel termasuk tempat sampah galeri.
- Foto baru disimpan di folder terpisah dari foto serangan lama; foto lama tidak dihapus atau ditimpa.
- Model ponsel dan OS dicatat di manifest (kolom device_model dan os; manifest berada di datasets/ yang tidak ikut Git).
- Persetujuan relawan dipastikan masih berlaku sebelum pengambilan.

## 4. Pemeriksaan sebelum evaluasi (syarat lolos)

Hanya header EXIF yang dibaca (orientasi, merek, model, software, lensa, bukaan, panjang fokus); GPS, tanggal, nomor seri,
dan piksel tidak dibaca. Per relawan:
1. foto serangan baru dan foto asli memakai lensa yang sama (bukaan dan panjang fokus sama);
2. himpunan ukuran asli foto serangan baru dan foto asli tumpang tindih.
Bila salah satu syarat gagal pada seorang relawan, hal itu dilaporkan dan diputuskan sebelum evaluasi dilanjutkan; hasil liveness
tidak dipakai memilih model sampai syarat terpenuhi.

## 5. Evaluasi

- Pipeline, aturan keputusan bawaan, threshold EER lipatan latih, perlakuan gagal deteksi, dan tiga skenario resolusi (640, 1280, penuh) sama dengan amandemen 1-5. Tidak ada aturan yang diubah setelah melihat hasil.
- Foto asli lama (kamera depan) dipasangkan dengan foto serangan baru (kamera depan). Foto serangan lama tidak ikut.
- Hasil baru ditulis ke berkas terpisah dari hasil lama; hasil lama diberi label "v1 (serangan kamera belakang)" dan tidak digabung.
- Jumlah gagal deteksi dilaporkan per model, relawan, kelas, cahaya, dan skenario.

## 6. Keterbatasan yang wajib dilaporkan

- Foto serangan baru diambil pada sesi berbeda dari foto asli; perbedaan waktu, cahaya, atau pengaturan antar sesi dapat memengaruhi skor [T].
- 4 relawan dan 4 ponsel: perbandingan relatif, bukan akurasi populasi; selang kepercayaan optimistis.
- Hanya serangan cetak dan foto di layar; replay video dan serangan lain tidak diuji.
- Kamera bawaan ponsel belum tentu sama dengan kamera di dalam aplikasi HRMS.
