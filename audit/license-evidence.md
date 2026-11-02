# Bukti Lisensi

Tanggal pemeriksaan: 2 November 2026. Bukan opini hukum. Pernyataan di bawah dirangkum dengan kata-kata sendiri dari halaman yang tertera.

## 1. Silent-Face-Anti-Spoofing (MiniFASNet)

- Kode: file LICENSE berisi Apache License 2.0, hak cipta Minivision 2020. https://github.com/minivision-ai/Silent-Face-Anti-Spoofing/blob/master/LICENSE
- Bobot: ada di folder `resources/anti_spoof_models` pada repo yang sama; tidak ada pernyataan lisensi terpisah yang ditemukan. https://github.com/minivision-ai/Silent-Face-Anti-Spoofing
- Data latih: tidak dijelaskan di README.
- Pemeliharaan: halaman organisasi menunjukkan pembaruan terakhir 3 Oktober 2023. https://github.com/minivision-ai
- Klaim vendor (belum diukur): MiniFASNetV2 0,081 GFLOPs dan 0,435 juta parameter; model APK 84M FLOPs, 20 ms, FPR 1e-5, TPR 97,8% (protokol tidak dijelaskan).
- Belum terverifikasi: lisensi dan data latih detektor RetinaFace di `resources/detection_model`.

## 2. anti-spoof-mn3 (OpenVINO Open Model Zoo)

- Halaman model menyatakan model asli didistribusikan di bawah MIT dan dilatih pada CelebA-Spoof. https://docs.openvino.ai/2024/omz_models_model_anti_spoof_mn3.html
- Dataset CelebA-Spoof: ketentuan menyebut penggunaan hanya untuk riset nonkomersial. https://github.com/Davidzhangyuanhan/CelebA-Spoof
- Unduhan bobot lewat `omz_downloader`; keberlakuan perintah ini belum diuji.
- Pernyataan di forum Intel bahwa bobot sudah "bersih" untuk komersial adalah jawaban forum, bukan pernyataan resmi; jangan dijadikan dasar. https://community.intel.com/t5/Intel-Distribution-of-OpenVINO/Anti-spoof-mn3/m-p/1720003

## 3. CDCN

- README resmi menyatakan kode hanya untuk tujuan riset dan penggunaan komersial tidak diizinkan. https://github.com/ZitongYu/CDCN
- Repo tidak memiliki Releases. Isi subfolder belum diperiksa.

## 4. InsightFace buffalo_l

- Model zoo menyatakan seluruh model hanya untuk riset nonkomersial. https://github.com/deepinsight/insightface/blob/e68b8b076fb11e9f75c87244d234385f0f318181/model_zoo/README.md (commit tertentu; periksa versi terbaru saat keputusan).
- buffalo_l: detektor RetinaFace-10GF, pengenal ResNet50 pada WebFace600K, ukuran paket 326 MB (halaman yang sama).
- Akurasi self-reported (halaman yang sama): LFW 99,83; CFP-FP 99,33; AgeDB-30 98,23; IJB-C(E4) 97,25; East Asian 74,96. Tidak ada kolom Asia Tenggara.
- Lisensi komersial: harus diminta ke InsightFace (kontak resmi tercantum pada README repo utama).

## 5. AuraFace-v1

- Model card: lisensi Apache-2.0, ResNet100 dengan additive angular margin loss, dilatih pada data komersial dan publik agar bisa dipakai di setting komersial. https://huggingface.co/fal/AuraFace-v1
- Keterbatasan menurut model card: efektivitas dapat berbeda menurut etnis; generalisasi terbatas oleh data latih; pengguna perlu menilai sendiri bias dan kepatuhan privasi.
- Benchmark resmi: LFW 0,9965; CFP-FP 0,9519; AgeDB 0,9610; CALFW 0,9470; CPLFW 0,9093.
- Contoh penggunaan memakai pustaka insightface. Pustaka tersebut dan detektor bawaannya berlisensi terpisah; detektor yang dipakai harus diaudit sendiri.

## 6. SFace (OpenCV Zoo)

- README menyatakan semua file di direktori model berlisensi Apache 2.0; model adalah MobileFaceNet yang dilatih dengan SFace loss; konversi ONNX dari kode asli. https://github.com/opencv/opencv_zoo/blob/main/models/face_recognition_sface/README.md
- README tidak menyebut dataset latih bobot.
- Akurasi pada tools evaluasi OpenCV Zoo: 0,9940 (dataset evaluasi tidak dinyatakan di halaman itu).
- Detektor yang dipakai demo: YuNet dari repo yang sama (lisensi diaudit terpisah).
