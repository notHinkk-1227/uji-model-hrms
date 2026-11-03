# Serah Terima Penelitian: Liveness Detection dan Face Recognition (HRMS Mobile)

Dibuat: 2 November 2026. Cara pakai: tempel dokumen ini beserta MASTER PROMPT asli di awal percakapan baru, lalu minta asisten melanjutkan dari bagian "Status dan langkah berikutnya". Asisten baru harus memverifikasi kondisi nyata lewat `logs/experiment-log.md` dan output perintah, bukan hanya mempercayai dokumen ini.

## 1. Tujuan dan keputusan

- Memilih 1 model liveness dan 1 model face recognition untuk fitur absensi pada aplikasi HRMS mobile (backend rencana: Frappe). Target: **produksi**.
- Keenam kandidat diuji dan dibandingkan penuh (keputusan peneliti; atasan mengizinkan model open-source). Kelayakan produksi ditentukan terpisah lewat gerbang lisensi. Jika model berlabel riset menang, minta konfirmasi tertulis sebelum produksi.
- Liveness: (1) Silent-Face-Anti-Spoofing / MiniFASNet, (2) anti-spoof-mn3 (OpenVINO), (3) CDCN.
- Face recognition: (4) InsightFace buffalo_l, (5) AuraFace-v1, (6) SFace (OpenCV Zoo).
- Status audit (target produksi): #1 LULUS AUDIT AWAL, #5 LULUS AUDIT AWAL, #2 TERTAHAN-LISENSI (dilatih pada CelebA-Spoof, nonkomersial), #6 TERTAHAN-LISENSI (dataset latih tidak disebut), #3 RISET SAJA, #4 RISET SAJA. Detail dan bukti: `audit/model-audit.md` dan `audit/license-evidence.md`.
- CPU adalah jalur utama pengukuran. GPU opsional dan belakangan.
- Pipeline produksi tidak boleh memakai detektor bawaan: RetinaFace Caffe milik MiniFASNet (dilatih pada WIDER FACE) dan SCRFD milik paket InsightFace/AuraFace (nonkomersial menurut sumber sekunder). Detektor berlisensi bersih harus dipilih dan diaudit sendiri (kandidat: YuNet dari OpenCV Zoo, lisensi belum diverifikasi di sumber resmi).

## 2. Lingkungan

- Windows 11, Git Bash. Laptop i7-11800H (8 core/16 thread), RAM 15,7 GB, RTX 3060 Laptop. Disk C: sisa sekitar 23 GB (96% terpakai); D: sisa sekitar 102 GB. Dataset besar harus diarahkan ke D: lewat konfigurasi.
- Proyek: `C:\dev\model-research-face` (Git Bash: `/c/dev/model-research-face`). Git sudah di-init.
- Python 3.12.10 (winget, scope user) di samping 3.14.7. Venv: `.venv` (aktifkan: `source .venv/Scripts/activate`).
- Versi terpasang: numpy 2.5.4, onnxruntime 1.31.1, opencv-python-headless 5.0.0.93 (OpenCV 5), pillow 13.0.0, easydict 1.13, tqdm 4.70.1, torch 2.15.0+cpu, torchvision 0.29.2+cpu. Daftar: `configs/requirements-stage1.txt` dan `requirements-stage2.txt`.
- Struktur: audit, repositories, models, datasets/{liveness,recognition}, configs, scripts, logs, results/{liveness,recognition,combined}, reports. `.gitignore` mengecualikan venv, datasets, models, repositories, dan berkas bobot.

## 3. Fakta terverifikasi (hasil eksperimen aktual)

- AuraFace: `models/auraface/glintr100.onnx`, 260694151 byte, SHA-256 `a7933ea5330113b01c9b60351d8f4c33003f145d8470ac5f0e52ee2effe25c60` (cocok dengan nilai resmi Hugging Face). Hanya glintr100.onnx, LICENSE.md, README.md yang diunduh; SCRFD dan model lain sengaja tidak.
- Smoke test AuraFace (data acak, bukan pengukuran kualitas): input `[batch dinamis, 3, 112, 112]`; output `[1, 512]`; norma L2 sekitar 9,71, jadi embedding harus dinormalisasi L2 sebelum cosine.
- MiniFASNet: diekstrak ke `repositories/Silent-Face-Anti-Spoofing` dari data Git di `repositories/_git-Silent-Face-Anti-Spoofing`, HEAD `b6d5f04ad78778917853b25c778acef6d5626d15` (commit terakhir 2020-08-05). Remote resmi `github.com/minivision-ai/Silent-Face-Anti-Spoofing`. LICENSE Apache 2.0 terverifikasi.
- Checksum lokal (tanpa pembanding resmi), `logs/checksums-silentface.txt`:
  - `2.7_80x80_MiniFASNetV2.pth` a5eb02e1843f19b5386b953cc4c9f011c3f985d0ee2bb9819eea9a142099bec0
  - `4_0_0_80x80_MiniFASNetV1SE.pth` 84ee1d37d96894d5e82de5a57df044ef80a58be2b218b5ed7cdfd875ec2f5990
  - `deploy.prototxt` 5935df8926b4fd8f1be2d9425434e7eaf35d59c92401c72736a65081b3798d33
  - `Widerface-RetinaFace.caffemodel` d08338a2c207df16a9c566f767fea67fb43ba6fff76ce11e938fe3fabefb9402

## 4. Temuan dari kode MiniFASNet (dibaca langsung)

1. Nama bobot menentukan parameter: V2 skala 2,7 dan V1SE skala 4,0, keduanya input 80x80, kernel konvolusi akhir (5,5).
2. Keluaran 3 kelas; hasil softmax dua model dijumlah lalu dibagi 2; kode menganggap indeks 1 = wajah asli. Makna indeks 0 dan 2 tidak dijelaskan di kode (belum terverifikasi).
3. `check_image` menolak gambar yang rasio lebar/tinggi tidak tepat 3:4. Aplikasi HRMS harus menangkap atau memotong ke 3:4.
4. Model dimuat ulang di setiap `predict`; harus dipisah agar latensi inferensi terukur benar (perubahan kode = modifikasi yang dicatat).
5. Detektor Caffe memilih satu kotak dengan skor tertinggi, tidak menangani kasus tanpa wajah atau banyak wajah.
6. Risiko belum diuji: `cv2.dnn.readNetFromCaffe` di OpenCV 5; `F.softmax` tanpa `dim` di kode asli.
7. `requirements.txt` asli (torch 1.2.0, numpy 1.17.0, opencv 4.2.0.34, Pillow 7.1.2) tidak dipakai; versi modern dipakai dan ketidakcocokan dicatat sebagai modifikasi.
8. Klaim README (belum diukur): MiniFASNetV2 0,081 GFLOPs dan 0,435 juta parameter.

## 5. Status dan langkah berikutnya

- Selesai: Fase 0, Fase 1 (audit awal), sebagian besar Fase 2 (struktur, venv, dependensi tahap 1 dan 2, unduh dan verifikasi AuraFace dan MiniFASNet).
- Skrip `scripts/smoke_minifasnet.py` sudah diberikan (memuat dua bobot dengan `weights_only=True`, data acak) tetapi **hasilnya belum dikirim**. Langkah pertama di percakapan baru: minta output skrip itu dan isi `src/data_io/transform.py`, `src/generate_patches.py`, dan awal `src/model_lib/MiniFASNet.py` (belum dibaca).
- Setelah smoke test: pilih dan audit detektor wajah berlisensi bersih; audit teknis dan unduh model #2, #3, #4, #6 satu per satu (verifikasi sumber resmi bobot, ukuran, checksum; belum dilakukan); Fase 3 (dataset dan protokol evaluasi, hitung ukuran dataset dan ruang disk dulu); Fase 4 dan seterusnya sesuai master prompt.
- Koreksi pada `audit/model-audit.md` yang belum diterapkan: tanggal commit terakhir MiniFASNet adalah 2020-08-05 (bukan Oktober 2023); keputusan nomor 1 diganti "Keenam kandidat diuji penuh"; lokasi proyek C:\dev\model-research-face.

## 6. Aturan kerja (ringkasan master prompt)

- Jangan mengarang hasil; bedakan fakta terverifikasi, klaim sumber, hasil eksperimen aktual, asumsi.
- Satu langkah kecil per giliran, tunggu output nyata; jangan menganggap perintah berhasil.
- Semua perintah untuk Git Bash di Windows 11. Format respons: A posisi, B penjelasan, C langkah, D verifikasi, E pencatatan, F gerbang.
- Tidak mengunggah foto biometrik pribadi ke percakapan; smoke test memakai data acak.
- Threshold hanya ditentukan dari data dev, bukan data test.
- Catat setiap modifikasi kode dan versi di `logs/experiment-log.md`.

## 7. Kesalahan yang sudah terjadi (agar tidak diulang)

- Clone MiniFASNet gagal di Windows karena path `saved_logs/.../Jul08_12-51-18 /...` (spasi di akhir nama folder). Diagnosis awal "file dihapus" salah; sparse-checkout dan `git archive HEAD` juga gagal. Yang berhasil: `git archive "HEAD:<subfolder>"` per subfolder plus `git show "HEAD:<file>"` untuk file akar; folder `images/` dan `saved_logs/` tidak diekstrak.
- Jangan menyatakan klaim README sebagai hasil terukur. Jangan memakai README turunan sebagai bukti lisensi bila sumber resmi tersedia.
