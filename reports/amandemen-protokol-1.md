# Amandemen 1 untuk Protokol Evaluasi v1.0 (5 November 2026)

Melengkapi v1.0; isi v1.0 tidak diubah.

1. Kelas replay tidak dikumpulkan. Alasan peneliti: dianggap mirip dengan kelas screen. Catatan: model uji menilai satu gambar sehingga jejak keduanya sejenis, tetapi replay video berbeda (kompresi, resolusi, blur gerak) dan kesetaraannya TIDAK terbukti. Klaim laporan dibatasi pada serangan cetak dan foto di layar; ketahanan terhadap replay video tidak diuji.
2. Uji stres (ponsel dengan kamera depan rusak) tidak dilakukan (opsional di v1.0).
3. Detektor: deteksi dijalankan pada salinan gambar yang diperkecil (sisi terpanjang maks 640 px) dan koordinat dikembalikan ke gambar asli (detect_max_side = 640). Dasar: YuNet tidak menghasilkan kotak lebih besar dari sekitar 510 px, sehingga gagal pada foto resolusi tinggi.
4. Skenario resolusi: pipeline dijalankan dengan batas sisi terpanjang 640, 1280, dan resolusi penuh. Skenario utama sementara 1280 (ASUMSI) sampai resolusi unggahan aplikasi HRMS diketahui.
5. Kondisi benchmark latensi: charger tercolok, mode daya Turbo, laptop pengembangan (bukan server produksi).
