# Bukti Lisensi (revisi 2)

Tanggal pemeriksaan: 2 November 2026. Bukan opini hukum. Pernyataan di bawah dirangkum dengan kata-kata sendiri dari halaman yang tertera.
Perubahan dari revisi 1: CDCN dikeluarkan; face-antispoof-onnx ditambahkan; bukti detektor wajah dan perincian buffalo_l ditambahkan.

## 1. Silent-Face-Anti-Spoofing (MiniFASNet)

- Kode: file LICENSE berisi Apache License 2.0, hak cipta Minivision 2020. https://github.com/minivision-ai/Silent-Face-Anti-Spoofing/blob/master/LICENSE
- Bobot: ada di folder `resources/anti_spoof_models` pada repo yang sama; tidak ada pernyataan lisensi terpisah yang ditemukan. https://github.com/minivision-ai/Silent-Face-Anti-Spoofing
- Data latih: tidak dijelaskan di README.
- Pemeliharaan: commit terakhir pada salinan lokal bertanggal 2020-08-05 (hash b6d5f04ad78778917853b25c778acef6d5626d15).
- Klaim vendor (belum diukur): MiniFASNetV2 0,081 GFLOPs dan 0,435 juta parameter. Hasil hitung lokal V2: 434560 parameter (konsisten).
- Konfirmasi sekunder: halaman konversi ONNX pihak ketiga mencantumkan SHA-256 `2.7_80x80_MiniFASNetV2.pth` = a5eb02e1843f19b5386b953cc4c9f011c3f985d0ee2bb9819eea9a142099bec0, sama dengan berkas lokal. https://huggingface.co/garciafido/minifasnet-v2-anti-spoofing-onnx
- Belum terverifikasi: lisensi dan data latih detektor RetinaFace di `resources/detection_model`.

## 2. anti-spoof-mn3 (OpenVINO Open Model Zoo)

- Halaman model menyatakan model asli didistribusikan di bawah MIT dan dilatih pada CelebA-Spoof. https://docs.openvino.ai/2024/omz_models_model_anti_spoof_mn3.html
- Input: model asli RGB dengan mean dan scale tertentu; model konversi BGR; 128x128; kelas 0 = asli, kelas 1 = spoof (halaman yang sama).
- Dataset CelebA-Spoof: ketentuan menyebut penggunaan hanya untuk riset nonkomersial. https://github.com/Davidzhangyuanhan/CelebA-Spoof
- Unduhan bobot lewat `omz_downloader`; keberlakuan perintah ini belum diuji.
- Pernyataan di forum Intel bahwa bobot "dijernihkan" untuk komersial adalah jawaban forum, bukan pernyataan resmi; jangan dijadikan dasar. Jawaban itu sendiri mengakui klausul nonkomersial pada CelebA-Spoof. https://community.intel.com/t5/Intel-Distribution-of-OpenVINO/Anti-spoof-mn3/m-p/1720003

## 3. face-antispoof-onnx (facenox), pengganti CDCN

- Repo: https://github.com/facenox/face-antispoof-onnx (sebelumnya terlihat di bawah akun johnraivenolazo dan suriAI; halaman yang dibuka pada 2 Nov 2026 beralamat facenox).
- Lisensi: Apache-2.0 pada repo (lencana dan file LICENSE tertaut di halaman). Berbasis arsitektur MiniFAS dari Minivision (Apache-2.0); repo menyatakan menyediakan pipeline pelatihan, ekspor ONNX, dan kuantisasi yang independen.
- Bobot di repo: `best_model.pth` (1,95 MB), `best_model.onnx` (1,82 MB), `best_model_quantized.onnx` (600 KB). Input 128x128 RGB, dua kelas.
- Klaim README (belum diukur): akurasi 98,20% dan ROC-AUC 0,9984, diuji pada 70 ribu+ sampel CelebA-Spoof.
- Data latih: tidak dinyatakan eksplisit pada README yang dibuka. Skrip persiapan data memakai berkas kotak wajah `*_BB.txt` dan label tipe spoof (format CelebA-Spoof), sehingga data latih sangat mungkin CelebA-Spoof yang nonkomersial. Ini dugaan, bukan fakta terverifikasi; dokumen `docs/DATA_PREPARATION.md` perlu dibaca langsung.
- Status sementara: TERTAHAN, LISENSI.

## 4. InsightFace buffalo_l

- Model zoo menyatakan seluruh model hanya untuk riset nonkomersial. https://github.com/deepinsight/insightface/blob/e68b8b076fb11e9f75c87244d234385f0f318181/model_zoo/README.md (commit tertentu; periksa versi terbaru saat keputusan).
- buffalo_l: detektor SCRFD-10GF, pengenal ResNet50 pada WebFace600K, ukuran paket 326 MB setelah diekstrak. Paket zip yang diunduh berukuran 288621354 byte (terkompresi). Isi: `genderage.onnx`, `2d106det.onnx`, `det_10g.onnx`, `1k3d68.onnx`, `w600k_r50.onnx`.
- URL unduhan (dari dokumentasi sekunder): https://github.com/deepinsight/insightface/releases/download/v0.7/buffalo_l.zip
- Akurasi self-reported (halaman model zoo): LFW 99,83; CFP-FP 99,33; AgeDB-30 98,23; IJB-C(E4) 97,25; East Asian 74,96. Tidak ada kolom Asia Tenggara.
- Lisensi komersial: harus diminta ke InsightFace (kontak resmi tercantum pada README repo utama).

## 5. AuraFace-v1

- Model card: lisensi Apache-2.0, ResNet100 dengan additive angular margin loss, dilatih pada data komersial dan publik agar bisa dipakai di setting komersial. https://huggingface.co/fal/AuraFace-v1
- Keterbatasan menurut model card: efektivitas dapat berbeda menurut etnis; generalisasi terbatas oleh data latih; pengguna perlu menilai sendiri bias dan kepatuhan privasi.
- Benchmark resmi: LFW 0,9965; CFP-FP 0,9519; AgeDB 0,9610; CALFW 0,9470; CPLFW 0,9093.
- Berkas yang diunduh: hanya `glintr100.onnx` (260694151 byte, SHA-256 cocok dengan nilai resmi), `LICENSE.md`, `README.md`. Repo juga memuat detektor SCRFD yang nonkomersial menurut sumber sekunder; sengaja tidak diunduh.

## 6. SFace (OpenCV Zoo)

- README menyatakan semua file di direktori model berlisensi Apache 2.0; model adalah MobileFaceNet yang dilatih dengan SFace loss; konversi ONNX dari kode asli. https://github.com/opencv/opencv_zoo/blob/main/models/face_recognition_sface/README.md
- Berkas LICENSE di repo Hugging Face OpenCV: Apache License 2.0 (diverifikasi pada berkas yang diunduh).
- README tidak menyebut dataset latih bobot.
- Akurasi pada tools evaluasi OpenCV Zoo: 0,9940 (dataset evaluasi tidak dinyatakan di halaman itu).

## 7. Detektor wajah

- YuNet (OpenCV Zoo): README resmi menyatakan MIT. Data latih/evaluasi WIDER Face; kartu model pihak ketiga melabeli WIDER Face sebagai CC-BY-NC-ND-4.0 (sumber sekunder); situs resmi WIDER Face belum dapat dibuka. https://github.com/opencv/opencv_zoo/blob/main/models/face_detection_yunet/README.md
- BlazeFace short-range (MediaPipe): ringkasan sekunder menyatakan bobot Apache-2.0 (hak cipta Google) dan data latih proprietary Google yang tidak diungkap; model card Google belum dibaca langsung.

## 8. Kandidat yang dikeluarkan: CDCN

- README resmi menyatakan kode hanya untuk tujuan riset dan penggunaan komersial tidak diizinkan. https://github.com/ZitongYu/CDCN
- Repo tidak memiliki Releases dan bobot RGB siap pakai tidak ditemukan; kode membaca data OULU-NPU olahan (`.dat`). Isu GitHub (2021-2022) melaporkan kesulitan mendapatkan berkas olahan dan akses dataset. https://github.com/zitongyu/cdcn/issues/44
- Status: TIDAK DILANJUTKAN.

## Pembaruan 9 November 2026 (detektor; rincian di logs/experiment-log.md)

- WIDER Face: situs resmi gagal dibuka (sertifikat TLS tidak cocok; pemeriksaan tidak dilewati). Kartu dataset Hugging Face organisasi CUHK-CSE: "cc-by-nc-nd-4.0" (CC BY-NC-ND 4.0 International) [S, lebih dekat ke pemilik]. https://huggingface.co/datasets/CUHK-CSE/wider_face/blob/main/README.md
- BlazeFace short-range: model card resmi Google ("MediaPipe BlazeFace Model Card (Short Range)", tanggal 9 Juni 2021, SHA-256 PDF cd335c06...f758) dibaca langsung [V]:
  - "LICENSED UNDER Apache License, Version 2.0".
  - Data latih: "consented images of people using a mobile AR application captured with smartphone cameras"; data tidak dirilis.
  - Out-of-scope: "Any form of surveillance or identity recognition is explicitly out of scope and not enabled by this technology"; "not intended for human life-critical decisions".
  - Syarat input: sisi kotak wajah >= 20% sisi gambar; roll/pitch <= 45 derajat; >= 70% kotak di dalam gambar; jarak <= 2 m; terutama kamera depan.
  - Keluaran 6 titik (dua mata, ujung hidung, mulut, dua tragion), bukan 5 titik ArcFace (tanpa dua sudut mulut).
  - https://storage.googleapis.com/mediapipe-assets/MediaPipe%20BlazeFace%20Model%20Card%20(Short%20Range).pdf
