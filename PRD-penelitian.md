# PRD: Penelitian Komparatif Liveness Detection dan Face Recognition untuk Absensi HRMS Mobile

Versi 1.0, 6 November 2026. Dokumen rujukan untuk peneliti dan alat bantu (termasuk Claude Code). Aturan kerja ada di `CLAUDE.md`.

## 1. Latar belakang

Aplikasi HRMS mobile membutuhkan fitur absensi berbasis wajah. Dua komponen model dibutuhkan: (a) liveness
detection untuk menolak foto cetak dan foto di layar; (b) face recognition untuk memverifikasi identitas
pengguna yang sudah menyatakan identitasnya (verifikasi 1:1). Backend tujuan: Frappe Framework. Aplikasi hanya
memakai kamera depan. Resolusi dan format gambar yang dikirim aplikasi ke server belum ditentukan.

## 2. Tujuan dan non-tujuan

Tujuan:
- T1. Menguji enam kandidat open-source (3 liveness, 3 recognition) dengan protokol yang sama dan dapat direproduksi.
- T2. Memilih 1 model liveness dan 1 model recognition berdasarkan bukti, atau menyatakan belum ada yang layak.
- T3. Memastikan kelayakan lisensi untuk penggunaan produksi (kode, bobot, dataset latih, dependensi).
- T4. Mendokumentasikan keterbatasan, risiko, dan rancangan integrasi Frappe (analisis kelayakan).

Non-tujuan (tahap ini): implementasi backend Frappe; pelatihan ulang model; deteksi serangan video replay,
topeng 3D, atau injeksi kamera virtual; klaim akurasi populasi.

## 3. Kandidat dan status

| # | Model | Peran | Sumber | Status audit (produksi) |
|---|---|---|---|---|
| 1 | MiniFASNetV2 + V1SE | liveness | github.com/minivision-ai/Silent-Face-Anti-Spoofing (commit b6d5f04a, 2020) | LULUS AUDIT AWAL |
| 2 | anti-spoof-mn3 | liveness | OpenVINO Open Model Zoo (omz_downloader) | TERTAHAN-LISENSI (CelebA-Spoof nonkomersial) |
| 3 | face-antispoof-onnx | liveness | github.com/facenox/face-antispoof-onnx (commit 2f8dd93d) | TERTAHAN-LISENSI sementara |
| 4 | InsightFace buffalo_l (w600k_r50) | recognition | github.com/deepinsight/insightface release v0.7 | RISET SAJA |
| 5 | AuraFace-v1 (glintr100) | recognition | huggingface.co/fal/AuraFace-v1 | LULUS AUDIT AWAL |
| 6 | SFace | recognition | OpenCV Zoo (huggingface.co/opencv/face_recognition_sface) | TERTAHAN-LISENSI |

CDCN dikeluarkan (tanpa bobot siap pakai, lisensi riset saja) dan diganti face-antispoof-onnx. Keenam model
tetap diuji penuh; kelayakan produksi ditentukan terpisah oleh gerbang lisensi. Bila model berlabel riset menang,
perlu konfirmasi tertulis sebelum produksi. Bukti lisensi: `audit/license-evidence-v2.md`.
Detektor wajah bersama: YuNet 2023mar (eksperimen); detektor produksi belum ditentukan (kandidat BlazeFace).

## 4. Data dan protokol

- Protokol: `reports/protokol-evaluasi-v1.0.md` (dibekukan) + amandemen 1-4 (`reports/amandemen-protokol-*.md`).
- Relawan: 4 (S01-S04), ponsel masing-masing, kamera depan, foto rasio 3:4 JPEG, cahaya terang/redup diatur fisik.
- Kelas: real, print (foto cetak), screen (foto di layar). Replay dan uji stres tidak dikumpulkan.
- Jumlah: per relawan real 20 (10 terang, 10 redup), print 10, screen 10; enrollment 5. Total 160 foto liveness + 20 enrollment.
- Pembagian: leave-one-subject-out (threshold dari 3 relawan, uji pada 1). Aturan keputusan bawaan tiap model; ROC terpisah.
- Skenario resolusi: batas sisi terpanjang 640, 1280, penuh (utama sementara 1280, ASUMSI).
- Pengenalan: enrollment 5 foto per relawan; probe = foto real yang BUKAN duplikat enrollment; 1:1; impostor = probe vs enrollment relawan lain.
- Metrik liveness: APCER per jenis serangan, BPCER, ACER, AUC, confusion matrix, per cahaya dan per relawan.
- Metrik pengenalan: FAR/FRR pada threshold dari lipatan latih, jumlah FA/FR, batas atas FAR (aturan 3/N), per cahaya.
- Kinerja: latensi median dan p95 CPU (1 dan 4 thread), memori; model dimuat di luar pengukuran.
- Interval kepercayaan Clopper-Pearson (optimistis karena korelasi dalam relawan); perbandingan antarmodel berpasangan.

## 5. Kebutuhan teknis (skrip) dan kriteria penerimaan

| ID | Kebutuhan | Status | Kriteria penerimaan |
|---|---|---|---|
| K1 | Detektor bersama + gagal-deteksi tercatat | SELESAI | `test_resolusi.py`: 1 wajah pada semua ukuran 375-4032 px |
| K2 | Preprocessing per model liveness | SELESAI | `test_warna.py` SEMUA OK |
| K3 | Inferensi liveness ke CSV + metadata | SELESAI | CSV + `.meta.json` (hash bobot, versi, aturan keputusan) |
| K4 | Benchmark latensi dan memori | SELESAI (awal) | median/p95 per model; kondisi laptop tercatat |
| K5 | Penataan dan pemeriksaan data | SELESAI | `periksa_data.py`: duplikat, rasio, orientasi terlaporkan |
| K6 | Manifest 16 kolom | SELESAI | 160 baris; detail perangkat/pengaturan diberi penanda "tidak_dicatat" |
| K7 | Modul metrik (APCER dll., CI, berpasangan) | SELESAI | lolos uji pada data tiruan berlabel dengan jawaban diketahui |
| K8 | Modul pengenalan (alignment, embedding, cosine) | SELESAI (uji identitas berbeda belum) | templat ArcFace dari kode resmi; uji pasangan sama/beda |
| K9 | Evaluasi penuh (LOSO x skenario resolusi) | SELESAI 2026-11-08 (liveness + pengenalan, 640/1280/penuh) | CSV skor mentah + tabel metrik; tanpa threshold pada data uji |
| K10 | Laporan akhir + rekomendasi + kelayakan Frappe | BELUM | memenuhi "definisi selesai" di bawah |

## 6. Asumsi, risiko, dan hal belum terverifikasi

- Persetujuan relawan ditandatangani semua: SUDAH DIKONFIRMASI peneliti (8 November 2026).
- Semua gambar dipotong tengah ke tepat 3:4 sebelum pipeline (`reports/amandemen-protokol-2.md`).
- Crop anti-spoof-mn3: terverifikasi dari kode sumber (amandemen 5); ketatnya kotak YuNet vs detektor asli [T]. Makna indeks keluaran 0 dan 2 MiniFASNet: belum diverifikasi.
- Data latih bobot MiniFASNet dan face-antispoof-onnx tidak dinyatakan; lisensi WIDER Face (YuNet) belum dibaca dari situs resmi.
- Templat 5 titik ArcFace dan `norm_crop`: terverifikasi dari kode resmi insightface (commit ffa12d3); SimilarityTransform skimage diganti Umeyama numpy (diuji).
- Resolusi dan format unggahan aplikasi HRMS belum ditentukan.
- Kebocoran enrollment -> probe: 18 dari 20 foto identik dikeluarkan dari probe (62 probe tersisa; `reports/amandemen-protokol-3.md`).
  Enrollment sesi yang sama dengan probe dan sebagian redup: bias optimistis pada pengenalan.
- Data kecil (4 relawan): hasil = perbandingan relatif; tidak ada analisis demografis; FAR di bawah ~1,6% (3/186) tidak dapat dibuktikan.
- Akses dataset publik (mis. OULU-NPU) dilaporkan bermasalah; tidak diandalkan.
- Liveness pasif RGB tidak melindungi dari injeksi kamera virtual atau topeng 3D.

## 7. Definisi selesai

Penelitian selesai bila: keenam kandidat terdokumentasi (audit + hasil atau alasan tidak dilanjutkan); hasil dapat
direproduksi (log, hash bobot, versi, konfigurasi, skor mentah); satu model liveness dan satu recognition dipilih
berdasarkan bukti atau dinyatakan belum ada yang layak; kelayakan lisensi ditinjau; keterbatasan dicatat;
rekomendasi integrasi Frappe terdokumentasi; tidak ada hasil yang dibuat-buat.
