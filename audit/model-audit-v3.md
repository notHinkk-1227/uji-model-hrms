# Audit Model: Liveness Detection dan Face Recognition (revisi 3, 2 November 2026)

Tujuan penggunaan (dikonfirmasi pengguna): fitur absensi aplikasi HRMS mobile, jadi diperlakukan sebagai **target produksi/komersial**.
Catatan: dokumen ini bukan opini hukum. Status lisensi perlu dikonfirmasi penasihat hukum sebelum produksi.

Legenda: [V] terverifikasi dari halaman resmi atau hasil eksperimen; [K] klaim vendor/publikasi, belum diukur; [S] sumber sekunder; [T] belum terverifikasi.

Perubahan dari revisi 2: **CDCN diganti face-antispoof-onnx (facenox)** atas persetujuan peneliti; status unduhan dan smoke test diperbarui.

## Tabel keputusan model

| # | Model | Kategori | Status audit (produksi) | Alasan singkat |
|---|---|---|---|---|
| 1 | Silent-Face-Anti-Spoofing (MiniFASNetV2 + V1SE) | Liveness | LULUS AUDIT AWAL (risiko dicatat) | Apache-2.0 [V]. Data latih bobot tidak dijelaskan [V: tidak ada]. Commit terakhir master: 2020-08-05 [V]. |
| 2 | anti-spoof-mn3 (OpenVINO Open Model Zoo) | Liveness | TERTAHAN, LISENSI | Model MIT [V], dilatih pada CelebA-Spoof yang nonkomersial [V]. Jawaban forum Intel yang menyebut bobot "dibersihkan" untuk komersial bukan pernyataan resmi [S]. Bobot belum diunduh. |
| 3 | face-antispoof-onnx (facenox), MiniFAS | Liveness | TERTAHAN, LISENSI (sementara) | Kode Apache-2.0 [V]. Data latih sangat mungkin CelebA-Spoof (format data dan pengujian mengikuti dataset itu) [T]. Bobot ONNX siap pakai di repo [K]. Menggantikan CDCN. Belum diunduh. |
| 4 | InsightFace buffalo_l | Face recognition | RISET SAJA | Semua model di model zoo hanya untuk riset nonkomersial [V]. |
| 5 | AuraFace-v1 | Face recognition | LULUS AUDIT AWAL (risiko dicatat) | Apache-2.0 [V], dilatih pada data komersial/publik agar boleh komersial [V]; cakupan etnis terbatas menurut model card [V]. |
| 6 | SFace (OpenCV Zoo) | Face recognition | TERTAHAN, LISENSI | Apache-2.0 untuk file di direktori [V], dataset latih tidak disebut [V: tidak ada]. |

### Kandidat yang dikeluarkan

| Model | Status | Alasan |
|---|---|---|
| CDCN | TIDAK DILANJUTKAN | Repo tanpa Releases dan bobot RGB siap pakai tidak ditemukan; kode membaca data OULU-NPU olahan (.dat); lisensi hanya riset [V]. Akses OULU-NPU juga dilaporkan bermasalah pada 2022 (isu GitHub; status kini belum diverifikasi). |

## Detektor wajah (komponen pipeline bersama)

| Detektor | Lisensi file | Data latih | Status |
|---|---|---|---|
| RetinaFace Caffe (bawaan MiniFASNet) | Tidak dinyatakan [T] | WIDER Face (dari nama) [T] | Tidak dipakai produksi |
| SCRFD (paket InsightFace/AuraFace) | Nonkomersial [S] | Tidak dirinci | Tidak dipakai |
| YuNet 2023mar (OpenCV Zoo) | MIT [V] | WIDER Face; dilabeli CC-BY-NC-ND-4.0 oleh kartu pihak ketiga [S]; situs resmi WIDER belum diperiksa [T] | **Detektor eksperimen**; TERTAHAN-LISENSI untuk produksi |
| BlazeFace short-range (MediaPipe) | Apache-2.0 [S] | Proprietary Google, tidak diungkap [S] | Kandidat detektor produksi; model card Google belum diverifikasi [T] |

## Keputusan yang dicatat

1. Keenam kandidat (dengan face-antispoof-onnx sebagai pengganti CDCN) diuji penuh dengan protokol yang sama. Kelayakan produksi ditentukan terpisah lewat gerbang lisensi. Jika model berlabel riset menang, minta konfirmasi tertulis sebelum produksi.
2. Jalur eksekusi utama: CPU. GPU RTX 3060 Laptop opsional dan belakangan.
3. Python eksperimen 3.12.10 di samping 3.14.7.
4. Lokasi proyek: `C:\dev\model-research-face`. Dataset besar dapat diarahkan ke D: bila C: tidak cukup (C: sisa sekitar 21 GB, 96% terpakai).
5. Satu detektor yang sama (YuNet) untuk semua model pada eksperimen. Detektor produksi ditentukan terpisah.
6. Pengumpulan data: ponsel masing-masing relawan (kamera depan) sebagai inti; jangkar (ponsel rekan) dan uji stres (kamera depan rusak) opsional. Protokol evaluasi v1.0 dibekukan (tag `protokol-v1.0`).
7. Pengambilan data relawan baru dimulai setelah formulir persetujuan ditandatangani semua relawan.

## Status unduhan dan verifikasi (hasil eksperimen)

| Model / berkas | Ukuran (byte) | SHA-256 | Pembanding | Smoke test (data acak) |
|---|---|---|---|---|
| AuraFace `glintr100.onnx` | 260694151 | a7933ea5330113b01c9b60351d8f4c33003f145d8470ac5f0e52ee2effe25c60 | Cocok dengan nilai resmi Hugging Face [V] | input [batch,3,112,112], output [1,512], embedding perlu L2-normalize |
| MiniFASNet (commit b6d5f04ad78778917853b25c778acef6d5626d15) `2.7_80x80_MiniFASNetV2.pth` | 1849453 | a5eb02e1843f19b5386b953cc4c9f011c3f985d0ee2bb9819eea9a142099bec0 | Sama dengan hash hulu yang dicantumkan pihak ketiga [S] | 434560 parameter, input 80x80, output (1,3) |
| MiniFASNet `4_0_0_80x80_MiniFASNetV1SE.pth` | 1856130 | 84ee1d37d96894d5e82de5a57df044ef80a58be2b218b5ed7cdfd875ec2f5990 | Hash lokal saja | 433586 parameter, input 80x80, output (1,3) |
| MiniFASNet `deploy.prototxt` | 43286 | 5935df8926b4fd8f1be2d9425434e7eaf35d59c92401c72736a65081b3798d33 | Hash lokal saja | tidak dipakai (detektor bawaan) |
| MiniFASNet `Widerface-RetinaFace.caffemodel` | 1866013 | d08338a2c207df16a9c566f767fea67fb43ba6fff76ce11e938fe3fabefb9402 | Hash lokal saja | tidak dipakai (detektor bawaan) |
| YuNet `face_detection_yunet_2023mar.onnx` | 232589 | 8f2383e4dd3cfbb4553ea8718107fc0423210dc964f9f4280604804ed2552fa4 | Cocok dengan nilai mirror [S] | belum diuji |
| SFace `face_recognition_sface_2021dec.onnx` | 38696353 | 0ba9fbfa01b5270c96627c4ef784da859931e02f04419c829e83484087c34e79 | Cocok dengan nilai mirror [S] | input [1,3,112,112], output fc1 [1,128] |
| buffalo_l `w600k_r50.onnx` (dari buffalo_l.zip 288621354 byte, SHA-256 80ffe37d8a5940d59a7384c201a2a38d4741f2f3c51eef46ebb28218a7b0ca2f) | 174383860 | 4c06341c33c2ca1f86781dab0e829f88ad5b64be9fba56e56bc9ebdefc619e43 | Tanpa pembanding resmi | input [batch,3,112,112], output [1,512]; normalisasi input yang benar belum diverifikasi |
| anti-spoof-mn3 | belum diunduh | - | - | - |
| face-antispoof-onnx `best_model.onnx` | belum diunduh (klaim 1,82 MB) | - | - | - |

## Spesifikasi input yang sudah terverifikasi

- MiniFASNet (dari kode): gambar BGR, nilai 0-255 (pembagian 255 dinonaktifkan di kode asli), tanpa Normalize; crop kotak wajah diperbesar sebesar skala (2,7 untuk V2, 4,0 untuk V1SE), resize 80x80 tanpa menjaga rasio; gambar harus rasio 3:4; makna indeks keluaran 0 dan 2 belum terverifikasi (halaman pihak ketiga mengklaim urutan [live, print, replay], bertentangan dengan kode asli yang menganggap indeks 1 asli).
- anti-spoof-mn3 (dokumen OpenVINO): model asli RGB dengan mean/scale tertentu; model konversi BGR; 128x128; kelas 0 = asli, kelas 1 = spoof [V].
- face-antispoof-onnx (README): RGB 128x128, dua kelas (real/spoof), perluasan kotak wajah 1,5x [K]; detail preprocessing akan dipastikan dari kode sebelum dipakai.

## Perangkat uji

Intel i7-11800H (8 core/16 thread), RAM 15,7 GB, RTX 3060 Laptop, Windows 11, Git Bash, Python 3.12.10 (venv), torch 2.15.0+cpu, torchvision 0.29.2+cpu, onnxruntime 1.31.1, opencv-python-headless 5.0.0.93, numpy 2.5.4.

## Pertanyaan terbuka

- #1: lisensi data latih bobot; makna indeks keluaran 0 dan 2.
- #2: cara mengunduh bobot (alat omz_downloader, venv terpisah); status pemeliharaan Open Model Zoo; izin tertulis terkait CelebA-Spoof.
- #3: data latih pastinya (dokumen `DATA_PREPARATION.md` di repo); isi file LICENSE; ukuran dan hash bobot; kode preprocessing.
- #4: perlukah lisensi komersial ke InsightFace; normalisasi input w600k_r50.
- #5: isi file lengkap repo AuraFace dan dataset latih.
- #6: dataset latih bobot ONNX OpenCV Zoo.
- Detektor: lisensi WIDER Face di situs resmi; model card BlazeFace Google.
- Dataset evaluasi publik: syarat akses dan lisensi masing-masing belum dibaca; akses OULU-NPU dilaporkan bermasalah.
