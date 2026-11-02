# Audit Model: Liveness Detection dan Face Recognition

Tanggal pemeriksaan sumber: 2 November 2026
Tujuan penggunaan (dikonfirmasi pengguna): model akan dipakai pada fitur absensi aplikasi HRMS mobile, jadi diperlakukan sebagai **target produksi/komersial**.
Catatan: dokumen ini bukan opini hukum. Status lisensi perlu dikonfirmasi penasihat hukum sebelum produksi.

Legenda: [V] terverifikasi dari halaman resmi; [K] klaim vendor/publikasi, belum diukur; [T] belum terverifikasi.

## Tabel keputusan

| # | Model | Kategori | Status audit (target produksi) | Alasan singkat |
|---|---|---|---|---|
| 1 | Silent-Face-Anti-Spoofing (MiniFASNetV2 + V1SE) | Liveness | LULUS AUDIT AWAL (risiko dicatat) | Apache-2.0 [V]. Data latih bobot tidak dijelaskan [V: tidak ada]. Repo terakhir diperbarui Okt 2023. |
| 2 | anti-spoof-mn3 (OpenVINO Open Model Zoo) | Liveness | TERTAHAN, LISENSI | Model MIT [V], tetapi dilatih pada CelebA-Spoof yang nonkomersial [V]. Boleh diuji sebagai pembanding riset. |
| 3 | CDCN | Liveness | RISET SAJA | README resmi: hanya riset, komersial tidak diizinkan [V]. Tidak ada Releases; bobot belum ditemukan [T]. |
| 4 | InsightFace buffalo_l | Face recognition | RISET SAJA | Semua model di model zoo hanya untuk riset nonkomersial [V]. |
| 5 | AuraFace-v1 | Face recognition | LULUS AUDIT AWAL (risiko dicatat) | Apache-2.0 [V], dilatih pada data komersial/publik agar boleh komersial [V]. Cakupan etnis terbatas menurut model card [V]. |
| 6 | SFace (OpenCV Zoo) | Face recognition | TERTAHAN, LISENSI | Apache-2.0 untuk semua file di direktori model [V], tetapi README tidak menyebut dataset latih [V: tidak ada]. |

## Keputusan yang dicatat

1. Keenam kandidat tetap dipertahankan untuk eksperimen. Hanya #1 dan #5 yang berhak dipilih untuk produksi, kecuali ada izin tertulis atau verifikasi hukum untuk #2 dan #6.
2. Jalur eksekusi utama: CPU (backend Frappe kemungkinan CPU). GPU RTX 3060 Laptop opsional dan hanya setelah CPU selesai.
3. Python eksperimen: 3.12 berdampingan dengan 3.14 (3.14 tidak dihapus). Alasan: dukungan wheel 3.14 masih baru dan belum merata; repo MiniFASNet tidak aktif sejak 2023. Perlu divalidasi saat instalasi.
4. Lokasi proyek: C:\dev\model-research-face; dataset besar dapat diarahkan ke D: bila C: tidak cukup.”
5. Urutan kerja eksperimen: #1 dan #5 lebih dulu, lalu pembanding.

## Spesifikasi perangkat uji (tercatat 2 Nov 2026)

- CPU: Intel Core i7-11800H, 8 core / 16 thread
- RAM: 15,7 GB
- GPU: NVIDIA GeForce RTX 3060 Laptop, Intel UHD Graphics
- OS: Windows 11, terminal Git Bash
- Git 2.54.0, Python 3.14.7 (satu-satunya versi terpasang), pip 26.2.1
- Disk: C: sisa 24 GB dari 454 GB; D: sisa 102 GB dari 932 GB

## Pertanyaan terbuka

- #1: versi Python/PyTorch yang didukung kode asli; lisensi data latih detektor RetinaFace bawaan; sumber data latih bobot.
- #2: apakah omz_downloader dan sumber bobot masih berfungsi; status pemeliharaan Open Model Zoo; izin tertulis terkait CelebA-Spoof.
- #3: lokasi bobot di subfolder `CVPR2020_paper_codes` / `FAS_challenge_CVPRW2020` (belum diperiksa); dataset latih.
- #4: apakah lisensi komersial akan diminta ke InsightFace; hanya jika #5 gagal memenuhi kebutuhan.
- #5: nama file dan ukuran ONNX di tab Files; isi file lengkap (apakah ada detektor SCRFD yang nonkomersial); dataset latih tidak dirinci.
- #6: dataset latih bobot ONNX OpenCV Zoo; konfirmasi ke maintainer jika SFace ingin dipertimbangkan produksi.
- Semua: checksum file bobot (dihitung setelah unduh); status lisensi dataset evaluasi publik yang akan dipakai.
