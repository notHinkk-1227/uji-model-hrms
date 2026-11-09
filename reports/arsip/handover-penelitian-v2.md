# Serah Terima Penelitian (revisi 2, 2 November 2026)

Cara pakai: tempel dokumen ini beserta MASTER PROMPT asli di awal percakapan baru, lalu minta asisten melanjutkan dari bagian "Status dan langkah berikutnya". Asisten baru harus memverifikasi kondisi nyata lewat `logs/experiment-log.md`, `audit/` dan output perintah, bukan hanya mempercayai dokumen ini. Menggantikan handover-penelitian.md (yang masih menyebut CDCN).

## 1. Tujuan dan keputusan

- Memilih 1 model liveness dan 1 model face recognition untuk fitur absensi aplikasi HRMS mobile (backend rencana: Frappe). Target: **produksi**. Aplikasi hanya memakai **kamera depan**.
- Keenam kandidat diuji penuh dengan protokol yang sama; kelayakan produksi ditentukan terpisah lewat gerbang lisensi. Jika model berlabel riset menang, minta konfirmasi tertulis sebelum produksi.
- Liveness: (1) Silent-Face-Anti-Spoofing / MiniFASNet, (2) anti-spoof-mn3 (OpenVINO), (3) **face-antispoof-onnx (facenox)**, pengganti CDCN yang dikeluarkan (tidak ada bobot siap pakai, lisensi riset saja; peneliti menyetujui penggantian).
- Face recognition: (4) InsightFace buffalo_l, (5) AuraFace-v1, (6) SFace (OpenCV Zoo).
- Status audit (produksi): #1 LULUS AUDIT AWAL, #5 LULUS AUDIT AWAL, #2 TERTAHAN-LISENSI (dilatih pada CelebA-Spoof, nonkomersial), #3 TERTAHAN-LISENSI sementara (data latih diduga CelebA-Spoof, belum eksplisit), #6 TERTAHAN-LISENSI (dataset latih tidak disebut), #4 RISET SAJA. Detail dan bukti: `audit/model-audit-v3.md` dan `audit/license-evidence-v2.md`.
- CPU adalah jalur utama pengukuran; GPU opsional.
- Detektor wajah: satu detektor yang sama untuk semua model pada eksperimen = YuNet 2023mar (MIT, tetapi data latih WIDER Face dilabeli nonkomersial oleh sumber sekunder). Detektor produksi ditentukan terpisah (kandidat: BlazeFace, Apache-2.0, data latih Google proprietary; model card Google belum diverifikasi). Detektor bawaan MiniFASNet (RetinaFace Caffe) dan SCRFD tidak dipakai.

## 2. Lingkungan

- Windows 11, Git Bash. Laptop i7-11800H (8 core/16 thread), RAM 15,7 GB, RTX 3060 Laptop. Disk C: sisa sekitar 21 GB (96% terpakai); D: sisa sekitar 102 GB. Dataset besar diarahkan ke D: lewat konfigurasi.
- Proyek: `C:\dev\model-research-face` (Git Bash: `/c/dev/model-research-face`), repo Git dengan commit dan tag `protokol-v1.0`.
- Python 3.12.10 (winget) di samping 3.14.7. Venv: `.venv` (aktifkan: `source .venv/Scripts/activate`).
- Versi: numpy 2.5.4, onnxruntime 1.31.1, opencv-python-headless 5.0.0.93, pillow 13.0.0, easydict 1.13, tqdm 4.70.1, torch 2.15.0+cpu, torchvision 0.29.2+cpu (`configs/requirements-stage1.txt`, `requirements-stage2.txt`).
- Struktur: audit, repositories, models, datasets, configs, scripts, logs, results, reports. `.gitignore` mengecualikan venv, datasets, models, repositories, dan berkas bobot.

## 3. Fakta terverifikasi (hasil eksperimen)

Checksum lengkap: `logs/checksums-models.txt` dan `logs/checksums-silentface.txt`.

- AuraFace `glintr100.onnx`: 260694151 byte, SHA-256 a7933ea5...5c60 (cocok dengan nilai resmi). Input [batch,3,112,112], output [1,512], embedding harus dinormalisasi L2.
- SFace `face_recognition_sface_2021dec.onnx`: 38696353 byte, SHA-256 0ba9fbfa...4e79 (cocok dengan nilai mirror). Input [1,3,112,112], output [1,128].
- buffalo_l `w600k_r50.onnx`: 174383860 byte, SHA-256 4c06341c...9e43 (tanpa pembanding resmi; zip sudah dihapus, hash zip 80ffe37d...0ca2f tercatat). Input [batch,3,112,112], output [1,512]; normalisasi input yang benar belum diverifikasi.
- YuNet `face_detection_yunet_2023mar.onnx`: 232589 byte, SHA-256 8f2383e4...2fa4 (cocok dengan nilai mirror).
- MiniFASNet: commit b6d5f04ad78778917853b25c778acef6d5626d15 (2020-08-05), diekstrak ke `repositories/Silent-Face-Anti-Spoofing` dari data Git di `repositories/_git-Silent-Face-Anti-Spoofing`. Bobot V2 (a5eb02e1...bec0) sama dengan hash hulu yang dicantumkan pihak ketiga. V2: 434560 parameter; V1SE: 433586 parameter; input 80x80; kernel (5,5); keluaran 3 kelas.
- Preprocessing MiniFASNet (dari kode): BGR, nilai 0-255 (pembagian 255 dinonaktifkan), tanpa Normalize; crop diperbesar sebesar skala (V2 2,7; V1SE 4,0) lalu resize 80x80 tanpa menjaga rasio; gambar harus rasio 3:4; model dimuat ulang tiap predict (harus dipisah untuk ukur latensi); detektor bawaan tidak menangani tanpa-wajah. Makna indeks keluaran 0 dan 2 belum terverifikasi (halaman pihak ketiga mengklaim [live, print, replay], bertentangan dengan kode asli yang menganggap indeks 1 asli).

## 4. Protokol dan pengumpulan data

- Protokol evaluasi v1.0 dibekukan (`reports/protokol-evaluasi-v1.0.md`, tag `protokol-v1.0`). Perubahan hanya lewat catatan bertanggal di log.
- Relawan: 4 orang, ponsel masing-masing (kamera depan; contoh Samsung dan iPhone) sebagai inti; jangkar (ponsel rekan, sesi gabungan) dan uji stres (ponsel peneliti, kamera depan rusak) opsional. Kelas: real 20, print/screen/replay 10 per relawan per perangkat. Pencahayaan diatur fisik (bukan diedit). Foto rasio 3:4, JPEG (iPhone: format "Paling Kompatibel").
- Pembagian data: leave-one-subject-out; threshold tidak pernah disetel pada lipatan yang sedang diuji. Batas statistik: sekitar 300 pasangan impostor, FAR di bawah sekitar 1% tidak dapat dilaporkan.
- Pengambilan data baru dimulai setelah **formulir persetujuan ditandatangani semua relawan** (templat: formulir-persetujuan-relawan.md; perlu diisi bagian kurung siku dan idealnya ditinjau pembimbing/atasan).
- Struktur folder: `datasets/liveness/internal/raw/S01..S04/{own,anchor,stress}`, `datasets/recognition/internal/enrollment/S01..S04`, manifest 16 kolom di `datasets/liveness/internal/manifest.csv`.
- Akses OULU-NPU dilaporkan bermasalah pada 2022; status kini belum diverifikasi.

## 5. Status dan langkah berikutnya

- Selesai: Fase 0, Fase 1 sebagian (4 dari 6 model diunduh dan lolos smoke test: MiniFASNet, AuraFace, SFace, buffalo_l), Fase 2, protokol Fase 3 (dibekukan).
- Berikutnya:
  1. Audit dan unduh face-antispoof-onnx: baca `docs/DATA_PREPARATION.md` untuk data latih, ambil `best_model.onnx`, catat ukuran dan hash, smoke test (input RGB 128x128).
  2. Audit dan unduh anti-spoof-mn3 lewat alat `omz_downloader` di venv terpisah (agar lingkungan utama tidak terganggu).
  3. Konfirmasi dari sumber resmi: normalisasi input dan alignment tiap model pengenalan (AuraFace, buffalo_l, SFace) dan urutan warna.
  4. Tulis skrip evaluasi: deteksi YuNet, crop/alignment, preprocessing per model, pencatatan skor mentah ke `results/`, pengukuran latensi dan memori (model dimuat di luar pengukuran).
  5. Setelah formulir ditandatangani: pengambilan data, isi manifest, jalankan evaluasi sesuai protokol v1.0.
  6. Verifikasi lisensi WIDER Face (situs resmi) dan model card BlazeFace Google untuk keputusan detektor produksi.
- Catatan: laporan baseline di Claude Docs sudah diperbarui (CDCN diganti face-antispoof-onnx). Berkas lama `audit/model-audit.md`, `audit/model-audit-v2.md`, `audit/license-evidence.md`, dan `handover-penelitian.md` masih menyebut CDCN dan digantikan oleh v3, v2, dan dokumen ini.

## 6. Aturan kerja (ringkasan master prompt)

- Jangan mengarang hasil; bedakan fakta terverifikasi, klaim sumber, hasil eksperimen aktual, asumsi.
- Satu langkah kecil per giliran, tunggu output nyata; jangan menganggap perintah berhasil.
- Semua perintah untuk Git Bash di Windows 11. Format respons: A posisi, B penjelasan, C langkah, D verifikasi, E pencatatan, F gerbang.
- Tidak mengunggah foto biometrik ke percakapan; smoke test memakai data acak.
- Catat setiap modifikasi kode dan versi di `logs/experiment-log.md`.

## 7. Kesalahan yang sudah terjadi (agar tidak diulang)

- Clone MiniFASNet gagal di Windows karena path `saved_logs/.../Jul08_12-51-18 /...` (spasi di akhir nama folder). Diagnosis awal "file dihapus" salah; sparse-checkout dan `git archive HEAD` juga gagal. Yang berhasil: `git archive "HEAD:<subfolder>"` per subfolder plus `git show "HEAD:<file>"` untuk file akar; folder `images/` dan `saved_logs/` tidak diekstrak.
- Desain kamera belakang sempat diusulkan lalu dibatalkan (aplikasi hanya memakai kamera depan); kamera belakang hanya boleh untuk materi sumber serangan.
- Jangan menyatakan klaim README sebagai hasil terukur; jangan memakai README turunan sebagai bukti lisensi bila sumber resmi tersedia.
