"""Uji sensitivitas detektor terhadap ukuran gambar (gambar dokumentasi, diskalakan)."""
import sys
import time

import cv2
import numpy as np

from common import create_detector, detect_faces, load_image

img = load_image(sys.argv[1] if len(sys.argv) > 1 else "repositories/face-antispoof-onnx/assets/docs/face.jpg")
det = create_detector()
h0, w0 = img.shape[:2]
print("asli:", w0, "x", h0)
for w in [375, 750, 1000, 1500, 2000, 3000, 4032]:
    h = int(round(w * h0 / w0))
    interp = cv2.INTER_AREA if w < w0 else cv2.INTER_CUBIC
    im = cv2.resize(img, (w, h), interpolation=interp)
    waktu = []
    for _ in range(5):
        t = time.perf_counter()
        faces = detect_faces(im, det)
        waktu.append((time.perf_counter() - t) * 1000)
    skor = round(faces[0]["score"], 3) if faces else None
    lebar = round(faces[0]["bbox_xywh"][2]) if faces else None
    print(f"lebar {w:5d} x {h:5d} | wajah: {len(faces)} | skor: {skor} | lebar kotak: {lebar} | median {np.median(waktu):.1f} ms")
