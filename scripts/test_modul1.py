"""Uji modul 1 (detektor) dan modul 2 (preprocessing liveness).

Hanya memeriksa bahwa kode berjalan dan bentuk/rentang tensor sesuai spesifikasi.
BUKAN pengukuran kinerja model. Jalankan dari akar proyek:
    python scripts/test_modul1.py [jalur_gambar]
"""
import sys

import numpy as np

from common import DETECTOR_CONFIG, create_detector, detect_faces, load_image, primary_face
from preprocess_liveness import (
    MINIFAS_SCALES,
    preprocess_antispoof_mn3,
    preprocess_facenox,
    preprocess_minifasnet,
)

path = sys.argv[1] if len(sys.argv) > 1 else "repositories/face-antispoof-onnx/assets/docs/face.jpg"
print("gambar :", path)
print("detektor:", DETECTOR_CONFIG)

img = load_image(path)
print("ukuran gambar (tinggi, lebar, kanal):", img.shape, "| dtype:", img.dtype)

faces = detect_faces(img, create_detector())
face, n = primary_face(faces)
print("jumlah wajah terdeteksi:", n)
if face is None:
    print("Tidak ada wajah terdeteksi: dicatat sebagai kegagalan deteksi. Uji preprocessing dilewati.")
    sys.exit(0)

bbox = face["bbox_xywh"]
print("wajah terbesar: bbox (x, y, w, h) =", tuple(round(v, 1) for v in bbox), "| skor =", round(face["score"], 3))
print("landmark (5 titik):", np.round(face["landmarks"], 1).tolist())


def laporan(nama, tensor, harapan_bentuk, harapan_rentang):
    ok_bentuk = tensor.shape == harapan_bentuk and tensor.dtype == np.float32
    print(f"[{'OK' if ok_bentuk else 'SALAH'}] {nama}: bentuk {tensor.shape}, dtype {tensor.dtype}, "
          f"min {tensor.min():.3f}, maks {tensor.max():.3f}  (harapan rentang: {harapan_rentang})")


for nama, skala in MINIFAS_SCALES.items():
    laporan(f"MiniFASNet {nama}", preprocess_minifasnet(img, bbox, skala), (1, 3, 80, 80), "0-255, BGR")

laporan("face-antispoof-onnx", preprocess_facenox(img, bbox), (1, 3, 128, 128), "0-1, RGB")
laporan("anti-spoof-mn3 (crop ASUMSI)", preprocess_antispoof_mn3(img, bbox), (1, 3, 128, 128), "sekitar -2 sampai 2, RGB")
