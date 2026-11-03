# Audit Model: Liveness Detection dan Face Recognition (revisi 2, 2 November 2026)

Tujuan penggunaan (dikonfirmasi pengguna): fitur absensi aplikasi HRMS mobile, jadi diperlakukan sebagai **target produksi/komersial**.
Catatan: dokumen ini bukan opini hukum. Status lisensi perlu dikonfirmasi penasihat hukum sebelum produksi.

Legenda: [V] terverifikasi dari halaman resmi atau hasil eksperimen; [K] klaim vendor/publikasi, belum diukur; [S] sumber sekunder; [T] belum terverifikasi.

## Tabel keputusan model

| # | Model | Kategori | Status audit (produksi) | Alasan singkat |
|---|---|---|---|---|
| 1 | Silent-Face-Anti-Spoofing (MiniFASNetV2 + V1SE) | Liveness | LULUS AUDIT AWAL (risiko dicatat) | Apache-2.0 [V]. Data latih bobot tidak dijelaskan [V: tidak ada]. Commit terakhir master: 2020-08-05 [V]. |
| 2 | anti-spoof-mn3 (OpenVINO Open Model Zoo) | Liveness | TERTAHAN, LISENSI | Model MIT [V], dilatih pada CelebA-Spoof yang nonkomersial [V]. |
| 3 | CDCN | Liveness | RISET SAJA | README resmi: hanya riset, komersial tidak diizinkan [V]. Tidak ada Releases; bobot belum ditemukan [T]. |
| 4 | InsightFace buffalo_l | Face recognition | RISET SAJA | Semua model di model zoo hanya untuk riset nonkomersial [V]. |
| 5 | AuraFace-v1 | Face recognition | LULUS AUDIT AWAL (risiko dicatat) | Apache-2.0 [V], dilatih pada data komersial/publik agar boleh komersial [V]; cakupan etnis terbatas menurut model card [V]. |
| 6 | SFace (OpenCV Zoo) | Face recognition | TERTAHAN, LISENSI | Apache-2.0 untuk file di direktori [V], dataset latih tidak disebut [V: tidak ada]. |

## Detektor wajah (komponen pipeline bersama)

| Detektor | Lisensi file | Data latih | Status |
|---|---|---|---|
| RetinaFace Caffe (bawaan MiniFASNet) | Tidak dinyatakan [T] | WIDER Face (dari nama) [T] | Tidak dipakai produksi |
| SCRFD (paket InsightFace/AuraFace) | Nonkomersial [S] | Tidak dirinci | Tidak dipakai |
| YuNet 2023mar (OpenCV Zoo) | MIT [V] | WIDER Face; dilabeli CC-BY-NC-ND-4.0 oleh kartu pihak ketiga [S]; situs resmi WIDER belum diperiksa [T] | **Detektor eksperimen**; TERTAHAN-LISENSI untuk produksi |
| BlazeFace short-range (MediaPipe) | Apache-2.0 [S] | Proprietary Google, tidak diungkap [S] | Kandidat detektor produksi; model card Google belum diverifikasi [T] |

## Keputusan yang dicatat

1. Keenam kandidat diuji penuh dengan protokol yang sama. Kelayakan produksi ditentukan terpisah lewat gerbang lisensi. Jika model berlabel riset menang, minta konfirmasi tertulis sebelum produksi.
2. Jalur eksekusi utama: CPU. GPU RTX 3060 Laptop opsional dan belakangan.
3. Python eksperimen 3.12.10 di samping 3.14.7. Alasan: dukungan wheel 3.14 masih baru dan belum merata; repo MiniFASNet tidak aktif sejak 2020.
4. Lokasi proyek: `C:\dev\model-research-face`. Dataset besar dapat diarahkan ke D: bila C: tidak cukup.
5. Satu detektor yang sama (YuNet) untuk semua model pada eksperimen. Detektor produksi ditentukan terpisah.
6. Urutan kerja: #1 dan #5 lebih dulu, lalu pembanding.

## Fakta terverifikasi (hasil eksperimen)

- AuraFace `glintr100.onnx`: 260694151 byte, SHA-256 a7933ea5330113b01c9b60351d8f4c33003f145d8470ac5f0e52ee2effe25c60 (cocok dengan nilai resmi). Input [batch dinamis,3,112,112]; output [1,512]; norma L2 sekitar 9,71, jadi embedding harus dinormalisasi L2.
- MiniFASNet commit b6d5f04ad78778917853b25c778acef6d5626d15. Bobot dimuat dengan `weights_only=True`; V2: 434560 parameter, skala 2,7; V1SE: 433586 parameter, skala 4,0; input 80x80, kernel (5,5), keluaran 3 kelas (smoke test, data acak).
- Preprocessing MiniFASNet (dari kode): gambar BGR, skala nilai 0-255 (tanpa pembagian 255), tanpa Normalize; crop kotak wajah diperbesar sebesar skala, resize 80x80 tanpa menjaga rasio; gambar harus rasio 3:4; makna indeks 0 dan 2 keluaran belum terverifikasi.
- YuNet `face_detection_yunet_2023mar.onnx`: 232589 byte, SHA-256 8f2383e4dd3cfbb4553ea8718107fc0423210dc964f9f4280604804ed2552fa4 (cocok dengan nilai mirror).

## Perangkat uji

Intel i7-11800H (8 core/16 thread), RAM 15,7 GB, RTX 3060 Laptop, Windows 11, Git Bash, Python 3.12.10 (venv), torch 2.15.0+cpu, onnxruntime 1.31.1, opencv-python-headless 5.0.0.93, numpy 2.5.4. Disk C: sisa sekitar 23 GB, D: sekitar 102 GB.

## Pertanyaan terbuka

- #1: lisensi data latih bobot; makna indeks keluaran 0 dan 2; kompatibilitas OpenCV 5 dengan detektor Caffe (tidak dipakai).
- #2: sumber unduhan bobot dan status pemeliharaan Open Model Zoo; izin tertulis terkait CelebA-Spoof.
- #3: lokasi bobot di subfolder repo.
- #4: perlukah lisensi komersial ke InsightFace.
- #5: isi file lengkap repo AuraFace dan dataset latih.
- #6: dataset latih bobot ONNX OpenCV Zoo.
- Detektor: lisensi WIDER Face di situs resmi; model card BlazeFace Google.
- Dataset evaluasi publik: syarat akses dan lisensi masing-masing belum dibaca.
