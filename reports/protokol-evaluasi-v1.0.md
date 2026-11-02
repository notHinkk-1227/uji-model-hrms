# Protokol Evaluasi v1.0 (DIBEKUKAN 2026-11-02)

Tanggal: 2 November 2026. Menggantikan v0.1. Dibekukan menjadi v1.0 setelah ditinjau peneliti dan sebelum pengambilan data dimulai.

## 1. Batasan

- 4 relawan (S01 sampai S04), masing-masing memakai ponsel sendiri dengan kamera depan (mis. Samsung, iPhone). Aplikasi HRMS hanya memakai kamera depan, jadi kamera belakang tidak dipakai untuk data uji.
- Relawan yang kamera depannya buruk atau rusak memakai ponsel lain yang kamera depannya baik (mis. ponsel rekan). Catat di manifest.
- Hasil = perbandingan relatif antarmodel pada skenario kecil, bukan estimasi akurasi populasi. Tidak ada analisis demografis. Selang kepercayaan lebar dan optimistis (sampel dalam satu relawan saling berkorelasi).
- Penguat (opsional, syarat akses belum dibaca): dataset publik anti-spoofing (mis. OULU-NPU) dan benchmark pengenalan publik.

## 2. Perangkat

| Kode | Perangkat | Peran |
|---|---|---|
| own | Ponsel milik tiap relawan, kamera depan | Inti. Satu perangkat per relawan. |
| anchor | Ponsel rekan, kamera depan (opsional) | Jangkar: perangkat yang sama dipakai semua relawan di satu sesi gabungan. |
| stress | Ponsel peneliti, kamera depan rusak (opsional) | Uji stres kualitas rendah, dilaporkan terpisah; tidak ikut menentukan pemilihan model. |

Di perangkat "own", orang dan ponsel menyatu, sehingga penyebab hasil buruk tidak bisa dipisahkan. Perangkat "anchor" ada untuk membantu memisahkan keduanya.

## 3. Aturan pengambilan gambar

- Kamera depan, rasio foto **3:4**, format **JPEG** (iPhone: Pengaturan > Kamera > Format > Paling Kompatibel; HEIC tidak dibaca langsung oleh pustaka kita). Tanpa filter, mode kecantikan, atau HDR agresif jika dapat dimatikan; catat pengaturan.
- Samakan dan catat pengaturan cermin kamera depan di tiap ponsel.
- Matikan sinkronisasi cloud galeri dan penandaan lokasi selama pengambilan data. Pindahkan foto lewat kabel ke laptop, lalu hapus dari ponsel (termasuk tempat sampah galeri).
- Materi sumber serangan (foto potret dan video pendek tiap relawan) diambil dengan kamera berkualitas baik (kamera belakang boleh, karena ini sumber penyerang, bukan input presensi).

## 4. Kelas dan jumlah (usulan, dapat diturunkan atau ditambah; catat perubahan)

Per relawan per perangkat "own":

| Kelas | Cara | Jumlah |
|---|---|---|
| real | wajah asli | 20 (10 terang, 10 redup) |
| print | foto cetak (A4 kertas biasa, ukuran wajah mendekati asli) di depan kamera | 10 (5 terang, 5 redup) |
| screen | foto ditampilkan di layar (laptop; ponsel lain jika ada) | 10 |
| replay | video diputar di layar, ambil foto/frame | 10 |

Total inti: 4 x 50 = 200 foto. "anchor": 5 foto per kelas per relawan (sekitar 80). "stress": real 10, tiap serangan 5 per relawan.

Kelas real dibuat lebih banyak karena murah dan menjadi probe pengenalan wajah. Perangkat penyerang (layar) dan jenis layar dicatat.

## 5. Pengenalan wajah

- Enrollment: 5 foto per relawan, frontal, terang, perangkat "own", **sesi berbeda** dari probe.
- Probe: foto kelas real (own: 20 per relawan; anchor: 5 per relawan). Probe anchor menguji pengenalan lintas-perangkat.
- Pasangan impostor: tiap probe vs enrollment 3 relawan lain. Sekitar 100 probe menghasilkan sekitar 300 pasangan impostor.
- Batas statistik: tanpa kesalahan pun, FAR hanya bisa dibatasi sekitar 1% (aturan 3/N, keyakinan 95%). **TAR pada FAR di bawah 1% tidak dapat dilaporkan** dari data internal. Laporkan jumlah mentah FA dan FR.

## 6. Pembagian data dan threshold

- Model sudah dilatih; data hanya untuk menentukan threshold dan mengevaluasi.
- **Leave-one-subject-out (4 lipatan):** threshold dari 3 relawan, evaluasi pada 1 yang ditahan. Karena satu relawan = satu ponsel, ini mengukur "pengguna baru dengan ponsel baru". Laporkan per relawan.
- Perangkat "anchor" dan "stress" tidak dipakai menentukan threshold.
- MiniFASNet: aturan keputusan bawaan (argmax kelas 1 = asli) sebagai hasil utama; ROC dilaporkan terpisah.
- Threshold tidak pernah disetel pada lipatan yang sedang diuji.

## 7. Pipeline

- Detektor eksperimen: YuNet 2023mar, sama untuk semua model; gagal deteksi dilaporkan, tidak dibuang diam-diam.
- MiniFASNet: BGR, nilai 0-255, tanpa Normalize, skala crop 2,7 (V2) dan 4,0 (V1SE), resize 80x80, jumlah softmax dua model dibagi 2; model dimuat sekali di luar pengukuran latensi.
- AuraFace: crop 112x112 hasil alignment 5 titik (detail alignment dan normalisasi piksel dikonfirmasi dari contoh resmi sebelum dipakai), keluaran 512-d, L2-normalize, cosine similarity.

## 8. Metrik

- Liveness: APCER per jenis serangan, BPCER, ACER, AUC (bila skor kontinu), confusion matrix, per perangkat dan pencahayaan, jumlah gagal deteksi.
- Pengenalan: FAR/FRR pada threshold lipatan latih, jumlah FA dan FR, batas atas FAR, per perangkat dan pencahayaan.
- Kinerja: latensi median dan p95 setelah warm-up (CPU, minimal 100 pengulangan), memori, ukuran embedding.
- Selang kepercayaan Clopper-Pearson, ditandai optimistis. Perbandingan antarmodel pada sampel yang sama (berpasangan).

## 9. Manifest

Kolom: sample_id, subject, device_code (own/anchor/stress), device_model, os, camera (depan), class, lighting, pose, attack_display, session, mirror_setting, filename.

## 10. Belum diputuskan

- Syarat akses dataset publik.
- Jenis printer dan kertas (bawaan: printer peneliti, kertas A4 biasa).
- Ponsel dan sistem operasi tiap relawan (isi di manifest).

## 11. Tambahan v1.0: definisi pencahayaan dan pengaturan kamera (dibekukan 2026-11-02)

- Pencahayaan diatur secara fisik sebelum pengambilan gambar. Gambar tidak boleh diedit (kecerahan, warna, ketajaman). Penggelapan digital hanya untuk analisis tambahan berlabel "sintetis", terpisah dari data inti.
- Terang: lampu ruangan normal, wajah menghadap sumber cahaya, tanpa cahaya latar. Redup: ruangan disuramkan namun wajah masih jelas terlihat, bukan gelap total.
- Ukur dan catat lux dengan aplikasi pada satu ponsel yang sama sebagai penanda relatif (bukan standar mutlak).
- Eksposur otomatis bawaan; tanpa blitz; tanpa pengaturan kecerahan manual; mode malam dimatikan bila bisa, jika tidak dicatat.
- Jarak sekitar sepanjang lengan, frontal; kecerahan layar penampil serangan dibuat tetap dan dicatat.
- Keterbatasan: kamera bawaan ponsel belum tentu sama dengan kamera di dalam aplikasi HRMS (resolusi, pemrosesan, kompresi); dicatat sebagai batasan, kecuali pengambilan data dapat memakai kamera aplikasi.
- Penambahan kolom manifest: lux_catatan, night_mode, screen_brightness.
