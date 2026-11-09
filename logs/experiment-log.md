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

## 2026-11-04 - anti-spoof-mn3 smoke test; SFace preprocessing terverifikasi
- anti-spoof-mn3 smoke test (data acak, BUKAN pengukuran): input actual_input_1 [1,3,128,128]; output output1 [1,2]; keluaran sudah probabilitas (jumlah 1,0); pada derau acak model menghasilkan [0.983, 0.017] (yakin "real"), jadi smoke test hanya bukti model berjalan.
- SFace (kode OpenCV face_recognize.cpp): alignCrop memakai 5 landmark dari kolom 4-13 keluaran YuNet, similarity transform, warpAffine 112x112 INTER_LINEAR; feature memakai blobFromImage(skala 1, mean 0, swapRB=true) -> RGB nilai 0-255 mentah, tanpa normalisasi.
- Keenam model terunduh dan lolos smoke test. reports/spesifikasi-preprocessing-v2.md adalah tabel preprocessing acuan (v1 tidak pernah disimpan ke repo).
- Tersisa: nilai titik templat ArcFace dan norm_crop dari kode resmi insightface; verifikasi empiris pasangan sama/beda identitas.

## 2026-11-04 - Koreksi catatan v1
- Entri sebelumnya menyebut "v1 tidak pernah disimpan ke repo"; ternyata berkas v1 ikut ter-commit (eb78686). v1 kini diarsipkan ke reports/arsip/; v2 adalah acuan.

## 2026-11-04 - Modul 1 dan 2 skrip evaluasi lolos uji bentuk
- scripts/common.py (detektor YuNet bersama), scripts/preprocess_liveness.py (tiga preprocessing liveness), scripts/test_modul1.py.
- Uji pada repositories/face-antispoof-onnx/assets/docs/face.jpg (500x750, gambar dokumentasi repo, bukan data relawan): 1 wajah, bbox (293.9, 73.6, 157.2, 200.9), skor 0.94. Landmark 5 titik masuk akal (mata sejajar y~152-154, hidung y 196.7, sudut mulut y 223-225) dan terletak di dalam bbox.
- Keluaran: MiniFASNet (1,3,80,80) float32 rentang 0-255; face-antispoof-onnx (1,3,128,128) rentang 0-1; anti-spoof-mn3 (1,3,128,128) rentang -2.400 s/d 2.675 (sama dengan batas matematis normalisasi mean/scale). Ini uji bentuk dan rentang, BUKAN uji kualitas dan belum menguji urutan warna.
- Crop anti-spoof-mn3 masih ASUMSI (persegi x1,5 seperti face-antispoof-onnx); belum diverifikasi.

## 2026-11-04 - Koreksi: uji warna lolos
- scripts/test_warna.py (gambar sintetis biru murni): MiniFASNet V2 dan V1SE [255, 0, 0] (BGR, 0-255); face-antispoof-onnx [0, 0, 1] (RGB, 0-1); anti-spoof-mn3 [-2.4002, -2.1183, 2.6755] (RGB, mean/scale). SEMUA OK. Urutan warna dan skala terverifikasi untuk tiga preprocessing liveness (koreksi atas kalimat "belum menguji urutan warna" di entri sebelumnya).

## 2026-11-05 - Modul 3 (infer_liveness.py) lolos uji
- Uji pada face.jpg (gambar dokumentasi repo; BUKAN data relawan dan BUKAN pengukuran kinerja): status ok; MiniFASNet rata-rata p1 = 0.9998 (V2 0.99995; V1SE 0.99972), pred_real 1; face-antispoof-onnx logit_real 4.118, logit_spoof -4.118, diff +8.236, pred_real 1; anti-spoof-mn3 p_real 0.988, pred_real 1. CSV dan .meta.json terbentuk; hash empat berkas bobot di metadata sama dengan logs/checksums-models.txt.
- Catatan interpretasi: satu gambar tidak membedakan indeks 0 dan 2 MiniFASNet; anti-spoof-mn3 sebelumnya juga menjawab "real" 98% untuk derau acak, jadi kesepakatan tiga model bukan bukti kinerja.
- Perbaikan skrip: parameter threads pada LivenessModels; metadata mencatat skrip_belum_di_commit (hash commit tidak mewakili kode bila folder scripts punya perubahan yang belum di-commit).
- Modul 4 (benchmark_latency.py) ditulis; butuh psutil.

## 2026-11-05 - Benchmark latensi awal (laptop pengembangan, CPU)
- Gambar face.jpg 500x750, 100 ulangan, warm-up 10; median (ms) 1 thread / 4 thread: YuNet 31.4 / 16.6; MiniFASNet V2 inferensi 8.1 / 10.1; V1SE 7.8 / 10.9; ansambel total 15.2 / 21.4; face-antispoof-onnx total 6.7 / 4.6; anti-spoof-mn3 total 5.6 / 4.3. Memori RSS: memuat model menambah ~42-46 MB (dasar ~232 MB, puncak ~326-332 MB; kasar).
- Derau: pada 1 thread ansambel_total (15.2) < ansambel_inferensi (17.5) dan p95 V1SE 14.0 vs median 7.8 -> variasi antar pengukuran ~10-15%; selisih lebih kecil dari ~15-20% belum bermakna.
- Multithread: ONNX Runtime dan YuNet lebih cepat dengan 4 thread; MiniFASNet (PyTorch) lebih lambat.
- Kondisi laptop (daya, mode performa) tidak dicatat; angka bukan angka server produksi. Resolusi gambar yang dikirim aplikasi HRMS belum diketahui.

## 2026-11-05 - Koreksi benchmark latensi; temuan detektor pada gambar besar
- Tiga ulangan (1 thread, 100 ulangan, face.jpg 500x750), median ms: YuNet 23.75/22.84/22.11; MiniFASNet V2 inferensi 5.58/5.12/4.90; V1SE 5.55/5.57/5.32; ansambel inferensi 11.01/10.90/10.46, ansambel total 10.94/10.60/10.58; face-antispoof-onnx total 4.72/4.72/4.75; anti-spoof-mn3 total 3.34/3.35/3.22.
- KOREKSI: perkiraan derau "10-15%" terlalu kecil. Variasi dalam satu sesi ~2-10%, tetapi antar-sesi angka bergeser 35-60% (benchmark pertama jauh lebih lambat; kondisi laptop tidak diketahui). Perbandingan antarmodel hanya valid dalam satu sesi dengan kondisi tercatat. Anomali "total < inferensi" tidak muncul lagi (artefak gangguan sesaat).
- Urutan kecepatan stabil di dua sesi: anti-spoof-mn3 < face-antispoof-onnx < ansambel MiniFASNet (sekitar 2-3x). Detektor (22 ms) lebih mahal daripada model liveness mana pun.
- TEMUAN: YuNet tidak menemukan wajah pada gambar 4032x2688 (face.jpg dibesarkan 5.4x, rasio sama); pada ukuran asli 750x500 skor 0.94. Penyebab belum diketahui (wajah terlalu besar bagi detektor atau pembesaran digital yang buram). Dugaan: deteksi harus dijalankan pada gambar diperkecil lalu koordinat dikembalikan ke gambar asli. Diuji dengan scripts/test_resolusi.py.

## 2026-11-05 - Detektor pada gambar besar terjelaskan; amandemen protokol
- Ambang 0,05 pada gambar 3000 dan 4032 px: 23 dan 39 deteksi, skor tertinggi 0.734 dan 0.638 dengan lebar kotak ~511 dan ~509 px (lebar wajah sebenarnya 621 dan 835): detektor tidak dapat menghasilkan kotak > ~510 px; kegagalan = skor di bawah ambang 0,8.
- Setelah perbaikan common.py (deteksi pada salinan <= 640 px): semua ukuran 375-4032 mendeteksi 1 wajah, skor 0.94, waktu 3.6-14.8 ms (sebelumnya sampai 512 ms). test_modul1 dan test_warna lolos. Kotak pada face.jpg bergeser ~1-3% (295.5, 72.5, 155.3, 204.3 vs 293.9, 73.6, 157.2, 200.9).
- Benchmark dijalankan dengan charger tercolok dan mode Turbo. Penyebab benchmark pertama yang lebih lambat tetap tidak diketahui.
- Pengumpulan data relawan dilaporkan sudah dilakukan; kelas replay dan uji stres tidak dikumpulkan (lihat reports/amandemen-protokol-1.md). Konfirmasi formulir persetujuan TERTANDATANGANI semua relawan menunggu jawaban peneliti; analisis model pada data relawan ditahan sampai itu dikonfirmasi.
- Resolusi unggahan aplikasi HRMS belum ditentukan: skenario 640, 1280, penuh; opsi --max_side ditambahkan pada infer_liveness.py.

## 2026-11-05 - Data S01 dirapikan
- Foto S01 dipindahkan dari datasets/_masuk dengan scripts/rename_foto.py (log: datasets/rename_log.csv, tidak ikut Git). Jumlah dan ukuran per kelas: lihat output inventaris_data.py (diisi peneliti).

## 2026-11-08 - Persetujuan relawan; amandemen 2 (pemotongan 3:4); temuan ukuran per kelas
- Dikerjakan di salinan uji D:\dev\model-research-face-cc (uji cara kerja Claude Code); repo resmi tetap C:\dev\model-research-face. Bila dipakai, entri ini dipindahkan ke repo resmi.
- Peneliti mengonfirmasi formulir persetujuan keempat relawan (S01-S04) SUDAH ditandatangani. Gerbang untuk menjalankan model pada data relawan terbuka mulai entri ini.
- Peneliti mengonfirmasi cara pengambilan foto serangan sesuai protokol (kamera depan ponsel relawan).
- Inventaris (inventaris.csv, hanya angka; tidak ada gambar dibuka, tidak ada model dijalankan): 30 dari 160 foto bukan 3:4, semuanya serangan (S02 print 10, 2296x4080; S03 print 10 + screen 10, 1884x4080). Ukuran foto real berbeda dari foto serangan pada keempat relawan; S01 real EXIF 5, serangan 6/1. Penyebab [T].
- Keputusan peneliti: pemotongan tengah ke tepat 3:4 untuk semua model sebelum pipeline; tanpa analisis "apa adanya". Rincian: reports/amandemen-protokol-2.md. Belum diimplementasikan di kode.
- Keputusan sementara "B" (foto enrollment identik dikecualikan dari probe) disebut di CLAUDE.md tetapi belum punya angka di log; output periksa_data.py belum ada di salinan ini. Dicatat saat output tersedia.

## 2026-11-08 - Pemotongan 3:4 diimplementasikan dan lolos uji
- scripts/common.py: crop_to_3x4 (k = min(w//3, h//4), ukuran (3k, 4k), offset di tengah, hanya slicing). DETECTOR_CONFIG mencatat "pemotongan_rasio" (ikut ke .meta.json).
- scripts/infer_liveness.py: score_original = potong 3:4 -> limit_resolution -> score_image; kolom baru crop34_x, crop34_y, crop34_w, crop34_h (koordinat pada gambar asli). bbox_* tetap pada gambar yang diproses (setelah potong dan batas resolusi).
- scripts/benchmark_latency.py: gambar dipotong 3:4 sebelum diukur (sama dengan pipeline).
- scripts/test_potong34.py (gambar sintetis, tanpa data relawan): 10/10 ukuran sama dengan tabel amandemen-protokol-2, rasio tepat 3:4 juga setelah batas 640 (480x640) dan 1280 (960x1280), offset di tengah, piksel tidak berubah. test_warna SEMUA OK; test_modul1 semua OK.
- face.jpg ternyata 750x500 (lebar x tinggi, lanskap); entri lama menulis "500x750" (tinggi x lebar). Setelah dipotong 375x500 (offset x 187): 1 wajah, skor 0,940 -> 0,939.
- KOREKSI KRITERIA UJI (terbuka): kriteria awal "posisi kotak bergeser <= 3 px" GAGAL (3,9 px). Diagnosis: pada skala deteksi yang sama pun kotak YuNet berbeda (293.9, 73.6, 157.2, 200.9) vs (299.1, 76.5, 152.8, 195.0) setelah dikembalikan dengan offset; YuNet tidak identik bila latar sekitar wajah dipotong. Pemetaan offset terbukti benar oleh uji sintetis. Kriteria diganti IoU kotak >= 0,9; hasil IoU 0,926 (lolos). Ini uji kode pada gambar dokumentasi, bukan data evaluasi.
- Implikasi: pemotongan 3:4 dapat menggeser kotak deteksi beberapa persen walau wajah tidak terpotong; berlaku sama untuk semua model.
- infer_liveness --image face.jpg (penuh dan --max_side 640): status ok, kolom crop34_* terisi. Skor sedikit berubah dari 2026-11-05 (facenox diff 8,236 -> 8,095; mn3 p_real 0,988 -> 0,992) karena kotak berubah; BUKAN bukti kinerja.
- benchmark_latency.py berjalan (5 ulangan, hanya cek tidak error; angka tidak dipakai).

## 2026-11-08 - periksa_data.py: duplikat enrollment-probe
- Dijalankan di salinan uji (python scripts/periksa_data.py, exit 0). Hanya hash SHA-256 berkas dan inventaris.csv; tidak ada gambar dibuka, tidak ada model dijalankan. Daftar: datasets/recognition/internal/duplikat_enrollment.csv (tidak ikut Git).
- 18 dari 20 foto enrollment identik (byte demi byte) dengan foto raw: S01 5/5, S02 5/5, S03 5/5, S04 3/5. Pemetaan 1:1 (18 berkas raw unik); semuanya kelas real. Tidak ada berkas identik di dalam raw sendiri.
- Berkas raw yang identik per cahaya: terang 3/3/3/2, redup 2/2/2/1 (S01/S02/S03/S04). Penyimpangan: 7 foto enrollment berasal dari kondisi redup, padahal protokol v1.0 bagian 5 meminta enrollment frontal terang dan sesi berbeda.
- Bila keputusan sementara "B" (foto identik dikecualikan dari probe) dipakai: probe real tersisa 62 dari 80 (S01 15, S02 15, S03 15, S04 17; terang 29, redup 33). Perkiraan pasangan: genuine 62, impostor 62 x 3 = 186; batas atas FAR tanpa kesalahan (aturan 3/N) sekitar 1,6%.
- Hash hanya menangkap salinan persis; foto yang hampir sama (mis. jepretan beruntun) tidak terdeteksi [T].
- Rasio dan orientasi per relawan sama dengan entri sebelumnya (30 bukan 3:4: S02 print 10, S03 print 10 + screen 10).
- scripts/periksa_data.py di-commit (versi yang menghasilkan angka ini).

## 2026-11-08 - Keputusan "B" final (amandemen 3)
- Peneliti memutuskan enrollment dipakai apa adanya (tidak diambil ulang); 18 foto raw yang identik dengan enrollment dikeluarkan dari probe. Alasan peneliti: foto berperan sebagai pendaftaran sehingga dapat diterima. Diputuskan sebelum model pengenalan dijalankan.
- Rincian dan keterbatasan (sesi sama, sebagian redup, hash hanya salinan persis): reports/amandemen-protokol-3.md. Probe 62, genuine 62, impostor 186, batas FAR sekitar 1,6%.
- CLAUDE.md dan PRD diperbarui (status langkah 1, angka batas FAR 1,7% -> 1,6%).

## 2026-11-08 - manifest.csv 16 kolom dibuat
- scripts/buat_manifest.py (hanya membaca nama berkas) -> datasets/liveness/internal/manifest.csv (tidak ikut Git): 160 baris, 16 kolom, header sama dengan header lama (sebelumnya hanya header). Semua jalur root/subject/device_code/filename ada; tidak ada sel kosong. Per relawan: real 10+10, print 5+5, screen 5+5 (terang+redup).
- Keterangan peneliti: semua pengaturan diatur sesuai protokol tetapi detailnya tidak dicatat; semua foto diambil pada hari yang sama; model ponsel dan OS belum ditanyakan.
- Maka: device_model = inisial samaran HP-S01..HP-S04; os = tidak_dicatat; mirror_setting, lux_catatan, night_mode, screen_brightness (screen) = sesuai_protokol_tidak_dicatat; attack_display = cetak_tidak_dicatat / layar_tidak_dicatat; session = sesi-1; pose = frontal (protokol).
- Keterbatasan: tanpa model ponsel, OS, lux, dan jenis layar, hasil tidak dapat dikaitkan dengan karakteristik perangkat atau penampil serangan; satu relawan = satu perangkat sehingga pengaruh orang dan ponsel tidak terpisahkan (protokol bagian 2).

## 2026-11-08 - Modul 5 (metrics.py) lolos uji data tiruan
- scripts/metrics.py: APCER per jenis serangan, BPCER, ACER (APCER terburuk + BPCER)/2, confusion, AUC Mann-Whitney, FAR/FRR (diterima bila skor >= threshold), Clopper-Pearson eksak (bisection pada CDF binomial eksak, log-gamma), batas atas tanpa kesalahan (eksak dan 3/N), McNemar eksak, threshold EER, lipatan LOSO. Hanya numpy + pustaka standar; tidak ada paket baru (keputusan peneliti: tanpa scipy).
- scripts/test_metrics.py: 32/32 lolos. Harapan dihitung terpisah dari kode (hitung tangan, rumus tertutup CP untuk 0/n dan n/n, definisi ekor binomial dengan math.comb untuk 5/20). CP 5/20 = 0,0866-0,4910 (sama dengan nilai tabel terbitan yang diingat asisten [S]). Uji LOSO: subjek uji tidak pernah di latih; threshold tidak berubah bila skor data uji diubah ekstrem.
- Dua kegagalan pada putaran pertama adalah kesalahan skrip uji, bukan metrics.py: (1) harapan McNemar b=1,c=9 salah hitung (1+9 seharusnya C(10,0)+C(10,1)=1+10; kode memberi 22/1024 = 0,021484, benar); (2) fungsi pembanding mencoba mengurangkan string. Keduanya diperbaiki di test_metrics.py; metrics.py tidak diubah.
- Belum diputuskan (perlu sebelum evaluasi): aturan threshold pengenalan dari lipatan latih; perlakuan sampel gagal deteksi dalam metrik.

## 2026-11-08 - Amandemen 4: aturan threshold dan perlakuan gagal deteksi
- Peneliti menyetujui (sebelum skor apa pun dilihat): (1) threshold pengenalan = EER pada lipatan latih LOSO; (2) liveness: aturan bawaan sebagai utama, EER lipatan latih + AUC sebagai tambahan; (3) gagal deteksi/gagal proses dihitung "ditolak" dan dilaporkan terpisah. Rincian: reports/amandemen-protokol-4.md.
- Diperjelas saat penulisan: pasangan latih hanya melibatkan relawan latih sebagai probe DAN sebagai identitas yang diklaim (enrollment relawan uji tidak dipakai untuk threshold). Akibatnya lipatan latih hanya sekitar 90 pasangan impostor (koreksi atas perkiraan "sekitar 140" yang diucapkan asisten sebelumnya di percakapan).
- Masih terbuka: cara menggabungkan 5 foto enrollment menjadi skor pasangan.

## 2026-11-08 - Modul pengenalan wajah (recognition.py) lolos uji
- Izin peneliti untuk membaca kode resmi insightface. Berkas diambil dengan curl ke scratchpad (bukan ke proyek), terkunci pada commit ffa12d315041c0505b077c7ff057ca914bb8dc7e (commit terakhir face_align.py, 2022-12-17): face_align.py SHA-256 a8b34ddd...d922; arcface_onnx.py SHA-256 89041694...81a9. Templat dan aturan normalisasi kini [V] (sebelumnya [S]). Tidak ada paket dipasang, tidak ada bobot diunduh.
- skimage dan onnx tidak terpasang (tidak dipasang, aturan 7). Pengganti: (1) similarity_umeyama (numpy) untuk SimilarityTransform; (2) scripts/onnx_nodes.py, pembaca protobuf minimal untuk nama node.
- onnx_nodes: 8 node pertama glintr100 dan w600k_r50 = Conv, PRelu, BatchNormalization, Conv, PRelu, Conv, Conv, Add (tanpa Sub/Mul) -> mean = std = 127,5 menurut aturan insightface.
- scripts/recognition.py: align_arcface (Umeyama + warpAffine 112x112), embedding ArcFace via blobFromImages(1/127,5, mean 127,5, swapRB=True), SFace via cv2.FaceRecognizerSF (alignCrop + feature), L2-normalize, templat = rata-rata embedding ternormalisasi lalu L2 (keputusan peneliti), cosine.
- scripts/test_pengenalan.py: 11/11 lolos. Umeyama memulihkan transformasi eksak (galat 5,7e-14) dan optimum kuadrat terkecil (0/2000 gangguan lebih baik); face.jpg (setelah potong 3:4): urutan landmark sesuai templat, RMS landmark ke templat 2,68 px; dimensi 512/512/128, norma 1, deterministik.
- Informatif, identitas sama (face.jpg diubah; BUKAN pengukuran kinerja): diperkecil 0,5x auraface 0,925 / buffalo_l 0,973 / sface 0,942; JPEG 60: 0,956 / 0,977 / 0,985; dicerminkan: 0,851 / 0,951 / 0,959. Skala cosine berbeda antarmodel, jadi angka ini tidak dapat dibandingkan langsung antarmodel.
- Keterbatasan uji: "identitas berbeda" tidak dapat diuji tanpa wajah kedua yang boleh dipakai (aturan 1).
- Dokumen: spesifikasi-preprocessing-v2.md mendapat bagian "Pembaruan 8 November 2026" (tabel lama tidak diubah); CLAUDE.md dan PRD (K8) diperbarui.

## 2026-11-08 - Modul 6 (evaluasi.py) lolos uji data palsu
- scripts/evaluasi.py, tiga sub-perintah: liveness (metrik dari CSV skor infer_liveness + manifest), embed (embedding probe dan enrollment, tiga model, satu skenario resolusi, ke .npz), recognition (pasangan, templat rata-rata, threshold EER LOSO, FAR/FRR). Aturan sesuai amandemen 2-4: gagal = ditolak (skor -inf untuk AUC), sampel gagal tidak ikut menentukan threshold, pasangan latih hanya relawan latih sebagai probe dan klaim, sampel manifest tanpa skor menghentikan proses.
- scripts/test_evaluasi.py (data palsu, tanpa model, tanpa data relawan): 30/30 lolos, termasuk dua uji kebocoran (mengubah ekstrem data relawan uji tidak mengubah threshold lipatannya). Satu kegagalan di putaran pertama adalah harapan yang salah di skrip uji (lupa mengeluarkan probe gagal dari hitungan pasangan latih lipatan S01: benar 8/16, bukan 9/18); evaluasi.py tidak diubah.
- Uji ujung-ke-ujung sub-perintah liveness dengan CSV palsu di scratchpad: JSON sah (inf/nan ditulis null); BPCER 1/8 dan AUC 0,875 sesuai hitungan tangan.
- Belum teruji: sub-perintah embed (hanya dapat dijalankan pada data relawan); diperiksa lewat jumlah status pada run pertama.

## 2026-11-08 - Run pertama data relawan: liveness skenario 1280
- Perintah: python scripts/infer_liveness.py --manifest datasets/liveness/internal/manifest.csv --root datasets/liveness/internal/raw --max_side 1280 --out results/liveness/skor_1280.csv (26 detik); lalu python scripts/evaluasi.py liveness --scores results/liveness/skor_1280.csv --out results/liveness/metrik_1280.json. Kode commit 6a81568 (skrip_belum_di_commit = False).
- Pipeline: 160/160 ok, 1 wajah per foto, skor deteksi min 0,889 (median 0,944), semua 960x1280 setelah potong 3:4; lebar kotak wajah 190-588 px; 2 foto real dengan wajah < 5 px dari tepi.
- Aturan bawaan (hasil utama; CI Clopper-Pearson 95%, optimistis):
  - MiniFASNet: BPCER 0/80 (0-4,5%); APCER print 16/40 = 40,0% (24,9-56,7); screen 7/40 = 17,5% (7,3-32,8); ACER 20,0%; AUC 0,995.
  - face-antispoof-onnx: BPCER 4/80 = 5,0% (1,4-12,3); APCER print 17/40 = 42,5% (27,0-59,1); screen 14/40 = 35,0% (20,6-51,7); ACER 23,8%; AUC 0,878. S01: semua 20 serangan diterima.
  - anti-spoof-mn3 (crop ASUMSI): BPCER 42/80 = 52,5% (41,0-63,8; S02 20/20 dan S04 20/20 real ditolak); APCER print 0/40; screen 9/40 = 22,5%; ACER 37,5%; AUC 0,812.
- Tambahan EER-LOSO (ACER gabungan): MiniFASNet 8,1% (BPCER 7/80, APCER print 3/40, screen 0/40; threshold p1 0,82-0,93); face-antispoof-onnx 28,1% (threshold sangat berbeda antarlipatan: 0,50 vs 3,87-4,83); anti-spoof-mn3 44,4% (threshold p_real 0,002-0,022).
- McNemar (aturan bawaan): MiniFAS vs facenox 23 vs 11, p 0,058; MiniFAS vs mn3 50 vs 22, p 0,0013; facenox vs mn3 40 vs 24, p 0,060 (p optimistis karena korelasi dalam relawan).
- Catatan tafsir (BUKAN kesimpulan akhir): (1) dengan aturan bawaan tidak ada model yang menolak serangan dengan baik; (2) AUC MiniFASNet tinggi tetapi titik keputusan bawaan (argmax) terlalu longgar; (3) AUC gabungan dapat terpengaruh perbedaan pengaturan kamera antara foto real dan serangan (amandemen 2 bagian 2) [T]; (4) pola mn3 (semua real S02/S04 ditolak, threshold EER mendekati 0) konsisten dengan, tetapi tidak membuktikan, asumsi crop yang salah [T]; (5) 4 relawan: CI lebar.
- Skenario 640 dan penuh, serta pengenalan, belum dijalankan.

## 2026-11-08 - Verifikasi preprocessing anti-spoof-mn3 dari kode pelatihan sumber
- Izin peneliti untuk membaca. Repo github.com/kprokofi/light-weight-face-anti-spoofing (MIT, Intel; tidak diarsipkan), commit 82a2c26bacff5462c6f9320c34ae0363ccbed497 (2021-03-24). Berkas dibaca dengan curl ke scratchpad (bukan ke proyek); SHA-256: datasets/celeba_spoof.py c7391aa4...b2f5; demo/demo.py 5e46165e...186f; demo_tools/wrapers.py 8ef69701...bd97; utils.py a48fcc0d...78bd2; train.py 183a8f8b...8031. Tidak ada paket atau bobot diunduh.
- Kaitan model: README menyebut model akhir MN3_large dilatih pada CelebA-Spoof, 3,02 juta parameter, ACER 3,8% (sama dengan jumlah parameter bobot OMZ kita dan ACER 3,81% di dokumen OMZ) [V, kecocokan angka].
- CROP [V]: pelatihan (celeba_spoof.py) memotong TEPAT kotak wajah dari anotasi CelebA-Spoof, tanpa perluasan dan tanpa dipersegikan. Demo (demo.py + wrapers.py) memotong kotak detektor OpenVINO yang diperluas lebar x1,1 dan tinggi x1,05 (dipusatkan; kiri/atas dibatasi >= 0), tidak dipersegikan. ASUMSI kita (persegi x1,5 padding refleksi) SALAH.
- Resize [V]: 128x128 dengan cv.INTER_CUBIC (pelatihan val_transform dan demo); kita memakai INTER_AREA/INTER_LINEAR.
- Warna dan normalisasi [V]: BGR->RGB, x/255 lalu (x - mean)/std dengan mean [0.5931, 0.4690, 0.4229], std [0.2471, 0.2214, 0.2157]; x255 = [151.24, 119.60, 107.84] dan [63.01, 56.46, 55.00], cocok dengan mean/scale dokumen OMZ yang kita pakai. Normalisasi kita benar.
- Aturan keputusan [V]: demo menyatakan spoof bila p_spoof > 0,4 (--spoof_thresh bawaan 0,4, "makin rendah makin berorientasi spoof"). Aturan kita (real bila p_real > p_spoof, setara spoof bila p_spoof > 0,5) adalah usulan yang ditandai [T] di spesifikasi-preprocessing-v2.
- Akibat: hasil anti-spoof-mn3 pada run 1280 (2026-11-08) memakai crop yang salah dan tidak boleh dipakai untuk kesimpulan. Koreksi kode menunggu keputusan peneliti.

## 2026-11-08 - Liveness 1280 dijalankan ulang setelah amandemen 5
- Kode commit a2b6ca8 (bersih). test_mn3.py 5/5 (kotak sama dengan hitungan tangan dari rumus demo; gambar sintetis membuktikan potongan tepat pada kotak, tidak persegi, tanpa padding); test_warna, test_modul1, test_potong34 tetap lolos.
- Run ulang: perintah sama dengan run pertama; hasil menimpa results/liveness/skor_1280.csv dan metrik_1280.json (versi lama tetap di commit e5775d3). Perbandingan dengan run lama: 33/36 kolom identik untuk 160 sampel; hanya mn3_p_real, mn3_p_spoof (160) dan mn3_pred_real (9) berubah. MiniFASNet dan face-antispoof-onnx tidak berubah (ACER 20,0% dan 23,8%).
- anti-spoof-mn3 (preprocessing dan aturan sesuai sumber): BPCER 45/80 = 56,2% (44,7-67,3; S02 20/20 dan S04 20/20 real ditolak, S01 2/20, S03 3/20); APCER print 0/40 (0-8,8); screen 7/40 = 17,5% (7,3-32,8); ACER 36,9%; AUC 0,835. EER-LOSO: threshold p_real 0,002-0,013, ACER 42,5%.
- Tafsir: koreksi crop bukan penyebab utama kinerja buruk mn3; penolakan seluruh foto real dua relawan tetap terjadi. Penyebab [T] (mis. pergeseran domain dari CelebA-Spoof ke kamera ponsel relawan; README sumber sendiri melaporkan ACER 16,3% lintas-dataset pada LCC_FASD). Tidak diselidiki lebih jauh tanpa keputusan peneliti.
- McNemar (aturan bawaan): MiniFAS vs facenox 23 vs 11, p 0,058; MiniFAS vs mn3 52 vs 23, p 0,0011; facenox vs mn3 42 vs 25, p 0,050.

## 2026-11-08 - Liveness skenario 640 dan penuh
- Perintah sama dengan run 1280 dengan --max_side 640 dan 0 (penuh); keluaran results/liveness/skor_{640,penuh}.csv (+ meta) dan metrik_{640,penuh}.json. Kode commit 73960b1 (kode sama dengan a2b6ca8; commit itu hanya menambah dokumen). Ketiga skenario: 160/160 ok, 1 wajah per foto, skor deteksi min 0,889-0,890.
- Aturan bawaan, ACER (BPCER k/80; APCER print k/40; screen k/40) untuk 640 / 1280 / penuh:
  - MiniFASNet: 21,2% (0; 17; 8) / 20,0% (0; 16; 7) / 16,2% (0; 13; 8); AUC 0,991 / 0,995 / 0,992.
  - face-antispoof-onnx: 21,9% (3; 16; 16) / 23,8% (4; 17; 14) / 25,6% (1; 20; 14); AUC 0,875 / 0,878 / 0,880.
  - anti-spoof-mn3: 33,8% (44; 0; 5) / 36,9% (45; 0; 7) / 35,0% (44; 0; 6); AUC 0,867 / 0,835 / 0,829.
- Tambahan EER-LOSO, ACER (BPCER/APCER print/screen): MiniFASNet 13,1% (11/5/1) / 8,1% (7/3/0) / 7,5% (6/3/1); facenox 28,7% / 28,1% / 26,9%; mn3 37,5% / 42,5% / 43,8%.
- McNemar MiniFAS vs facenox: p 0,121 / 0,058 / 0,024; MiniFAS vs mn3: p 0,007 / 0,001 / 0,0008; facenox vs mn3: p 0,114 / 0,050 / 0,101 (optimistis).
- Pengamatan (bukan kesimpulan akhir): urutan model sama di ketiga skenario (MiniFASNet terbaik, mn3 terburuk); dengan aturan bawaan tidak ada model yang menolak serangan dengan baik (APCER print MiniFASNet 33-43%); hanya MiniFASNet dengan threshold EER dari relawan latih yang mendekati kinerja berguna, dan membaik dengan resolusi lebih tinggi (640 terburuk).

## 2026-11-08 - Pengenalan wajah: tiga skenario resolusi
- Run pertama embed (1280) menemukan celah: metadata .npz tidak mencatat commit, hash bobot, versi pustaka (aturan 6). Diperbaiki (evaluasi.py jejak_embed, commit 1a61a5a; test_evaluasi tetap 30/30) lalu 1280 dijalankan ulang. Hash bobot di metadata cocok dengan logs/checksums-models.txt.
- Perintah: python scripts/evaluasi.py embed --max_side {640,1280,0} --threads 4 --out results/recognition/emb_{640,1280,penuh}.npz; lalu evaluasi.py recognition --emb ... --out results/recognition/metrik_{...}.json. Sekitar 22 detik per skenario.
- Ketiga skenario: 82/82 ok (62 probe: S01 15, S02 15, S03 15, S04 17; enrollment 5 per relawan, semua terpakai); tanpa embedding kosong; norma 1. Pasangan: genuine 62, impostor 186; lipatan latih 45-47 genuine / 90-94 impostor.
- Hasil LOSO (threshold EER lipatan latih), FRR k/62 dan FAR k/186 untuk 640 / 1280 / penuh:
  - AuraFace: FRR 1 / 1 / 1; FAR 0 / 2 / 15; AUC 1,0000 di ketiga skenario; median genuine 0,88-0,90, impostor 0,28-0,30.
  - buffalo_l: FRR 0 / 0 / 0; FAR 0 / 0 / 0 (batas atas FAR 1,6%); AUC 1,0000; median genuine 0,90-0,91, impostor 0,12.
  - SFace: FRR 1 / 1 / 1; FAR 7 / 8 / 16; AUC 1,0000 / 0,9999 / 0,9994; median genuine 0,91-0,92, impostor 0,31.
- Pengamatan: AuraFace mencapai AUC 1,0 (pemisahan sempurna gabungan) tetapi FAR 15/186 pada penuh: threshold EER pada data latih yang terpisah sempurna jatuh di titik tengah celah, dan impostor lipatan uji (S02, S03) masuk ke celah itu. FAR sensitif terhadap aturan threshold bila data latih terpisah sempurna. Aturan tidak diubah (amandemen 4).
- Batasan: enrollment dan probe sesi yang sama (bias optimistis, amandemen 3); hanya 4 identitas, 186 impostor; FAR di bawah ~1,6% tidak dapat dibuktikan; buffalo_l RISET SAJA (lisensi).
- Privasi: berkas embedding (results/recognition/*.npz) adalah data biometrik relawan; ditambahkan ke .gitignore (tetap di disk lokal). Hanya metrik agregat di-commit.

## 2026-11-09 - Langkah 6: makna indeks MiniFASNet, lisensi WIDER Face, model card BlazeFace
- MiniFASNet (repo lokal commit b6d5f04a): README_EN bagian Data Preprocessing hanya menyatakan data latih dibagi tiga kategori dalam folder bernama 0, 1, 2 (ImageFolder); test.py memakai indeks 1 = real. Makna indeks 0 dan 2 TIDAK didokumentasikan di repo resmi -> tetap [T]. Sumber sekunder (pembungkus pihak ketiga, hasil pencarian web) menyebut 0 dan 2 dua jenis spoof [S]. Tidak memengaruhi hasil: evaluasi memakai p(indeks 1) dan argmax.
- WIDER Face: situs resmi (shuoyang1213.me/WIDERFACE) gagal dibuka karena sertifikat TLS tidak cocok; pemeriksaan sertifikat TIDAK dilewati. Kartu dataset Hugging Face organisasi CUHK-CSE (huggingface.co/datasets/CUHK-CSE/wider_face, dibaca 2026-11-09): lisensi "cc-by-nc-nd-4.0" / "Creative Commons Attribution-NonCommercial-NoDerivatives 4.0 International" [S, sumber lebih dekat ke pemilik daripada sebelumnya, belum situs resmi]. Satu cermin Kaggle menyebut CC0 (bertentangan, tidak dipakai). Status YuNet untuk produksi tetap TERTAHAN-LISENSI.
- BlazeFace (halaman resmi Google developers.google.com/edge/mediapipe/solutions/vision/face_detector, dibaca 2026-11-09): tiga model (short-range, full-range, full-range sparse), input 128x128, float16, tautan model card PDF. Halaman tidak memuat pernyataan lisensi model. Model card short-range diunduh (tool-results, tidak ikut repo): teks tidak dapat diekstrak tanpa pustaka PDF (tidak dipasang tanpa izin); hanya terbaca judul dan tautan ke Apache License 2.0 (konteks tautan tidak terbaca) -> lisensi bobot dan data latih BlazeFace tetap [T].

## 2026-11-09 - Model card BlazeFace dibaca (pypdf dipasang atas izin peneliti)
- Peneliti memilih opsi A: pypdf 7.0.0 dipasang di .venv (pip install pypdf; murni Python). Lingkungan dicatat ulang di configs/requirements-stage4.txt (beda dengan stage3: hanya tambahan pypdf==7.0.0).
- PDF model card short-range (SHA-256 cd335c06fc0de7807cd815a0777a697932598bcdb28fa98adaaabf847485f758, 6 halaman, tanggal 9 Juni 2021) diekstrak dengan pypdf ke scratchpad (tidak ikut repo).
- Temuan [V]: bobot "Apache License, Version 2.0"; data latih "consented images" dari aplikasi AR ponsel (tidak dirilis); "identity recognition" dan pengawasan dinyatakan di luar cakupan; keluaran 6 titik (bukan 5 titik ArcFace); syarat wajah >= 20% sisi gambar, <= 2 m.
- Dicatat di audit/license-evidence-v2.md dan audit/model-audit-v3.md (bagian pembaruan baru di akhir; isi lama tidak diubah). Implikasi: lisensi BlazeFace layak, tetapi pernyataan out-of-scope perlu tafsir hukum [T] dan alignment AuraFace perlu disesuaikan dan diuji [T]. BlazeFace belum diuji di pipeline ini.

## 2026-11-09 - Draf laporan akhir (K10)
- reports/laporan-akhir.md v1.0 (draf) ditulis dari metrik_*.json dan log; tidak ada eksperimen baru. Angka dicek ulang dari JSON (CI Clopper-Pearson) dan baris lisensi dicocokkan dengan audit/model-audit-v3.md (koreksi saat penulisan: mn3 MIT, buffalo_l tanpa klaim lisensi kode, facenox data latih [T]).
- Isi keputusan (usulan, menunggu peneliti): liveness MiniFASNet = kandidat untuk pilot, BELUM layak produksi (aturan bawaan meloloskan 33-43% foto cetak; dengan threshold EER-LOSO ACER 8,1% pada 1280); pengenalan AuraFace = layak bersyarat; detektor produksi belum ada (BlazeFace belum diuji). Format foto usulan: 3:4, sisi terpanjang 1280.
- Latensi pada laporan berasal dari benchmark awal 2026-11-05 (sebelum amandemen 2 dan 5); latensi pengenalan belum diukur.
- Kelayakan Frappe: desain saja (layanan inferensi terpisah, data biometrik/UU PDP [T]).
- Catatan: PRD berada di akar proyek (PRD-penelitian.md), bukan reports/ seperti tertulis di CLAUDE.md.

## 2026-11-09 - Tinjauan angka draf laporan akhir dan revisi v1.1
- Pemeriksaan dilakukan asisten pada salinan zip repo (membaca dokumen, log, dan metrik_*.json; tidak ada kode atau model dijalankan, tidak ada eksperimen baru, tidak ada data relawan dibuka).
- Hasil pencocokan: semua angka tabel 3.1, 3.2, dan 4 laporan sama dengan results/liveness/metrik_{640,1280,penuh}.json dan results/recognition/metrik_{640,1280,penuh}.json (termasuk rentang threshold MiniFASNet 0,82-0,93, rincian per cahaya dan per relawan, nilai McNemar, jumlah sampel 160/160 dan 82/82). Angka latensi sesuai benchmark sesi kedua 2026-11-05.
- Tidak diverifikasi dalam tinjauan ini: hash dan commit (zip tanpa riwayat Git) serta tabel lisensi secara menyeluruh.
- Revisi laporan-akhir.md menjadi v1.1 (6 butir, hanya teks; tidak ada angka hasil diubah):
  1. Ringkasan (bagian 1): ditambah catatan bahwa perbedaan ukuran dan EXIF antara foto asli dan serangan dapat memengaruhi AUC MiniFASNet [T].
  2. Bagian 3.3: "p <= 0,007" diganti "p < 0,01 (0,0008-0,0071)" (nilai pada 640 adalah 0,0071); ditambah catatan bahwa nilai p optimistis karena korelasi dalam relawan.
  3. Bagian 4: klaim FAR AuraFace 15/186 "disebabkan aturan threshold, bukan model" dilunakkan menjadi "kemungkinan besar terkait aturan threshold [T]"; median genuine turun (0,898 -> 0,884) dan impostor naik (0,284 -> 0,300) dari 640 ke penuh sehingga resolusi mungkin ikut berperan. Pemisahan penyebab belum dilakukan.
  4. Bagian 6: lisensi bobot MiniFASNet diubah dari [V] menjadi "mengikuti repo [T]" (yang terverifikasi hanya lisensi repo), disamakan dengan face-antispoof-onnx.
  5. Bagian 5: ukuran face.jpg dikoreksi menjadi 750x500 (lanskap), sesuai koreksi 2026-11-08.
  6. Bagian 7.2: usulan 1280 px dinyatakan sebagai asumsi kompromi, dengan angka pembanding 640/1280/penuh; klaim "FAR jauh lebih rendah" dihapus karena selisih 0 vs 2 dari 186 tidak bermakna.
- Masih terbuka: (a) bandingkan skor genuine terendah dan impostor tertinggi per skenario untuk memisahkan efek aturan threshold dari efek resolusi; (b) periksa apakah ukuran/EXIF saja dapat memisahkan foto asli dari serangan (hanya metadata, tanpa membuka gambar).

## 2026-11-09 - PRD dipindah ke reports/
- PRD-penelitian.md dipindah dari akar proyek ke reports/PRD-penelitian.md. Isi tidak berubah (dibandingkan dengan versi di HEAD memakai diff: sama).
- Lokasi baru sesuai dengan yang tertulis di CLAUDE.md (reports/PRD-penelitian.md); catatan entri 2026-11-09 sebelumnya (PRD di akar proyek) berlaku untuk keadaan sebelum pemindahan ini.
- Pembaruan tanggal dan baris status di CLAUDE.md dikerjakan terpisah.

## 2026-11-09 - CLAUDE.md: tanggal dan daftar reports/ diperbarui
- CLAUDE.md: "Terakhir diperbarui" dari 6 November menjadi 9 November 2026.
- CLAUDE.md, daftar isi reports/: ditambah amandemen-protokol-5.md (crop mn3), nama lengkap PRD-penelitian.md, dan laporan-akhir.md (v1.1, draf).
- Bagian lain CLAUDE.md tidak diubah, termasuk status langkah 7 (laporan akhir masih menunggu persetujuan peneliti) dan jalur proyek utama C:\dev\model-research-face.

## 2026-11-09 - Analisis celah skor pengenalan (scripts/analisis_celah.py)
- Skrip baru scripts/analisis_celah.py dan uji scripts/test_analisis_celah.py (16/16 lolos pada data tiruan, termasuk uji bahwa pemuat pasangan setara evaluasi.recognition_from_npz). Skrip hanya membaca emb_*.npz dan manifest.csv; tidak ada model dijalankan, tidak ada gambar dibuka, keluaran hanya angka agregat (results/recognition/analisis_celah.json).
- Pada data relawan, jumlah FA dan FR per lipatan sama dengan metrik_*.json (AuraFace FA 0/2/15 dan FR 1; SFace FA 7/8/16 dan FR 1; buffalo_l 0). Perintah: python scripts/analisis_celah.py --emb results/recognition/emb_640.npz results/recognition/emb_1280.npz results/recognition/emb_penuh.npz --out results/recognition/analisis_celah.json
- Celah gabungan (skor genuine terendah - skor impostor tertinggi), skenario 640 / 1280 / penuh: AuraFace 0,076 / 0,069 / 0,011; buffalo_l 0,356 / 0,352 / 0,348; SFace 0,001 / -0,012 / -0,058 (impostor yang skornya >= genuine terendah: 0 / 1 / 7).
- Threshold EER tiap lipatan selalu tepat di tengah celah data latih (posisi 0,50) pada semua model dan skenario yang celah latihnya positif. Pengecualian: lipatan S02 SFace pada 1280 dan penuh (celah latih negatif, posisi tidak terdefinisi).
- Tafsir (bukan kesimpulan akhir): (1) mekanisme aturan threshold terkonfirmasi [V]; pada penuh, threshold tengah-celah lipatan S02 (0,444) dan S03 (0,425) berada di bawah impostor uji tertinggi (0,492 dan 0,471), sehingga FA 6 + 9. (2) Klaim awal laporan v1.0/v1.1 bahwa kenaikan FAR "bukan karena model" tidak didukung: celah AuraFace menyempit sekitar 6 kali lipat pada penuh (0,069 -> 0,011) sedangkan buffalo_l hampir tetap, jadi sensitivitas terhadap resolusi bersifat spesifik model (AuraFace, SFace); penyebabnya belum diketahui [T]. (3) FAR 0/186 AuraFace pada 640 tipis: pada lipatan S02 threshold 0,481 hanya 0,003 di atas impostor uji tertinggi (0,478). (4) AUC 1,0 tidak berarti margin lebar: celah terbaik AuraFace 0,076 vs buffalo_l 0,356; dengan 4 identitas, impostor tertinggi kemungkinan naik bila identitas bertambah [T].
- Batas: rentang ambang tanpa kesalahan pada data ini TIDAK boleh dipakai sebagai threshold produksi karena diambil dari data yang sama (aturan 5).
- Belum dilakukan: identifikasi pasangan impostor tertinggi per relawan; uji hipotesis penyebab sensitivitas resolusi AuraFace; revisi laporan-akhir.md (bagian 1, 4, 7.2) menunggu persetujuan peneliti.

## 2026-11-09 - Revisi laporan-akhir.md v1.2 (hasil analisis celah skor)
- Dasar: results/recognition/analisis_celah.json (scripts/analisis_celah.py, commit e346f4c) dan entri log "Analisis celah skor pengenalan". Tidak ada eksperimen baru; tidak ada angka di metrik_*.json yang diubah.
- Perubahan teks (4 tempat):
  1. Bagian 1, baris face recognition: "pemisahan sempurna, AUC 1,0" diganti "AUC 1,0 tetapi celah skor sempit (0,07 pada 1280 px, 0,011 pada penuh)".
  2. Bagian 4, butir AuraFace: klaim "kemungkinan besar terkait aturan threshold [T]" diganti temuan terukur (celah 0,076 / 0,069 / 0,011; threshold selalu di tengah celah latih; celah menyempit pada penuh sedangkan buffalo_l tidak; FAR 0/186 pada 640 tipis; AUC 1,0 tidak berarti margin lebar; ambang tanpa kesalahan tidak boleh dipakai sebagai threshold produksi).
  3. Bagian 7.2, butir pengenalan: resolusi penuh tidak dipilih untuk AuraFace (celah 0,011); 640 vs 1280 tidak terbedakan; usulan 1280 tetap sebagai asumsi.
  4. Bagian 9: ditambah keterbatasan celah skor AuraFace sempit dengan 4 identitas [T].
- Penyebab sensitivitas resolusi AuraFace tetap [T] dan belum diuji.

## 2026-11-09 - CLAUDE.md: versi laporan akhir disamakan dengan v1.2
- Dasar: commit f05056e (laporan-akhir.md v1.2, hasil analisis celah skor). Tidak ada eksperimen baru, tidak ada model dijalankan, tidak ada data relawan dibuka.
- Dua perubahan teks pada CLAUDE.md (diff diperiksa: tepat 2 baris berubah):
  1. Baris 66 (daftar reports/): "laporan-akhir.md (v1.1, draf)" menjadi "(v1.2, draf)".
  2. Baris 129 (langkah 7): "DRAF 2026-11-09" menjadi "DRAF v1.2 2026-11-09". Status tetap menunggu tinjauan peneliti.
- Bagian lain CLAUDE.md tidak diubah, termasuk tanggal "Terakhir diperbarui" (9 November 2026).
- Catatan terbuka: daftar "Skrip yang ada" di CLAUDE.md belum diperiksa apakah memuat analisis_celah.py dan test_analisis_celah.py; dikerjakan sebagai langkah terpisah.

## 2026-11-09 - CLAUDE.md: analisis_celah.py ditambahkan ke daftar skrip
- Dasar: commit e346f4c (analisis_celah.py dan test_analisis_celah.py, uji 16/16) dan commit 560e2c2 (CLAUDE.md sinkron dengan laporan v1.2). Tidak ada eksperimen baru, tidak ada model dijalankan, tidak ada data relawan dibuka.
- Perubahan teks pada CLAUDE.md (diff diperiksa: tepat 1 baris ditambahkan, tanpa baris dihapus): bullet baru `analisis_celah.py` di bagian "Skrip yang ada", tepat setelah bullet metrics.py/recognition.py/evaluasi.py. Isi bullet hanya mengulang fakta dari entri log "Analisis celah skor pengenalan".
- Temuan terpisah, belum ditindaklanjuti: git log menunjukkan origin/main (remote), sedangkan CLAUDE.md menulis "Repo Git lokal, tanpa remote". Tujuan remote dan apakah publik belum diperiksa; tidak ada push dilakukan.
