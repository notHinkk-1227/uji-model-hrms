# Amandemen 4 untuk Protokol Evaluasi v1.0 (8 November 2026)

Melengkapi v1.0 dan amandemen 1-3; isinya tidak diubah. Diputuskan peneliti SEBELUM model dijalankan pada foto
relawan (belum ada skor yang dilihat). Fungsi yang dipakai: `scripts/metrics.py` (lolos `test_metrics.py`).

## 1. Threshold pengenalan wajah: EER pada lipatan latih

- Per lipatan leave-one-subject-out, threshold = `threshold_eer(genuine_latih, impostor_latih)`: titik |FAR - FRR|
  terkecil; seri dipecah dengan FAR + FRR terkecil, lalu threshold terbesar. Diterima bila skor >= threshold.
- Pasangan latih: probe dari 3 relawan latih DAN identitas yang diklaim juga salah satu dari 3 relawan latih.
  Enrollment relawan uji tidak dipakai sama sekali untuk menentukan threshold.
- Pasangan uji: probe relawan uji vs enrollment dirinya (genuine) dan vs enrollment 3 relawan lain (impostor).
  Tiap pasangan diuji tepat sekali di seluruh lipatan: total genuine 62, impostor 186 (amandemen 3).
- Konsekuensi: lipatan latih hanya berisi sekitar 90 pasangan impostor (probe 3 relawan x 2 identitas latih lain),
  jadi threshold dapat berubah cukup besar antarlipatan; dilaporkan per lipatan.
- Alternatif "FAR = 0 pada latih" tidak dipakai (bergantung pada satu skor impostor ekstrem).

## 2. Liveness: aturan bawaan sebagai hasil utama; EER sebagai tambahan

- Hasil utama: aturan keputusan bawaan tiap model (spesifikasi-preprocessing-v2; tanpa threshold dari data).
- Tambahan (dilaporkan terpisah): threshold EER per lipatan latih pada skor kontinu (MiniFASNet `minifas_avg_p1`,
  face-antispoof-onnx `facenox_diff`, anti-spoof-mn3 `mn3_p_real`; positif = real, negatif = semua serangan),
  serta AUC.

## 3. Gagal deteksi dan gagal proses dihitung sebagai "ditolak"

- Foto tanpa wajah terdeteksi (`no_face`) atau gagal diproses (`error:*`) = sistem menolak:
  - liveness: foto real dihitung sebagai kesalahan BPCER; foto serangan dihitung sebagai ditolak (benar);
  - pengenalan: probe gagal -> pasangan genuine dihitung ditolak (FRR), pasangan impostor dihitung ditolak (benar).
- Jumlah kegagalan dilaporkan terpisah per model, per relawan, per kelas, per cahaya, per skenario resolusi.
- Foto enrollment yang gagal dideteksi tidak dipakai untuk templat dan dicatat; bila seluruh foto enrollment seorang
  relawan gagal, hal itu dilaporkan dan diputuskan sebelum evaluasi dilanjutkan.
- Alasan: mencerminkan sistem nyata (aplikasi menolak dan meminta foto ulang); detektor sama untuk semua model
  sehingga perlakuan ini adil antarmodel. Tidak menyembunyikan kegagalan.

## 4. Belum diputuskan (harus diputuskan sebelum modul pengenalan dijalankan pada data relawan)

- Cara menggabungkan 5 foto enrollment menjadi skor pasangan (mis. rata-rata embedding yang dinormalisasi L2, atau
  kemiripan maksimum terhadap 5 foto).
