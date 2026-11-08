# Spesifikasi Preprocessing per Model (v2, 4 November 2026)

Menggantikan v1. Dasar untuk skrip evaluasi. Tiap model punya preprocessing sendiri; jangan menyamakan. Legenda: [V] terverifikasi dari kode atau dokumen resmi yang dibaca atau dari hasil eksperimen; [S] sumber sekunder; [T] belum terverifikasi.

## Keputusan pipeline bersama

- Detektor: YuNet 2023mar lewat `cv2.FaceDetectorYN` (OpenCV 5.0.0 termuat [V]). Satu deteksi per gambar, dipakai bersama semua model agar perbandingan adil. Gambar dibaca dengan `cv2.imread` (BGR) dan dimasukkan ke detektor dalam BGR (konvensi OpenCV). Demo face-antispoof-onnx memasukkan RGB ke detektor [V]; kita tidak meniru ini dan mencatat penyimpangannya.
- Baris keluaran YuNet: kotak (x, y, lebar, tinggi) di kolom 0-3, **5 landmark di kolom 4-13**, skor di kolom 14 [V: `alignCrop` OpenCV membaca landmark dari kolom 4-13; `face.py` repo facenox membaca skor dari kolom 14].
- Wajah tidak terdeteksi dilaporkan sebagai kegagalan deteksi, tidak dibuang diam-diam.
- Foto uji berrasio 3:4 (syarat skrip uji MiniFASNet).
- Konversi warna dilakukan di dalam fungsi preprocessing masing-masing model (gambar sumber selalu BGR).

## Liveness

| Item | MiniFASNet (V2 dan V1SE) | face-antispoof-onnx | anti-spoof-mn3 |
|---|---|---|---|
| Crop | Kotak (x,y,w,h) diperbesar sebesar skala 2,7 (V2) dan 4,0 (V1SE), dibatasi agar tidak keluar gambar, rasio tidak dijaga [V] | Kotak diubah ke (x1,y1,x2,y2) = (x, y, x+w, y+h); persegi dari sisi terpanjang x 1,5, dipusatkan; padding BORDER_REFLECT_101 [V] | Cara crop tidak dijelaskan di dokumen OMZ [T] |
| Ukuran | 80x80 (cv2.resize bawaan) [V] | 128x128 (INTER_AREA bila mengecil, LANCZOS4 bila membesar) [V] | 128x128 [V] |
| Urutan warna | BGR [V] | RGB [V] | RGB [V] |
| Skala nilai | 0-255, tanpa Normalize [V] | 0-1 (dibagi 255), tanpa mean/std [V] | (x - mean) / scale; mean [151.2405, 119.5950, 107.8395], scale [63.0105, 56.4570, 55.0035] pada skala 0-255 [V, dokumen OMZ] |
| Bentuk input | [1,3,80,80] [V] | [batch,3,128,128] [V] | [1,3,128,128] (batch tetap 1) [V] |
| Keluaran | 3 kelas softmax; jumlah dua model dibagi 2 [V] | 2 logit [real, spoof] [V] | 2 probabilitas, jumlah 1,0 (softmax sudah di dalam model) [V smoke test]; indeks 0 = real, 1 = spoof [V dokumen] |
| Aturan keputusan | argmax; indeks 1 = real menurut kode asli [V]; makna indeks 0 dan 2 [T] | real bila logit_real - logit_spoof >= 0 [V] | real bila p[0] > p[1] (usulan sama dengan argmax; threshold lain [T]) |
| Batas input | Rasio gambar 3:4 [V] | Wajah sumber minimal sekitar 64x64 px; frontal +/-30 derajat; cahaya redup/latar kuat bermasalah (pengakuan repo) [V] | [T] |
| Bobot | Smoke test lolos [V] | `models/best/98.20/best_model.onnx`, smoke test lolos [V] | `anti-spoof-mn3.onnx` 12270179 byte, smoke test lolos [V] |

Catatan smoke test anti-spoof-mn3: pada input acak model menghasilkan [0.983, 0.017] (yakin "real") dari derau murni. Itu menunjukkan model bisa yakin secara salah pada input tak bermakna; smoke test hanya membuktikan model berjalan, bukan kualitas.

## Face recognition

| Item | AuraFace (glintr100) | buffalo_l (w600k_r50) | SFace |
|---|---|---|---|
| Input | [batch,3,112,112] [V] | [batch,3,112,112] [V] | [1,3,112,112] [V] |
| Alignment | Similarity transform 5 landmark ke templat ArcFace 112x112 (`norm_crop` insightface) [S]; nilai titik templat harus diambil dari kode resmi [T] | sama dengan AuraFace [S][T] | `alignCrop` OpenCV: similarity transform dari 5 landmark YuNet (kolom 4-13), `warpAffine` 112x112 INTER_LINEAR [V, kode OpenCV] |
| Urutan warna | RGB (`blobFromImages` dengan `swapRB=True` dari gambar BGR) [S] | RGB [S] | RGB (`blobFromImage` dengan `swapRB=true`) [V, kode OpenCV] |
| Normalisasi | (x - 127,5) / 127,5 [S] | (x - 127,5) / 127,5 [S]; pengecualian: graf dengan node Sub/Mul awal memakai mean 0, std 1 [S]; norma 1837 pada input 0-255 menunjukkan normalisasi tidak ada di dalam model | Tanpa normalisasi: skala 1,0 dan mean 0, nilai 0-255 mentah [V, kode OpenCV] |
| Keluaran | 512-d [V] | 512-d [V] | 128-d [V] |
| Pasca-proses | L2-normalize lalu cosine similarity | sama | sama (OpenCV `match` mendukung cosine) |

Yang harus dikonfirmasi sebelum evaluasi pengenalan: nilai lima titik templat ArcFace dan implementasi `norm_crop` dari kode resmi insightface (hanya bagian kode, tanpa bobot); verifikasi empiris bahwa AuraFace dan buffalo_l menghasilkan kemiripan tinggi untuk dua foto orang yang sama dan rendah untuk orang berbeda (dengan foto uji non-biometrik atau relawan setelah persetujuan).

## Pembaruan 8 November 2026 (pengenalan; isi tabel di atas tidak diubah)

- Templat ArcFace dan `norm_crop` [V]: kode resmi insightface commit ffa12d315041c0505b077c7ff057ca914bb8dc7e
  (`python-package/insightface/utils/face_align.py`, SHA-256 a8b34ddd06716f5ca7e7501415cbd3789ccbce18db9e557b35e537695290d922).
  Templat `[[38.2946, 51.6963], [73.5318, 51.5014], [56.0252, 71.7366], [41.5493, 92.3655], [70.7299, 92.2041]]`;
  SimilarityTransform (skimage) lalu `cv2.warpAffine` 112x112, borderValue 0. Implementasi kita: Umeyama numpy (skimage tidak terpasang), diuji.
- Normalisasi AuraFace dan buffalo_l [V]: aturan `arcface_onnx.py` (commit sama, SHA-256 89041694a9c2ec9f84c506797a810b5dc95ab57f89407de541de62a6fea981a9):
  8 node pertama kedua graf tidak memuat Sub/Mul -> mean = std = 127,5; `blobFromImages(..., swapRB=True)` -> RGB.
- Urutan landmark YuNet sama dengan urutan templat [V pada face.jpg]: mata kiri-gambar, mata kanan-gambar, hidung, mulut kiri-gambar, mulut kanan-gambar.
