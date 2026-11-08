"""Uji pemotongan tengah 3:4 (reports/amandemen-protokol-2.md). Tanpa data relawan.

1. Gambar sintetis (hitam) berukuran sama dengan ukuran efektif di inventaris: ukuran hasil harus sama
   dengan tabel amandemen, rasio tepat 3:4, offset di tengah, piksel tidak berubah.
2. Rasio tetap tepat 3:4 setelah limit_resolution 640 dan 1280.
3. face.jpg (gambar dokumentasi repo, BUKAN relawan): wajah tetap terdeteksi setelah dipotong.
Jalankan dari akar proyek:  python scripts/test_potong34.py
"""
import numpy as np

from common import create_detector, crop_to_3x4, detect_faces, limit_resolution, load_image

# (lebar, tinggi) -> (lebar, tinggi) harapan; dari amandemen-protokol-2 dan hitungan k = min(w//3, h//4)
HARAPAN = {
    (1884, 4080): (1884, 2512),
    (2296, 4080): (2295, 3060),
    (3120, 4208): (3120, 4160),
    (3072, 4080): (3060, 4080),
    (3000, 4001): (3000, 4000),
    (2316, 3088): (2316, 3088),
    (3024, 4032): (3024, 4032),
    (2448, 3264): (2448, 3264),
    (4896, 6528): (4896, 6528),
    (4080, 3060): (2295, 3060),  # lanskap (tidak ada di data; uji arah sebaliknya)
}

hasil = []


def cek(nama, ok, detail=""):
    print(f"[{'OK' if ok else 'SALAH'}] {nama} {detail}")
    hasil.append(ok)


for (w, h), (ew, eh) in HARAPAN.items():
    img = np.zeros((h, w, 3), dtype=np.uint8)
    img[h // 2, w // 2] = (1, 2, 3)  # penanda di titik tengah gambar asli
    out, info = crop_to_3x4(img)
    oh, ow = out.shape[:2]
    ox, oy = info["crop34_x"], info["crop34_y"]
    ok = ((ow, oh) == (ew, eh) and ow * 4 == oh * 3
          and ox == (w - ow) // 2 and oy == (h - oh) // 2
          and (info["crop34_w"], info["crop34_h"]) == (ow, oh)
          and tuple(out[h // 2 - oy, w // 2 - ox]) == (1, 2, 3)  # penanda tetap ada, tidak bergeser
          and int(out.sum()) == 6 and out.flags["C_CONTIGUOUS"])
    rasio = []
    for ms in (640, 1280):
        r = limit_resolution(out, ms)
        rasio.append(f"{ms}:{r.shape[1]}x{r.shape[0]}")
        ok = ok and r.shape[1] * 4 == r.shape[0] * 3
    cek(f"{w}x{h} -> {ow}x{oh}", ok, f"(harapan {ew}x{eh}; offset {ox},{oy}; {', '.join(rasio)})")

face_path = "repositories/face-antispoof-onnx/assets/docs/face.jpg"
asli = load_image(face_path)
out, info = crop_to_3x4(asli)
det = create_detector()
fa, fb = detect_faces(asli, det), detect_faces(out, det)
ok = len(fa) == 1 and len(fb) == 1
detail = f"(asli {asli.shape[1]}x{asli.shape[0]}, dipotong {out.shape[1]}x{out.shape[0]}, info {info})"
if ok:
    # YuNet tidak menghasilkan kotak identik bila latar di sekitar wajah dipotong (terbukti juga pada
    # skala deteksi yang sama), jadi kriterianya tumpang-tindih kotak, bukan posisi persis.
    # Kotak pada gambar terpotong dikembalikan ke koordinat asli dengan offset lalu dibandingkan (IoU >= 0,9).
    xa, ya, wa, ha = fa[0]["bbox_xywh"]
    xb, yb, wb, hb = fb[0]["bbox_xywh"]
    xb, yb = xb + info["crop34_x"], yb + info["crop34_y"]
    iw = max(0.0, min(xa + wa, xb + wb) - max(xa, xb))
    ih = max(0.0, min(ya + ha, yb + hb) - max(ya, yb))
    iou = iw * ih / (wa * ha + wb * hb - iw * ih)
    ok = iou >= 0.9
    detail += f" skor {fa[0]['score']:.3f} -> {fb[0]['score']:.3f}, IoU kotak {iou:.3f}"
cek("face.jpg wajah tetap terdeteksi", ok, detail)

print("SEMUA OK" if all(hasil) else "ADA YANG SALAH: jangan lanjut, kirim output ini.")
