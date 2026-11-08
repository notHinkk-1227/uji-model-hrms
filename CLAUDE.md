# CLAUDE.md: Penelitian Komparatif Liveness Detection dan Face Recognition

Dokumen ini dibaca otomatis oleh Claude Code. Detail lengkap ada di `reports/PRD-penelitian.md`.
Terakhir diperbarui: 6 November 2026.

## Tujuan proyek

Memilih **1 model liveness** (anti-spoofing wajah) dan **1 model face recognition** untuk fitur absensi
aplikasi **HRMS mobile** (backend rencana: Frappe). Target: **produksi/komersial**. Aplikasi hanya memakai
**kamera depan**. Pemilihan harus berdasarkan hasil pengujian aktual, kelayakan lisensi, dan bukti yang dapat
diverifikasi. Jika tidak ada kandidat yang memenuhi syarat, kesimpulannya "belum ada kandidat layak".
Implementasi backend Frappe BUKAN bagian tahap ini (hanya analisis kelayakan).

## Aturan wajib (urutan prioritas)

1. **Privasi data biometrik.** Foto di `datasets/` adalah foto relawan. JANGAN membuka, membaca, menampilkan,
   atau mengirim berkas gambar mana pun di `datasets/` (termasuk lewat tool Read/view). Kode boleh memproses
   gambar secara LOKAL; yang boleh dilihat hanya angka, CSV, dan ringkasan. Satu-satunya gambar wajah yang
   boleh dipakai untuk uji kode: `repositories/face-antispoof-onnx/assets/docs/face.jpg` (bukan relawan).
   Jangan mengunggah data ke layanan apa pun. Jangan membuat kode yang mencetak piksel atau gambar ke terminal.
2. **Gerbang persetujuan.** Jangan menjalankan model pada foto relawan sebelum peneliti mengonfirmasi bahwa
   formulir persetujuan sudah ditandatangani keempat relawan (status: SUDAH DIKONFIRMASI peneliti 8 November 2026; lihat log).
3. **Jangan mengarang hasil.** Bedakan: fakta terverifikasi, klaim sumber, hasil eksperimen aktual, asumsi.
   Jangan menyatakan model berhasil, akurat, atau cepat tanpa pengukuran. Angka benchmark publik tidak boleh
   disamakan dengan hasil kita. Tandai yang belum terverifikasi dengan [T].
4. **Protokol dibekukan.** `reports/protokol-evaluasi-v1.0.md` tidak boleh disunting. Perubahan hanya lewat
   `reports/amandemen-protokol-*.md` bertanggal dan entri di `logs/experiment-log.md`.
5. **Threshold tidak boleh disetel pada data yang sedang diuji.** Evaluasi memakai leave-one-subject-out.
6. **Reproduksibilitas.** Catat versi kode, model (hash SHA-256), pustaka, konfigurasi, dan perintah. Setiap
   modifikasi kode atau keputusan dicatat di `logs/experiment-log.md` (hanya menambah di akhir, jangan
   menulis ulang entri lama; koreksi = entri baru).
7. **Langkah kecil.** Satu langkah per giliran, jelaskan tujuannya, beri perintah Git Bash, tunggu output nyata.
   Jangan menganggap perintah berhasil. Jangan memasang paket atau mengunduh model/dataset tanpa izin.
8. **Lisensi.** Lisensi kode tidak otomatis mencakup bobot dan dataset latih. Jangan menyatakan model aman
   untuk produksi tanpa bukti. Jangan mengganti, menambah, atau menghapus kandidat tanpa alasan tercatat.

## Gaya kerja

- Bahasa: **Indonesia**. Peneliti adalah pemula yang ingin memahami tiap langkah, bukan sekadar menyalin
  perintah: jelaskan tujuan, langkah, cara memverifikasi, dan apa yang dicatat.
- Lingkungan: **Windows 11 + Git Bash**. Perintah harus sesuai Git Bash (jalur `/c/dev/model-research-face`).
- Jangan mengubah beberapa variabel sekaligus saat memperbaiki error; diagnosis dulu dengan langkah berisiko kecil.
- Perubahan kode: tampilkan diff atau ringkasan, jangan menulis ulang berkas penuh tanpa alasan. Commit Git
  setelah satu unit pekerjaan selesai (pesan commit bahasa Indonesia, deskriptif).

## Lingkungan

- Proyek: `C:\dev\model-research-face` (Git Bash: `/c/dev/model-research-face`). Repo Git lokal, tanpa remote.
- Python 3.12.10, venv utama `.venv` (aktifkan: `source .venv/Scripts/activate`). Lingkungan terpisah
  `.venv-omz` hanya untuk alat unduh OpenVINO (jangan dipakai untuk eksperimen).
- Pustaka utama: numpy 2.5.4, onnxruntime 1.31.1, opencv-python-headless 5.0.0 (OpenCV 5), torch 2.15.0+cpu,
  pillow 13, psutil 7. Daftar lengkap: `configs/requirements-stage*.txt`.
- Mesin: i7-11800H (8 core/16 thread), RAM 15,7 GB, RTX 3060 Laptop (tidak dipakai; CPU adalah jalur utama).
  Disk C: terbatas (sisa sekitar 20-30 GB); dataset besar tidak boleh diunduh tanpa izin.
- `.gitignore` mengecualikan `datasets/`, `models/`, `repositories/`, venv, dan berkas bobot.

## Struktur repo

```
audit/            model-audit-v3.md, license-evidence-v2.md (arsip/ = versi lama)
configs/          requirements-stage*.txt
datasets/         DATA RELAWAN (jangan dibaca): liveness/internal/raw/S01..S04/own, recognition/internal/enrollment
logs/             experiment-log.md (kronologi, tambah di akhir), checksums-*.txt
models/           bobot (auraface, buffalo_l, sface, yunet, anti-spoof-mn3)
repositories/     kode sumber MiniFASNet (Silent-Face-Anti-Spoofing) dan face-antispoof-onnx
reports/          protokol-evaluasi-v1.0.md, amandemen-protokol-1.md, amandemen-protokol-2.md (potong 3:4), spesifikasi-preprocessing-v2.md, PRD
results/          hasil evaluasi (results/_uji = uji kode, tidak ikut Git)
scripts/          lihat di bawah
```

## Skrip yang ada (scripts/)

- `common.py`: pemuat gambar (BGR), detektor YuNet bersama (`detect_faces`, deteksi pada salinan sisi terpanjang
  maks 640 px lalu koordinat dikembalikan), `limit_resolution` (skenario 640/1280/penuh).
- `preprocess_liveness.py`: preprocessing per model liveness (memakai fungsi crop repo sumber langsung).
- `infer_liveness.py`: skor mentah tiga model liveness ke CSV + `.meta.json` (opsi `--max_side`, `--manifest`).
- `common.py` juga berisi `crop_to_3x4` (potong tengah tepat 3:4 sebelum pipeline; amandemen 2), diuji `test_potong34.py`.
- `benchmark_latency.py`: latensi (median, p95) dan memori CPU; `test_modul1.py`, `test_warna.py`,
  `test_resolusi.py`: uji kode; `smoke_*.py`: smoke test bobot.
- `rename_foto.py`, `inventaris_data.py`, `periksa_data.py`, `buat_manifest.py`: penataan, pemeriksaan administratif, dan manifest.

Perintah umum (dari akar proyek, venv aktif): `python scripts/infer_liveness.py --image JALUR [--max_side 1280]`,
`python scripts/benchmark_latency.py --image JALUR --threads 1 --repeat 100 --out results/_uji/x.json`.

## Fakta penting yang sudah terverifikasi

Kandidat (status lisensi untuk produksi; lengkap di `audit/model-audit-v3.md`):

| Model | Peran | Status |
|---|---|---|
| MiniFASNet V2 + V1SE (Silent-Face-Anti-Spoofing, commit b6d5f04a) | liveness | LULUS AUDIT AWAL (Apache-2.0; data latih tidak dijelaskan) |
| anti-spoof-mn3 (OpenVINO OMZ) | liveness | TERTAHAN-LISENSI (dilatih pada CelebA-Spoof, nonkomersial) |
| face-antispoof-onnx (facenox, commit 2f8dd93d; pengganti CDCN) | liveness | TERTAHAN-LISENSI sementara (data latih tidak dinyatakan) |
| AuraFace-v1 (`glintr100.onnx`) | recognition | LULUS AUDIT AWAL (Apache-2.0) |
| SFace (OpenCV Zoo) | recognition | TERTAHAN-LISENSI (dataset latih tidak disebut) |
| InsightFace buffalo_l (`w600k_r50.onnx`) | recognition | RISET SAJA (bobot nonkomersial) |
| YuNet 2023mar | detektor bersama | MIT, data WIDER Face berlabel nonkomersial (sekunder): detektor eksperimen |

Spesifikasi preprocessing (rinci di `reports/spesifikasi-preprocessing-v2.md`; tiap model BERBEDA):

- MiniFASNet: BGR, nilai 0-255 tanpa normalisasi, crop berskala (V2 2,7; V1SE 4,0) resize 80x80 (CropImage
  asli), keluaran 3 kelas (indeks 1 = real menurut kode asli; makna indeks 0 dan 2 [T]).
- face-antispoof-onnx: RGB, 0-1, crop persegi x1,5 padding refleksi, 128x128; real bila logit_real - logit_spoof >= 0.
- anti-spoof-mn3: RGB, (x - mean)/scale (mean 151.2405/119.5950/107.8395; scale 63.0105/56.4570/55.0035),
  128x128; indeks 0 = real. **Crop = ASUMSI (belum diverifikasi).**
- AuraFace dan buffalo_l: 112x112, alignment 5 landmark (templat ArcFace), RGB, (x-127,5)/127,5, 512-d, L2-normalize
  [S: kode insightface via salinan; nilai templat belum dibaca]. SFace: alignCrop OpenCV, RGB 0-255 mentah, 128-d.
- YuNet: landmark di kolom 4-13, skor kolom 14; gagal pada wajah > ~510 px sehingga deteksi dilakukan pada salinan 640 px.

## Data (hanya ringkasan, jangan dibuka)

4 relawan (S01-S04), ponsel masing-masing, kamera depan. Per relawan: real 20, print 10, screen 10 (replay dan
uji stres TIDAK dikumpulkan; lihat amandemen-protokol-1.md) + enrollment 5. Foto sangat besar (sisi sampai
~6500 px); 30 foto bukan rasio 3:4; EXIF orientasi 5 dan 0 ditemukan. **Temuan: foto enrollment sama dengan
sebagian foto real (kebocoran enrollment->probe)**: 18 dari 20 identik; foto identik dikecualikan dari probe
(keputusan "B", FINAL, `reports/amandemen-protokol-3.md`): 62 probe, 186 pasangan impostor. Enrollment sesi yang
sama dengan probe dan sebagian redup (bias optimistis, harus dicatat). Semua gambar dipotong 3:4 (amandemen 2).

## Status dan langkah berikutnya (urut)

1. SELESAI 2026-11-08: `periksa_data.py`; persetujuan relawan dikonfirmasi; amandemen 2 (3:4) dan 3 (enrollment).
2. SELESAI 2026-11-08: `manifest.csv` (16 kolom, `scripts/buat_manifest.py`); model ponsel/OS/detail pengaturan tidak dicatat (penanda eksplisit).
3. Modul 5: metrik (APCER/BPCER/ACER/AUC, FAR/FRR, CI Clopper-Pearson, perbandingan berpasangan), diuji dengan data tiruan berlabel.
4. Modul pengenalan wajah: alignment (verifikasi templat ArcFace dari kode resmi insightface), embedding, cosine.
5. Evaluasi leave-one-subject-out pada skenario resolusi 640/1280/penuh (utama sementara 1280 = ASUMSI).
6. Verifikasi asumsi crop anti-spoof-mn3; makna indeks MiniFASNet; lisensi WIDER Face dan BlazeFace (detektor produksi).
7. Laporan akhir + analisis kelayakan integrasi Frappe (desain saja).

Batas klaim di laporan: serangan cetak dan foto di layar saja (replay video tidak diuji); 4 relawan = perbandingan
relatif, bukan estimasi akurasi populasi; FAR di bawah ~1,6% (3/186) tidak dapat dibuktikan; angka latensi dari laptop pengembangan.
