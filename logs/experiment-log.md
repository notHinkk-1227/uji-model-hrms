# Experiment Log

## 2026-11-02 - Fase 0-2 awal
- Target: model liveness + face recognition untuk fitur absensi HRMS mobile (produksi).
- Mesin: i7-11800H, RAM 15,7 GB, RTX 3060 Laptop, Windows 11, Git Bash.
- Proyek: C:\dev\model-research-face (git init selesai).
- Python 3.12.10 dipasang lewat winget (scope user); Python 3.14.7 tetap ada.
- Venv: .venv (Python 3.12). Belum ada library ML.
- Disk C: sisa 25 GB (95% terpakai); lokasi dataset dibuat configurable.

## 2026-11-02 - Keputusan ruang lingkup
- Keenam model diuji dan dibandingkan penuh dengan protokol yang sama (permintaan peneliti; atasan mengizinkan penggunaan model open-source).
- Status lisensi di audit/model-audit.md tidak diubah. Jika model berlabel riset terpilih, minta konfirmasi tertulis sebelum produksi.

## 2026-11-02 - Unduh kode dan bobot kandidat lolos audit
- MiniFASNet: clone dangkal repo resmi, commit <ISI HASH DARI rev-parse>. Bobot dari resources/anti_spoof_models. Checksum lokal di logs/checksums-silentface.txt.
- AuraFace: hanya glintr100.onnx + LICENSE.md + README.md. SHA-256 cocok dengan nilai resmi Hugging Face (a7933ea5...5c60). SCRFD dan model lain sengaja tidak diunduh.

## 2026-11-02 - Verifikasi unduhan
- AuraFace: glintr100.onnx = 260694151 byte, SHA-256 a7933ea5330113b01c9b60351d8f4c33003f145d8470ac5f0e52ee2effe25c60 (cocok dengan nilai resmi Hugging Face). LICENSE.md dan README.md terunduh. SCRFD dan model lain sengaja tidak diunduh.
- MiniFASNet: clone gagal karena folder tujuan sudah ada (bukan dibuat dalam sesi ini). Repo ada di commit b6d5f04ad78778917853b25c778acef6d5626d15 (7,1 MB) tetapi folder resources/ tidak ada. Asal repo dan penyebab sedang didiagnosis; belum dipakai.

## 2026-11-02 - Koreksi metode ekstraksi MiniFASNet
- git archive HEAD gagal: Git tetap membuka seluruh pohon commit dan menolak path 'saved_logs/.../Jul08_12-51-18 /...' (spasi di akhir nama).
- Solusi: git archive "HEAD:<subfolder>" per subfolder (resources, src, datasets) + git show "HEAD:<file>" untuk file akar. Folder images/ dan saved_logs/ sengaja dilewati.
- Data Git asli: repositories/_git-Silent-Face-Anti-Spoofing (HEAD b6d5f04ad78778917853b25c778acef6d5626d15). Checksum: logs/checksums-silentface.txt.

## 2026-11-02 - MiniFASNet terekstrak, dependensi tahap 1
- MiniFASNet berhasil diekstrak (commit b6d5f04a...): 2 bobot .pth + detektor Caffe. Checksum di logs/checksums-silentface.txt. LICENSE terverifikasi Apache 2.0 (head -n 3).
- requirements.txt asli (torch 1.2.0, numpy 1.17.0, opencv 4.2.0.34, Pillow 7.1.2) tidak dipakai; versi modern akan dipasang dan ketidakcocokan kode dicatat sebagai modifikasi.
- Tahap 1 dependensi: numpy, onnxruntime, opencv-python-headless, pillow, easydict, tqdm (lihat configs/requirements-stage1.txt).
- Smoke test AuraFace (data acak, bukan pengukuran): input data [None,3,112,112] float; output 1333 [1,512] float; run acak: shape (1,512), norma L2 9,71 (bukan pengukuran kualitas).

## 2026-11-02 - Dependensi tahap 2 dan tinjauan kode MiniFASNet
- torch 2.15.0+cpu, torchvision 0.29.2+cpu (Python 3.12, CUDA tidak aktif). Daftar versi: configs/requirements-stage2.txt. Disk C: sisa 23 GB.
- Temuan kode: (1) skala/ukuran dari nama bobot: V2 skala 2,7, V1SE skala 4,0, input 80x80, kernel (5,5); (2) output 3 kelas, dijumlah dari 2 model, indeks 1 = asli menurut kode, makna indeks 0 dan 2 belum terverifikasi; (3) gambar harus tepat rasio 3:4; (4) model dimuat ulang tiap predict (perlu dipisah untuk ukur latensi); (5) detektor Caffe memilih satu kotak, tidak menangani tanpa-wajah; (6) risiko cv2.dnn Caffe di OpenCV 5 belum diuji.
- Smoke test MiniFASNet (data acak, bukan pengukuran): <ISI DARI OUTPUT>

## 2026-11-02 - Smoke test MiniFASNet dan tinjauan kode
- Smoke test (data acak, BUKAN pengukuran kualitas): torch 2.15.0+cpu, bobot dimuat dengan weights_only=True, load_state_dict lolos.
  - 2.7_80x80_MiniFASNetV2.pth: skala 2,7, input 80x80, kernel (5,5), 434560 parameter, output (1,3), jumlah prob 1,0.
  - 4_0_0_80x80_MiniFASNetV1SE.pth: skala 4,0, input 80x80, kernel (5,5), 433586 parameter, output (1,3), jumlah prob 1,0.
- Parameter V2 konsisten dengan klaim README (~0,435 juta).
- Kode: inferensi hanya Compose([ToTensor()]) tanpa Normalize; gambar dibaca cv2.imread (kemungkinan BGR, belum dipastikan); crop: kotak diperbesar sebesar scale, digeser agar masuk gambar, resize ke 80x80 tanpa menjaga rasio.
- Temuan awal (belum diverifikasi sumber primer): asumsi saya di skrip smoke test bahwa input berskala 0-255 belum terbukti (functional.to_tensor belum dibaca).
- Detektor: README resmi YuNet (OpenCV Zoo) menyatakan MIT; data latih/evaluasi WIDER Face dilabeli CC-BY-NC-ND-4.0 oleh kartu pihak ketiga (sumber sekunder). Lisensi WIDER Face di situs resmi belum diperiksa.

## 2026-11-02 - Koreksi: spesifikasi input MiniFASNet terverifikasi
- functional.to_tensor (jalur numpy.ndarray): transpose HWC->CHW lalu .float(); pembagian 255 dinonaktifkan di kode asli (komentar "modify by zkx"). Input berskala 0-255, TANPA konversi urutan warna (tetap BGR dari cv2.imread). Docstring ToTensor (0-1) usang.
- Asumsi skala 0-255 dan BGR pada skrip smoke test terbukti benar; skrip tidak perlu diubah.
- Implikasi integrasi: gambar dari kamera mobile (RGB) harus dikonversi ke BGR dan tidak dinormalisasi sebelum liveness.
- Detektor: eksperimen memakai satu detektor yang sama untuk semua model (usulan: YuNet MIT, berkas resmi OpenCV Zoo); status lisensi data (WIDER Face) dicatat sebagai risiko. Detektor produksi ditentukan kemudian (kandidat: BlazeFace, Apache-2.0, data latih Google proprietary; model card Google belum diverifikasi langsung).

## 2026-11-02 - YuNet diunduh, Fase 2 selesai
- YuNet face_detection_yunet_2023mar.onnx: 232589 byte, SHA-256 8f2383e4dd3cfbb4553ea8718107fc0423210dc964f9f4280604804ed2552fa4 (cocok dengan nilai mirror). Dipakai sebagai detektor eksperimen untuk semua model.
- audit/model-audit-v2.md menggantikan model-audit.md (koreksi: commit MiniFASNet 2020-08-05; tabel detektor; keputusan baru).
- Fase 2 selesai. Berikutnya Fase 3 (dataset dan protokol).

## 2026-11-02 - Protokol evaluasi v1.0 dibekukan
- Peneliti menyetujui protokol v0.2; ditambah definisi pencahayaan dan pengaturan kamera menjadi v1.0 (reports/protokol-evaluasi-v1.0.md).
- Desain: ponsel masing-masing relawan (kamera depan) sebagai inti; jangkar (ponsel rekan) dan uji stres (kamera depan rusak) opsional.
- Pencahayaan diatur secara fisik, bukan diedit. Pengambilan data baru dimulai setelah formulir persetujuan ditandatangani semua relawan.

## 2026-11-02 - SFace diunduh dan smoke test
- Sumber: huggingface.co/opencv/face_recognition_sface (resmi OpenCV). Berkas face_recognition_sface_2021dec.onnx: 38696353 byte, SHA-256 0ba9fbfa01b5270c96627c4ef784da859931e02f04419c829e83484087c34e79 (cocok dengan nilai mirror, sumber sekunder). LICENSE Apache 2.0 terunduh. Varian int8 tidak dipakai.
- Smoke test (data acak, BUKAN pengukuran): input [1,3,112,112] float, output fc1 [1,128] float, norma L2 5,09. Dimensi embedding 128.
- ONNX Runtime memberi peringatan bahwa initializer muncul di graph inputs (model hasil ekspor lama); tidak memengaruhi kebenaran, mungkin memengaruhi latensi (perlu dicatat saat benchmark).

## 2026-11-02 - buffalo_l diunduh; CDCN tidak dilanjutkan
- buffalo_l.zip dari GitHub release v0.7 (URL dari dokumentasi sekunder): 288621354 byte, SHA-256 80ffe37d8a5940d59a7384c201a2a38d4741f2f3c51eef46ebb28218a7b0ca2f (tanpa checksum resmi). Isi zip cocok dengan dokumentasi (5 berkas onnx). Hanya w600k_r50.onnx diekstrak: 174383860 byte, SHA-256 4c06341c33c2ca1f86781dab0e829f88ad5b64be9fba56e56bc9ebdefc619e43. Bobot nonkomersial, hanya acuan riset.
- Smoke test w600k_r50 (data acak, bukan pengukuran): input ['None',3,112,112], output [1,512]. Norma 1837 pada input 0-255 menunjukkan model mengharapkan input ternormalisasi (dugaan, belum diverifikasi dari kode resmi).
- Konfirmasi sekunder: halaman konversi ONNX pihak ketiga mencantumkan SHA-256 2.7_80x80_MiniFASNetV2.pth = a5eb02e1...bec0, sama dengan berkas lokal. Halaman itu juga mengklaim urutan keluaran [live, print, replay] yang bertentangan dengan kode asli (indeks 1 = asli); makna indeks belum terverifikasi.
- CDCN: TIDAK DILANJUTKAN. Tidak ada bobot siap pakai, kode memakai data OULU-NPU olahan (.dat), lisensi hanya riset. Akses OULU-NPU juga dilaporkan bermasalah (isu GitHub 2022; status kini belum diverifikasi).
- Usulan pengganti: facenox/face-antispoof-onnx (Apache-2.0 kode; MiniFAS; 128x128 RGB; diuji pada CelebA-Spoof; data latih belum dipastikan). Menunggu persetujuan peneliti dan audit data latih.

## 2026-11-02 - Penggantian CDCN diterapkan ke semua dokumen
- Peneliti menyetujui penggantian CDCN dengan face-antispoof-onnx (facenox) sebagai kandidat liveness ketiga.
- Diperbarui: audit/model-audit-v3.md, audit/license-evidence-v2.md, reports/handover-penelitian-v2.md, laporan baseline di Claude Docs (catatan revisi + 10 penyesuaian). Versi lama dipindahkan ke audit/arsip/.
- Status face-antispoof-onnx: TERTAHAN-LISENSI (sementara); data latih diduga CelebA-Spoof, menunggu pembacaan docs/DATA_PREPARATION.md.
