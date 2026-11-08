# Amandemen 2 untuk Protokol Evaluasi v1.0 (8 November 2026)

Melengkapi v1.0 dan amandemen 1; isi keduanya tidak diubah. Diputuskan peneliti SEBELUM model apa pun
dijalankan pada foto relawan (belum ada skor yang dilihat).

## 1. Pemotongan tengah ke rasio 3:4 sebelum pipeline (semua model)

Dasar:
- Kode asli MiniFASNet (`test.py`, `check_image`) menolak gambar yang rasio lebar/tinggi-nya bukan tepat 3/4.
  Skrip kita memanggil `CropImage` langsung sehingga pemeriksaan itu terlewati [V: kode].
- `CropImage._get_new_box` membatasi skala crop dengan ukuran gambar, sehingga rasio gambar mengubah banyaknya
  konteks di sekitar wajah yang diterima MiniFASNet [V: kode]; besar pengaruhnya pada skor [T].
- Inventaris (`datasets/liveness/internal/inventaris.csv`, ukuran efektif setelah orientasi EXIF): 30 dari 160
  foto liveness bukan 3:4 (toleransi 0,03), SEMUANYA foto serangan: S02 print 10 (2296x4080, 0,563);
  S03 print 10 + screen 10 (1884x4080, 0,462). Tidak ada foto real yang bukan 3:4. Dengan syarat tepat 3/4,
  81 dari 160 tidak lolos (51 sisanya meleset < 1,2%).
- Tanpa pemotongan, rasio gambar berkorelasi dengan kelas, dan hanya MiniFASNet yang berada di luar syarat
  inputnya: perbandingan antarmodel tidak adil. Mengeluarkan 30 foto itu tidak dipilih karena lipatan S03
  akan kehilangan seluruh foto serangan.

Aturan (berlaku untuk semua model liveness dan pengenalan, semua skenario resolusi, foto liveness dan enrollment):
1. Gambar dibaca `cv2.imread` (orientasi EXIF diterapkan), lalu dipotong ke ukuran tepat 3:4:
   `k = min(floor(lebar / 3), floor(tinggi / 4))`, ukuran baru `(3k, 4k)`, dipusatkan dengan offset
   `floor((lebar - 3k) / 2)` dan `floor((tinggi - 4k) / 2)`. Gambar yang sudah tepat 3:4 tidak berubah.
2. Urutan: potong 3:4 -> batas resolusi (640/1280/penuh, amandemen 1) -> deteksi YuNet -> crop per model.
3. Hanya pemotongan; tidak ada pengubahan piksel (kecerahan, warna, ketajaman), sesuai protokol v1.0 bagian 11.
4. Wajah yang ikut terpotong sehingga tidak terdeteksi dilaporkan sebagai kegagalan deteksi, tidak dibuang.
5. Ukuran asli, ukuran setelah dipotong, dan offset dicatat per sampel di CSV hasil.

Perkiraan dampak (dihitung dari ukuran, bukan dari isi gambar): 1884x4080 -> 1884x2512 (tinggi berkurang 38%);
2296x4080 -> 2295x3060 (25%); 3120x4208 -> 3120x4160; 3072x4080 -> 3060x4080; 3000x4001 -> 3000x4000.

Analisis tanpa pemotongan (pilihan "apa adanya") TIDAK dijalankan sebagai analisis sensitivitas (keputusan peneliti).

Implikasi produksi: aplikasi HRMS harus memotret dalam 4:3 atau server menerapkan pemotongan yang sama sebelum
liveness; dicatat untuk analisis kelayakan Frappe.

## 2. Perbedaan pengaturan kamera antara kelas (keterbatasan)

- Pada keempat relawan, ukuran gambar (dan pada S01 juga orientasi EXIF: real 5, serangan 6/1) foto real berbeda
  dari foto serangan [V: inventaris]. Peneliti mengonfirmasi (8 November 2026) bahwa cara pengambilan sesuai
  protokol (kamera depan ponsel relawan). Penyebab perbedaan ukuran tidak diketahui [T] (mis. mode kamera).
- Pemotongan 3:4 menghapus petunjuk rasio; skenario 640/1280 menyamakan resolusi; perbedaan pemrosesan kamera
  tidak dapat dihapus. Dicatat sebagai keterbatasan di laporan.
