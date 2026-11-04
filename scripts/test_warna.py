"""Uji urutan warna dan skala preprocessing liveness dengan gambar sintetis.

Gambar BGR berwarna biru murni (B=255, G=0, R=0), dengan kotak wajah sembarang di tengah.
Tidak ada data wajah. Jalankan dari akar proyek:
    python scripts/test_warna.py
"""
import numpy as np

from preprocess_liveness import (
    MN3_MEAN,
    MN3_SCALE,
    preprocess_antispoof_mn3,
    preprocess_facenox,
    preprocess_minifasnet,
)

img = np.zeros((480, 640, 3), dtype=np.uint8)
img[:, :, 0] = 255  # kanal 0 BGR = biru
bbox = (240.0, 140.0, 160.0, 200.0)


def rata_kanal(t):
    return [float(t[0, c].mean()) for c in range(3)]


def cek(nama, tensor, harapan, toleransi=1e-3):
    nilai = rata_kanal(tensor)
    ok = all(abs(a - b) <= toleransi for a, b in zip(nilai, harapan))
    print(f"[{'OK' if ok else 'SALAH'}] {nama}: rata-rata kanal {[round(v, 4) for v in nilai]} "
          f"| harapan {[round(v, 4) for v in harapan]}")
    return ok


hasil = []
# MiniFASNet: BGR, 0-255 -> kanal 0 = biru = 255
hasil.append(cek("MiniFASNet V2 (BGR, 0-255)", preprocess_minifasnet(img, bbox, 2.7), [255.0, 0.0, 0.0]))
hasil.append(cek("MiniFASNet V1SE (BGR, 0-255)", preprocess_minifasnet(img, bbox, 4.0), [255.0, 0.0, 0.0]))
# face-antispoof-onnx: RGB, 0-1 -> kanal 2 = biru = 1,0
hasil.append(cek("face-antispoof-onnx (RGB, 0-1)", preprocess_facenox(img, bbox), [0.0, 0.0, 1.0]))
# anti-spoof-mn3: RGB, (x - mean) / scale
mn3_harapan = [(0 - MN3_MEAN[0]) / MN3_SCALE[0], (0 - MN3_MEAN[1]) / MN3_SCALE[1], (255 - MN3_MEAN[2]) / MN3_SCALE[2]]
hasil.append(cek("anti-spoof-mn3 (RGB, mean/scale)", preprocess_antispoof_mn3(img, bbox), mn3_harapan))

print("SEMUA OK" if all(hasil) else "ADA YANG SALAH: jangan lanjut, kirim output ini.")
