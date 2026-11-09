# Serah Terima Penelitian (revisi 3, 9 November 2026)

Cara pakai: baca `CLAUDE.md` lebih dulu (aturan wajib), lalu dokumen ini. Claude Code membaca `CLAUDE.md` otomatis; asisten
obrolan biasa perlu diberi kedua berkas ini (tempel isinya). Verifikasi kondisi nyata lewat `git log`, `git status`, dan
`logs/experiment-log.md`, bukan hanya dokumen ini. Menggantikan handover-penelitian-v2.md (di `reports/arsip/`, usang).

## 1. Posisi saat ini

- Tujuan, kandidat, dan batas klaim: lihat `CLAUDE.md` dan `reports/PRD-penelitian.md` (v1.1).
- Hasil terkini: `reports/laporan-akhir.md` (v1.3.1, DRAF menunggu tinjauan peneliti).
  - Pengenalan: AuraFace layak bersyarat (AUC 1,0, celah skor sempit).
  - Liveness: BELUM ADA KESIMPULAN sah; foto serangan diambil dengan kamera belakang (`reports/amandemen-protokol-6.md`).
  - Detektor produksi: belum ada (BlazeFace belum diuji).
  - Latensi pengenalan dan pipeline sudah diukur di laptop pengembangan (`results/latensi/`, entri log 2026-11-09).
- Target peneliti: seluruh pekerjaan yang mungkin diselesaikan paling lambat akhir pekan 15 November 2026; selesai lebih awal tidak masalah.

## 2. Lingkungan kerja (penting)

- Pekerjaan dilakukan di SALINAN `D:\dev\model-research-face-cc` (Git Bash: `/d/dev/model-research-face-cc`), bukan proyek utama di C:. Peneliti sengaja memakai salinan agar proyek utama aman.
- `git push` DITUNDA: salinan masih menunjuk ke remote GitHub yang sama; visibilitas repo belum diverifikasi dan belum dipastikan formulir persetujuan mengizinkan data turunan disimpan di sana. Jangan push tanpa persetujuan peneliti.
- Prompt peneliti bisa menampilkan `(.venv)` milik proyek C:. Untuk perintah yang menjalankan kode, panggil langsung `.venv/Scripts/python.exe` (diverifikasi memakai D:\dev\model-research-face-cc\.venv).
- Peringatan "LF will be replaced by CRLF" dari Git tidak berbahaya. Skrip penyunting teks memeriksa tiap teks lama muncul tepat satu kali sebelum menulis; pakai pola itu.
- Jangan membuka, membaca, atau menampilkan foto di `datasets/` (CLAUDE.md aturan 1). Gambar uji kode hanya `repositories/face-antispoof-onnx/assets/docs/face.jpg`.

## 3. Pekerjaan berikutnya (urut)

1. Amandemen 7 (`reports/amandemen-protokol-7.md`, DRAF): peneliti membaca dan menyetujui, lalu dibekukan (ubah baris STATUS, commit) SEBELUM foto diambil.
2. Pengambilan ulang foto serangan dengan kamera DEPAN (print 10, screen 10 per relawan; 80 foto) mengikuti amandemen 7. Bergantung pada jadwal relawan (belum ada tanggal).
3. Sebelum evaluasi: periksa EXIF, ukuran, dan lensa foto asli vs serangan baru (syarat lolos di amandemen 7 bagian 4). Lalu jalankan ulang evaluasi liveness 640/1280/penuh ke berkas hasil terpisah, dan revisi laporan ke v1.4.
4. Uji BlazeFace dan sumber landmark: BELUM diizinkan. Perlu izin peneliti untuk mengunduh bobot dan memasang paket (usulan: venv terpisah, catat hash dan versi). BlazeFace hanya 6 titik; alignment 5 titik AuraFace tidak langsung berlaku.
5. Opsional: ukur memori AuraFace sendirian (angka sekarang gabungan tiga model).
6. Tinjauan hukum (lisensi bobot dan data latih, model card BlazeFace, UU PDP) dan konfirmasi persetujuan relawan untuk data turunan di GitHub: di tangan peneliti dan pihak lain.

## 4. Keputusan peneliti yang masih terbuka

- Menyetujui isi amandemen 7 (hanya foto serangan diulang; hasil lama tidak digabung; syarat lolos EXIF).
- Menambah relawan dan serangan replay: disarankan TIDAK minggu ini (harus protokol baru).
- Mengizinkan unduhan dan pemasangan untuk uji BlazeFace.
- Menyetujui laporan v1.3.1 sebagai final atau meminta revisi.

## 5. Cara bekerja dengan peneliti

- Bahasa Indonesia; peneliti pemula, jelaskan tujuan, langkah, cara memverifikasi, dan apa yang dicatat.
- Satu langkah kecil per giliran, perintah Git Bash, tunggu keluaran nyata; jangan menganggap perintah berhasil.
- Setiap perubahan kode atau keputusan dicatat sebagai entri baru di akhir `logs/experiment-log.md`; commit setelah satu unit pekerjaan, pesan bahasa Indonesia.
- Jangan memasang paket atau mengunduh apa pun tanpa izin; jangan mengarang hasil; tandai yang belum terverifikasi dengan [T].
