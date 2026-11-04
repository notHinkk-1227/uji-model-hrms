# Spesifikasi Preprocessing per Model (v1, 3 November 2026)

Dasar untuk skrip evaluasi. Tiap model punya preprocessing sendiri; jangan menyamakan. Legenda: [V] terverifikasi dari kode atau dokumen resmi yang dibaca; [S] sumber sekunder; [T] belum terverifikasi.

## Keputusan pipeline bersama

- Detektor: YuNet 2023mar lewat `cv2.FaceDetectorYN` (OpenCV 5.0.0 termuat [V]). Satu deteksi per gambar, dipakai bersama oleh semua model agar perbandingan adil. Gambar dibaca dengan `cv2.imread` (BGR) dan dimasukkan ke detektor dalam BGR (konvensi OpenCV).
- Catatan penyimpangan: demo face-antispoof-onnx memasukkan gambar RGB ke detektor [V]. Kita tidak meniru ini; dampaknya pada kotak wajah dicatat sebagai keterbatasan.
- Keluaran YuNet memuat kotak (x, y, lebar, tinggi) di indeks 0-3 dan skor di indeks 14 [V dari face.py], sehingga indeks 4-13 adalah 5 titik landmark (dipakai untuk alignment model pengenalan) [T, perlu dicek saat dijalankan].
- Wajah yang tidak terdeteksi dilaporkan sebagai kegagalan deteksi, tidak dibuang diam-diam.
- Foto uji berrasio 3:4 (syarat skrip uji MiniFASNet).

## Liveness

| Item | MiniFASNet (V2 dan V1SE) | face-antispoof-onnx | anti-spoof-mn3 (model asli) |
|---|---|---|---|
| Crop | Kotak wajah (x,y,w,h) diperbesar sebesar skala 2,7 (V2) dan 4,0 (V1SE), dibatasi agar tidak keluar gambar, rasio tidak dijaga [V] | Kotak diubah ke (x1,y1,x2,y2) = (x, y, x+w, y+h); persegi dari sisi terpanjang x 1,5, dipusatkan; padding BORDER_REFLECT_101 [V] | Cara crop tidak dijelaskan di dokumen OMZ [T] |
| Ukuran | 80x80 (cv2.resize bawaan) [V] | 128x128 (INTER_AREA bila mengecil, LANCZOS4 bila membesar) [V] | 128x128 [V] |
| Urutan warna | BGR [V] | RGB [V] | RGB [V] (model terkonversi OpenVINO: BGR) |
| Skala nilai | 0-255, tanpa Normalize [V] | 0-1 (dibagi 255), tanpa mean/std [V] | (x - mean) / scale; mean [151.2405, 119.5950, 107.8395], scale [63.0105, 56.4570, 55.0035] pada skala 0-255 [V, dokumen OMZ 2021] |
| Keluaran | 3 kelas softmax; jumlah dua model dibagi 2 [V] | 2 logit [real, spoof] [V] | probabilitas 2 kelas; indeks 0 = real, 1 = spoof [V] |
| Aturan keputusan | argmax; indeks 1 = real menurut kode asli [V]; makna indeks 0 dan 2 [T] | real bila logit_real - logit_spoof >= 0 (threshold 0,5 probabilitas dikonversi) [V] | real bila indeks 0 lebih besar; threshold [T] |
| Batas input | Rasio gambar 3:4 [V] | Wajah sumber minimal sekitar 64x64 px; frontal +/-30 derajat; cahaya redup/latar kuat bermasalah (pengakuan repo) [V] | [T] |
| Bobot | Terunduh, smoke test lolos [V] | `models/best/98.20/best_model.onnx`, smoke test lolos [V] | Belum diunduh |
| Tipe format | PyTorch (.pth) | ONNX | PyTorch asli (diunduh lewat omz_downloader) |

## Face recognition

| Item | AuraFace (glintr100) | buffalo_l (w600k_r50) | SFace |
|---|---|---|---|
| Input | [batch,3,112,112] [V] | [batch,3,112,112] [V] | [1,3,112,112] [V] |
| Alignment | 5 titik landmark ke 112x112 [S] | 5 titik landmark ke 112x112 [T] | `FaceRecognizerSF.alignCrop` dengan keluaran YuNet [S] |
| Urutan warna | [T] | [T] | [T] |
| Normalisasi | (x - 127,5) / 127,5 [S]; belum dipastikan dari kode resmi | [T] (dugaan praktik ArcFace umum: sama seperti AuraFace) | [T] |
| Keluaran | 512-d [V] | 512-d [V] | 128-d [V] |
| Pasca-proses | L2-normalize lalu cosine similarity | sama | sama |
| Catatan | Norma keluaran pada input acak 0-255 tidak berarti | Norma 1837 pada input acak 0-255 menunjukkan model mengharapkan input ternormalisasi | Batch tetap 1 |

Yang harus dikonfirmasi sebelum evaluasi pengenalan: urutan warna dan normalisasi dari kode resmi (insightface ArcFaceONNX untuk dua model berbasis ArcFace; OpenCV FaceRecognizerSF untuk SFace).
