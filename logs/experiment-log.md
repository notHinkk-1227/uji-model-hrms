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

## 2026-11-03 - Pengarsipan dokumen dan cadangan
- reports/handover-penelitian.md dan protokol-evaluasi-v0.2.md diarsipkan ke reports/arsip/. Pencarian "CDCN" di dokumen aktif hanya menemukan penyebutan yang menjelaskan alasan CDCN dikeluarkan.
- Cadangan riwayat Git: /d/backup-penelitian/model-research-face.bundle (30205 byte; tanpa bobot dan data). Ulangi setiap selesai satu fase.
- Dua salah ketik (spasi hilang) diperbaiki.

## 2026-11-03 - face-antispoof-onnx di-clone
- Clone dangkal https://github.com/facenox/face-antispoof-onnx ke repositories/face-antispoof-onnx. HEAD 2f8dd93dd0fd9d120f08e83d9020719f67ffdb68, commit terakhir 2026-10-15. Ukuran 789 MB (didominasi folder models/checkpoints; tidak dipakai).
- LICENSE Apache-2.0 (11548 byte). README mengkredit Minivision Silent-Face-Anti-Spoofing (Apache-2.0) sebagai dasar.
- Bobot: models/best/98.20/best_model.onnx 1912594 byte; best_model.pth 2965272 byte; best_model_quantized.onnx 626197 byte. models/detector.onnx 232589 byte (ukuran sama dengan YuNet 2023mar; hash diverifikasi di langkah berikutnya).
- Data latih: TIDAK dinyatakan di README, METRICS, PREVIOUS_RESULTS, DATA_PREPARATION (grep "celeba|dataset|license"). Yang dinyatakan hanya: diuji pada CelebA Spoof (70k+ sampel). Dugaan sebelumnya ("sangat mungkin CelebA-Spoof") belum terbukti maupun terbantah.

## 2026-11-03 - face-antispoof-onnx: checksum dan spesifikasi crop
- SHA-256 (tanpa pembanding resmi): models/best/98.20/best_model.onnx af2381b88f38769222ed93379e12444e2a50814575de1c46170de570c55a42b6; best_model.pth 290ad61b0ece12a4afef5186076415b05ef07f19d9e103db89875af05e795c02; best_model_quantized.onnx fde20585635cae62ed1d41796f76b6f8bc4b92cd91ec1cf0f1bc6485d2d587a9.
- models/detector.onnx identik (SHA-256 8f2383e4...2fa4) dengan YuNet 2023mar yang dipakai eksperimen.
- Smoke test (data acak): input [batch,3,128,128], output [batch,2]. Skala/urutan warna belum dipastikan (baca src/inference/preprocess.py).
- Crop (docs/DATA_PREPARATION.md): kotak wajah 1,5x, dipersegikan (sisi terpanjang), padding BORDER_REFLECT_101, resize 128x128. Batasan (docs/LIMITATIONS.md): cahaya redup/latar kuat bermasalah, wajah sumber >= ~64x64, frontal +/-30 derajat, tidak dilatih untuk topeng 3D; ambang bawaan 0,5.
- Data latih bobot tetap tidak dinyatakan; format data (image_BB.txt, metas/labels/*.json) tampak mengikuti CelebA-Spoof (pengetahuan peneliti/asisten, bukan kutipan dokumen). Status: TERTAHAN-LISENSI (sementara). Rencana: tanya maintainer lewat isu GitHub.

## 2026-11-03 - face-antispoof-onnx: preprocessing dari kode
- preprocess.py: crop persegi sisi-terpanjang x1,5 (padding BORDER_REFLECT_101), resize 128x128 (INTER_AREA bila mengecil, LANCZOS4 bila membesar), nilai /255 (rentang 0-1), CHW float32, TANPA mean/std. Tidak ada konversi warna di preprocess(); urutan warna (README: RGB) harus dipastikan dari system.py/demo.py.
- crop() mengharapkan bbox (x1,y1,x2,y2) (w = w - x, h = h - y); detektor mengembalikan x,y,width,height; konversi di system.py belum dilihat.
- inference.py: keluaran logit [real, spoof] (indeks 0 = real); real jika (real - spoof) >= threshold (selisih logit, bukan probabilitas).
- detection/face.py: cv2.FaceDetectorYN (conf 0,8; NMS 0,3), membuang wajah dengan jarak ke tepi < 5 px atau ukuran < 60 px.
- metrics.json (klaim repo): matriks konfusi [[31760,789],[493,38296]] pada 71338 sampel; hasil hitung asisten: BPCER ~2,42%, APCER ~1,27%, ACER ~1,85% (belum diukur sendiri; tidak sebanding langsung dengan ACER 3,81% anti-spoof-mn3). Kecepatan 0,13 ms diukur di CUDA. Parameter 695971.
- Perbedaan dengan MiniFASNet: skala 0-1 vs 0-255; crop persegi 1,5x vs skala 2,7/4,0 tanpa dipersegikan; keluaran 2 kelas vs 3 kelas. Skrip evaluasi harus memakai preprocessing terpisah per model.

## 2026-11-03 - face-antispoof-onnx: urutan warna, threshold, OpenCV 5
- demo.py (baris 169 dan 256): frame dikonversi BGR->RGB sebelum diproses, jadi model menerima RGB (berbeda dari MiniFASNet yang BGR).
- demo.py (baris 316-327): --threshold default 0,5 (probabilitas) dikonversi ke selisih logit = ln(p/(1-p)); untuk 0,5 hasilnya 0, jadi real bila logit_real - logit_spoof >= 0. Aturan keputusan utama kita; ROC dilaporkan terpisah.
- system.py hanya berisi info perangkat keras (CPU/GPU/provider); tidak memuat konversi warna atau bbox.
- OpenCV 5.0.0: cv2.FaceDetectorYN ada; YuNet termuat (baru terbukti termuat, belum terbukti mendeteksi wajah). Peringatan: targets (mis. GPU) tidak didukung graph engine baru; tidak berpengaruh untuk CPU.
- Belum pasti: format bbox yang diharapkan crop() (x1,y1,x2,y2 vs x,y,w,h); lihat demo.py dan tests/test_preprocess.py.

## 2026-11-03 - Format bbox pasti; spesifikasi anti-spoof-mn3
- face-antispoof-onnx: demo.py memanggil crop(rgb, (x, y, x+w, y+h), faktor) dan test_preprocess.py memakai (x, y, x2, y2): format bbox crop() = (x1,y1,x2,y2) [terverifikasi]. Detektor di demo menerima gambar RGB; pipeline kita memakai satu deteksi YuNet pada BGR untuk semua model (penyimpangan dicatat).
- anti-spoof-mn3 (dokumen OMZ): model asli RGB 128x128, mean [151.2405,119.5950,107.8395], scale [63.0105,56.4570,55.0035], keluaran probabilitas 2 kelas (0 real, 1 spoof); model terkonversi BGR; crop tidak dijelaskan. OMZ dalam mode pemeliharaan; bobot lewat omz_downloader.
- Lisensi anti-spoof-mn3: artikel dukungan Intel (000102082) menyatakan berbasis repo MIT dan boleh komersial, tidak menyinggung klausul dataset CelebA-Spoof. Pernyataan "bobot dibersihkan" hanya dari forum. Status tetap TERTAHAN-LISENSI.
- Dibuat reports/spesifikasi-preprocessing-v1.md (tabel preprocessing semua model).

## 2026-11-04 - anti-spoof-mn3 diunduh (omz_downloader); ArcFace preprocessing
- Lingkungan terpisah .venv-omz (Python 3.12, openvino-dev 2024.6.0, numpy 1.26.4); .venv utama tidak berubah (numpy 2.5.4, onnxruntime 1.31.1). .venv-omz ditambahkan ke .gitignore.
- omz_downloader --name anti-spoof-mn3 -> models/anti-spoof-mn3/public/anti-spoof-mn3/anti-spoof-mn3.onnx: 12270179 byte, SHA-256 c4c99af04603b62d7e44f6f4daeb33e0daeccc696008c0b1d62f6f5cebbb3262. Tidak ada pesan gagal; checksum OMZ tidak ditampilkan eksplisit. Ukuran konsisten dengan 3,02 juta parameter float32.
- Model asli (bukan IR terkonversi): RGB, normalisasi eksternal (mean/scale dari dokumen OMZ), keluaran 2 kelas (0 real, 1 spoof).
- Keluarga ArcFace (buffalo_l, AuraFace; sumber sekunder: salinan kode arcface_onnx.py insightface): input (x-127,5)/127,5, blobFromImages dengan swapRB=True (BGR->RGB), alignment 5 landmark norm_crop 112x112. Pengecualian: graf dengan node Sub/Mul awal memakai mean 0, std 1 (model MXNet). SFace belum dikonfirmasi.
