# Amandemen 5 untuk Protokol Evaluasi v1.0 (8 November 2026)

Melengkapi v1.0 dan amandemen 1-4; isinya tidak diubah. Koreksi preprocessing dan aturan keputusan anti-spoof-mn3
berdasarkan kode sumber pelatihan (log 2026-11-08, "Verifikasi preprocessing anti-spoof-mn3").

PENTING (transparansi): amandemen ini dibuat SETELAH hasil skenario 1280 terlihat. Dasar perubahan adalah kode
sumber resmi, bukan hasil: nilai lama adalah ASUMSI/usulan yang sejak awal ditandai [T]. Hasil lama anti-spoof-mn3
dinyatakan tidak berlaku dan tidak dipakai untuk kesimpulan.

Sumber: github.com/kprokofi/light-weight-face-anti-spoofing commit 82a2c26bacff5462c6f9320c34ae0363ccbed497
(MIT, Intel): demo/demo.py, demo_tools/wrapers.py, datasets/celeba_spoof.py, train.py.

## Perubahan

1. Crop (mengikuti demo penulis, FaceDetector.__decode_detections + pred_spoof): kotak YuNet (x, y, w, h) diubah ke
   bilangan bulat left = int(x), top = int(y), right = int(x + w), bottom = int(y + h); dw = (right - left) x 0,1 / 2,
   dh = (bottom - top) x 0,05 / 2; left = max(int(left - dw), 0), top = max(int(top - dh), 0), right = int(right + dw),
   bottom = int(bottom + dh); potongan = gambar[top:bottom, left:right] (tepi kanan/bawah terpotong oleh batas gambar).
   Tidak dipersegikan, tanpa padding. Menggantikan asumsi persegi x1,5 dengan padding refleksi.
2. Resize ke 128x128 dengan INTER_CUBIC (pelatihan dan demo).
3. Warna dan normalisasi tidak berubah: RGB, (x - mean) / scale dengan nilai OMZ (setara dengan konfigurasi sumber).
4. Aturan keputusan bawaan: spoof bila p_spoof > 0,4 (nilai bawaan --spoof_thresh di demo); real bila p_spoof <= 0,4.
   Menggantikan usulan "real bila p_real > p_spoof". Arah perubahan menolak lebih banyak foto (lebih ketat).

## Keterbatasan

- Ketatnya kotak YuNet belum tentu sama dengan kotak anotasi CelebA-Spoof (dipakai saat pelatihan) atau detektor
  OpenVINO face-detection (dipakai demo) [T]. Perbedaan ini tidak dapat dikoreksi tanpa detektor aslinya.
- Model lain (MiniFASNet, face-antispoof-onnx) tidak terpengaruh; skornya harus identik dengan run sebelumnya.
