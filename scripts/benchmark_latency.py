"""Modul 4: ukur latensi dan memori tiga model liveness di CPU.

Pemakaian (dari akar proyek, venv utama aktif):
  python scripts/benchmark_latency.py --image JALUR --threads 1 --repeat 100 --out results/_uji/latensi_t1.json

Yang diukur (milidetik, setelah warm-up 10 kali, perf_counter):
  detektor_yunet        deteksi wajah pada gambar utuh
  <model>_preprocess    preprocessing (crop, konversi warna, normalisasi) per model
  <model>_inferensi     inferensi saja pada tensor yang sudah siap (tanpa softmax/keputusan)
  <model>_total         preprocessing + inferensi
  minifasnet_ensemble   dua model MiniFASNet berurutan (sesuai cara kode asli memakainya)
Memori: selisih RSS proses sebelum dan sesudah memuat semua model (kasar, termasuk pustaka).
Pengukuran bergantung pada kondisi laptop: colokkan daya, pilih mode performa, tutup aplikasi lain,
ulangi beberapa kali. Angka ini BUKAN angka server produksi.
"""
import argparse
import json
import os
import platform
import sys
import time
from datetime import datetime

import cv2
import numpy as np
import onnxruntime as ort
import psutil
import torch

from common import create_detector, detect_faces, load_image, primary_face
from infer_liveness import LivenessModels
from preprocess_liveness import (
    preprocess_antispoof_mn3,
    preprocess_facenox,
    preprocess_minifasnet,
)


def ukur(fn, repeat, warmup=10):
    for _ in range(warmup):
        fn()
    waktu = []
    for _ in range(repeat):
        t0 = time.perf_counter()
        fn()
        waktu.append((time.perf_counter() - t0) * 1000.0)
    a = np.array(waktu)
    return {
        "median_ms": round(float(np.median(a)), 3),
        "p95_ms": round(float(np.percentile(a, 95)), 3),
        "mean_ms": round(float(a.mean()), 3),
        "min_ms": round(float(a.min()), 3),
        "n": int(repeat),
    }


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--image", required=True)
    ap.add_argument("--threads", type=int, default=1)
    ap.add_argument("--repeat", type=int, default=100)
    ap.add_argument("--out", required=True)
    args = ap.parse_args()

    proses = psutil.Process(os.getpid())
    rss_sebelum = proses.memory_info().rss
    models = LivenessModels(threads=args.threads)
    rss_sesudah = proses.memory_info().rss

    cv2.setNumThreads(args.threads)
    detector = create_detector()
    img = load_image(args.image)
    face, n = primary_face(detect_faces(img, detector))
    if face is None:
        sys.exit("Tidak ada wajah terdeteksi pada gambar; gunakan gambar lain.")
    bbox = face["bbox_xywh"]

    x_mf = {k: torch.from_numpy(preprocess_minifasnet(img, bbox, scale)) for k, (_, scale) in models.minifas.items()}
    x_fx = preprocess_facenox(img, bbox)
    x_mn = preprocess_antispoof_mn3(img, bbox)

    def mf_infer(key):
        def _f():
            with torch.no_grad():
                models.minifas[key][0](x_mf[key])
        return _f

    def mf_prep(key):
        scale = models.minifas[key][1]
        return lambda: preprocess_minifasnet(img, bbox, scale)

    def mf_ensemble():
        for key in models.minifas:
            mf_infer(key)()

    r = args.repeat
    hasil = {"detektor_yunet": ukur(lambda: detect_faces(img, detector), r)}
    for key in models.minifas:
        hasil[f"minifasnet_{key}_preprocess"] = ukur(mf_prep(key), r)
        hasil[f"minifasnet_{key}_inferensi"] = ukur(mf_infer(key), r)
    hasil["minifasnet_ensemble_inferensi"] = ukur(mf_ensemble, r)
    hasil["minifasnet_ensemble_total"] = ukur(
        lambda: ([mf_prep(k)() for k in models.minifas], mf_ensemble()), r)
    hasil["facenox_preprocess"] = ukur(lambda: preprocess_facenox(img, bbox), r)
    hasil["facenox_inferensi"] = ukur(lambda: models.facenox.run(None, {models.facenox_in: x_fx}), r)
    hasil["facenox_total"] = ukur(
        lambda: models.facenox.run(None, {models.facenox_in: preprocess_facenox(img, bbox)}), r)
    hasil["mn3_preprocess"] = ukur(lambda: preprocess_antispoof_mn3(img, bbox), r)
    hasil["mn3_inferensi"] = ukur(lambda: models.mn3.run(None, {models.mn3_in: x_mn}), r)
    hasil["mn3_total"] = ukur(
        lambda: models.mn3.run(None, {models.mn3_in: preprocess_antispoof_mn3(img, bbox)}), r)

    meta = {
        "dibuat": datetime.now().isoformat(timespec="seconds"),
        "gambar": args.image,
        "ukuran_gambar_hw": list(img.shape[:2]),
        "threads": args.threads,
        "ulangan": r,
        "warmup": 10,
        "cpu": platform.processor(),
        "cpu_logis": os.cpu_count(),
        "versi": {"python": sys.version.split()[0], "torch": torch.__version__,
                  "onnxruntime": ort.__version__, "opencv": cv2.__version__, "numpy": np.__version__},
        "memori_rss_mb": {
            "sebelum_muat_model": round(rss_sebelum / 1e6, 1),
            "sesudah_muat_model": round(rss_sesudah / 1e6, 1),
            "selisih": round((rss_sesudah - rss_sebelum) / 1e6, 1),
            "puncak_akhir": round(proses.memory_info().rss / 1e6, 1),
        },
        "catatan": ["Latensi diukur pada laptop pengembangan, bukan server produksi.",
                    "Inferensi tidak termasuk softmax/aturan keputusan (selisih diabaikan).",
                    "Crop anti-spoof-mn3 adalah ASUMSI."],
    }
    os.makedirs(os.path.dirname(args.out) or ".", exist_ok=True)
    with open(args.out, "w", encoding="utf-8") as f:
        json.dump({"meta": meta, "latensi": hasil}, f, indent=2, ensure_ascii=False)

    print(f"threads={args.threads}, ulangan={r}")
    print(f"{'pengukuran':36s} {'median ms':>10s} {'p95 ms':>10s}")
    for nama, s in hasil.items():
        print(f"{nama:36s} {s['median_ms']:10.3f} {s['p95_ms']:10.3f}")
    print("memori RSS (MB):", meta["memori_rss_mb"])
    print("ditulis:", args.out)


if __name__ == "__main__":
    main()
