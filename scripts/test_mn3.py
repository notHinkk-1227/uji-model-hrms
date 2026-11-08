"""Uji crop anti-spoof-mn3 (amandemen 5). Tanpa data relawan, tanpa model.

1. mn3_crop_box sama dengan hitungan tangan dari rumus demo penulis (wrapers.py, commit 82a2c26).
2. Gambar sintetis: area di dalam kotak crop biru, di luar merah -> tensor hasil harus seluruhnya biru
   (membuktikan potongan tepat pada kotak, tanpa padding, tidak dipersegikan).
Jalankan dari akar proyek:  python scripts/test_mn3.py
"""
import numpy as np

from preprocess_liveness import MN3_MEAN, MN3_SCALE, mn3_crop_box, preprocess_antispoof_mn3

hasil = []


def cek(nama, nilai, harapan):
    ok = nilai == harapan
    print(f"[{'OK' if ok else 'SALAH'}] {nama}: {nilai} | harapan {harapan}")
    hasil.append(ok)


# (100.7, 50.2, 80.6, 120.9): int -> 100, 50, 181, 171; w 81, h 121; dw 4,05; dh 3,025
# -> left int(95,95)=95, top int(46,975)=46, right int(185,05)=185, bottom int(174,025)=174
cek("kotak umum", mn3_crop_box((100.7, 50.2, 80.6, 120.9)), (95, 46, 185, 174))
# dekat tepi kiri/atas: (2, 1, 50, 60) -> 2, 1, 52, 61; dw 2,5; dh 1,5 -> max(int(-0,5), 0) = 0
cek("dibatasi >= 0 di kiri/atas", mn3_crop_box((2.0, 1.0, 50.0, 60.0)), (0, 0, 54, 62))

img = np.zeros((300, 400, 3), dtype=np.uint8)
img[:, :, 2] = 255                         # merah (BGR) di mana-mana
l, t, r, b = mn3_crop_box((150.0, 80.0, 90.0, 140.0))
img[t:b, l:r] = (255, 0, 0)                # biru tepat pada kotak crop
x = preprocess_antispoof_mn3(img, (150.0, 80.0, 90.0, 140.0))
biru = (np.array([0, 0, 255], dtype=np.float32) - MN3_MEAN) / MN3_SCALE  # RGB
cek("bentuk tensor", x.shape, (1, 3, 128, 128))
cek("seluruh tensor = biru (crop tepat pada kotak)", bool(np.allclose(x[0].transpose(1, 2, 0), biru, atol=1e-5)), True)
cek("kotak tidak persegi (90x140 -> lebar != tinggi)", (r - l) != (b - t), True)

print(f"\n{sum(hasil)}/{len(hasil)} lolos")
print("SEMUA OK" if all(hasil) else "ADA YANG SALAH: jangan lanjut, kirim output ini.")
