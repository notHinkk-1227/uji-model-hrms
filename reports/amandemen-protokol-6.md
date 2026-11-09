# Amandemen 6 untuk Protokol Evaluasi v1.0 (9 November 2026)

Melengkapi v1.0 dan amandemen 1-5; isinya tidak diubah. Mencatat penyimpangan pengambilan data liveness dan
konsekuensinya (log 2026-11-09, "EXIF foto liveness: foto serangan diambil dengan kamera belakang").

PENTING (transparansi): amandemen ini dibuat SETELAH seluruh hasil liveness terlihat. Penyimpangan ditemukan lewat
pemeriksaan EXIF dan dikonfirmasi peneliti. Amandemen ini tidak mengubah angka hasil apa pun.

## Penyimpangan

Protokol v1.0 baris 7 menyatakan kamera belakang tidak dipakai untuk data uji, dan baris 27 hanya mengizinkan
kamera belakang untuk materi sumber serangan (bukan untuk memotret hasil presentasi serangan). Pada data yang
terkumpul, foto serangan (print dan screen) diambil dengan KAMERA BELAKANG ponsel, sedangkan foto asli diambil
dengan kamera depan.

## Bukti

- Konfirmasi peneliti, 9 November 2026: foto serangan diambil dengan kamera belakang. [V]
- EXIF 160 foto (hanya header; tanpa GPS, tanggal, nomor seri, dan piksel): pada keempat relawan, foto asli dan
  foto serangan memakai lensa berbeda (bukaan dan panjang fokus berbeda). Pada S01 nama lensa menyebut kamera depan
  untuk foto asli dan kamera belakang untuk foto serangan. [V]
- Ukuran asli foto asli dan foto serangan tidak tumpang tindih pada keempat relawan (log 2026-11-09, "Cek confound
  ukuran"). Ini kini dijelaskan oleh perbedaan kamera dan mengoreksi catatan "penyebab tidak diketahui [T]" pada
  amandemen-protokol-2.md.

## Dampak

1. Semua hasil liveness (APCER, BPCER, ACER, AUC, peringkat model, perbandingan berpasangan) membandingkan foto
   kamera depan dengan foto kamera belakang. Model dapat membedakan keduanya dari karakter lensa, bukan dari tanda
   serangan. Besar pengaruhnya belum diukur [T].
2. Hasil liveness tidak mewakili aplikasi HRMS yang hanya memakai kamera depan.
3. Hasil pengenalan wajah TIDAK terdampak (hanya foto asli kamera depan).
4. Foto asli liveness (kamera depan) tetap sahih untuk BPCER, yaitu foto asli yang ditolak. Angka APCER dan semua
   ukuran yang bergantung pada pemisahan asli-serangan tidak sahih.

## Keputusan

1. Hasil liveness 640/1280/penuh TIDAK dipakai sebagai dasar memilih model liveness. Pemilihan MiniFASNet pada
   laporan-akhir.md berstatus belum didukung bukti yang sahih.
2. Berkas hasil (metrik_*.json, skor_*.csv) tidak diubah atau dihapus; tetap sebagai catatan, dengan penafsiran di
   atas.
3. Pengambilan ulang foto serangan dengan kamera depan DITUNDA karena relawan belum tersedia. Belum ada tanggal.

## Syarat bila pengambilan ulang dilakukan

- Amandemen atau protokol baru dibekukan SEBELUM pengambilan.
- Hanya foto serangan yang diulang (print 10 dan screen 10 per relawan, kamera depan, ponsel masing-masing),
  rasio 3:4, JPEG, orientasi dan pengaturan cermin dicatat.
- Model dan OS perangkat dicatat di manifest (kolom sudah ada, sebelumnya berisi penanda "tidak dicatat").
- EXIF diperiksa setelah pengambilan, dan ukuran serta lensa foto asli dan serangan dibandingkan sebelum evaluasi.
- Persetujuan relawan dipastikan masih berlaku.

## Keterbatasan

- Pada S02-S04 tag nama lensa kosong; bahwa foto serangan mereka diambil dengan kamera belakang bertumpu pada
  konfirmasi peneliti dan selisih bukaan dan panjang fokus, bukan pada nama lensa.
- Foto serangan kamera belakang tidak dapat dikonversi menjadi setara kamera depan; tidak ada koreksi statistik
  yang dilakukan.
