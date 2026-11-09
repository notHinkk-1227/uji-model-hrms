"""Modul 4b: ukur latensi dan memori model pengenalan wajah dan pipeline lengkap di CPU.

Pemakaian (dari akar proyek):
  .venv/Scripts/python.exe scripts/benchmark_recognition.py --image JALUR --threads 1 --repeat 100 --out results/_uji/latensi_rec_t1.json

Yang diukur (milidetik, warm-up 10 kali, perf_counter; fungsi ukur dari benchmark_latency.py):
  <model>_align       alignment (AuraFace dan buffalo_l: 5 titik ArcFace; SFace: alignCrop)
  <model>_inferensi   inferensi saja pada masukan yang sudah siap
  <model>_total       alignment + blob + inferensi + L2-normalize (embed)
  pipeline_yunet_minifasnet_auraface_total   deteksi YuNet + ansambel MiniFASNet + embedding AuraFace
Memori: selisih RSS proses sebelum dan sesudah memuat model (kasar, termasuk pustaka).
Gambar uji HARUS gambar non-relawan (face.jpg). --tinggi membesarkan gambar hasil potong 3:4 ke tinggi tertentu
(SINTETIS, hanya agar ukuran masukan mirip skenario resolusi; bukan foto nyata beresolusi itu).
Angka ini BUKAN angka server produksi.
"""
import argparse
import json
import os
import platform
import sys
from datetime import datetime

import cv2
import numpy as np
import onnxruntime as ort
import psutil
import torch

from benchmark_latency import ukur
from common import create_detector, crop_to_3x4, detect_faces, load_image, primary_face
from infer_liveness import LivenessModels
from preprocess_liveness import preprocess_minifasnet
from recognition import ARCFACE_MEAN, ARCFACE_STD, SIZE, RecognitionModels


def blob_arcface(crop):
    return np.ascontiguousarray(
        cv2.dnn.blobFromImages([crop], 1.0 / ARCFACE_STD, (SIZE, SIZE),
                               (ARCFACE_MEAN, ARCFACE_MEAN, ARCFACE_MEAN), swapRB=True),
        dtype=np.float32)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--image", required=True)
    ap.add_argument("--threads", type=int, default=1)
    ap.add_argument("--repeat", type=int, default=100)
    ap.add_argument("--tinggi", type=int, default=0,
                    help="bila > 0, besarkan gambar 3:4 ke tinggi ini (sintetis); 0 = apa adanya")
    ap.add_argument("--out", required=True)
    args = ap.parse_args()

    proses = psutil.Process(os.getpid())
    rss_awal = proses.memory_info().rss
    rec = RecognitionModels(threads=args.threads)
    rss_rec = proses.memory_info().rss
    lv = LivenessModels(threads=args.threads)
    rss_lv = proses.memory_info().rss

    cv2.setNumThreads(args.threads)
    detector = create_detector()
    img, _ = crop_to_3x4(load_image(args.image))
    if args.tinggi > 0:
        h = int(args.tinggi)
        img = cv2.resize(img, (h * 3 // 4, h), interpolation=cv2.INTER_CUBIC)
    face, _n = primary_face(detect_faces(img, detector))
    if face is None:
        sys.exit("Tidak ada wajah terdeteksi pada gambar; gunakan gambar lain.")

    r = args.repeat
    hasil = {}
    for nm in rec.NAMES:
        crop = rec.aligned(nm, img, face)
        hasil[f"{nm}_align"] = ukur(lambda nm=nm: rec.aligned(nm, img, face), r)
        if nm == "sface":
            hasil[f"{nm}_inferensi"] = ukur(lambda crop=crop: rec.sface.feature(crop), r)
        else:
            sess = rec.arc[nm]
            blob, nama_in = blob_arcface(crop), sess.get_inputs()[0].name
            hasil[f"{nm}_inferensi"] = ukur(lambda sess=sess, blob=blob, nama_in=nama_in: sess.run(None, {nama_in: blob}), r)
        hasil[f"{nm}_total"] = ukur(lambda nm=nm: rec.embed(nm, img, face), r)

    def pipeline():
        f, _ = primary_face(detect_faces(img, detector))
        b = f["bbox_xywh"]
        for model, scale in lv.minifas.values():
            x = torch.from_numpy(preprocess_minifasnet(img, b, scale))
            with torch.no_grad():
                model(x)
        rec.embed("auraface", img, f)

    hasil["pipeline_yunet_minifasnet_auraface_total"] = ukur(pipeline, r)

    meta = {
        "dibuat": datetime.now().isoformat(timespec="seconds"),
        "gambar": args.image,
        "ukuran_gambar_hw": list(img.shape[:2]),
        "gambar_diperbesar_sintetis_tinggi": args.tinggi or None,
        "threads": args.threads,
        "ulangan": r,
        "warmup": 10,
        "cpu": platform.processor(),
        "cpu_logis": os.cpu_count(),
        "versi": {"python": sys.version.split()[0], "torch": torch.__version__,
                  "onnxruntime": ort.__version__, "opencv": cv2.__version__, "numpy": np.__version__},
        "memori_rss_mb": {
            "awal": round(rss_awal / 1e6, 1),
            "sesudah_muat_pengenalan": round(rss_rec / 1e6, 1),
            "sesudah_muat_liveness": round(rss_lv / 1e6, 1),
            "selisih_pengenalan": round((rss_rec - rss_awal) / 1e6, 1),
            "selisih_liveness": round((rss_lv - rss_rec) / 1e6, 1),
            "puncak_akhir": round(proses.memory_info().rss / 1e6, 1),
        },
        "catatan": ["Latensi diukur pada laptop pengembangan, bukan server produksi.",
                    "Gambar uji non-relawan (face.jpg); ukuran gambar dan wajahnya tidak mewakili foto aplikasi.",
                    "Pipeline = YuNet + ansambel MiniFASNet + embedding AuraFace; tanpa perbandingan templat dan tanpa dekode JPEG."],
    }
    os.makedirs(os.path.dirname(args.out) or ".", exist_ok=True)
    with open(args.out, "w", encoding="utf-8") as f:
        json.dump({"meta": meta, "latensi": hasil}, f, indent=2, ensure_ascii=False)

    print(f"threads={args.threads}, ulangan={r}, ukuran gambar (h,w)={img.shape[:2]}")
    print(f"{'pengukuran':44s} {'median ms':>10s} {'p95 ms':>10s}")
    for nama, s in hasil.items():
        print(f"{nama:44s} {s['median_ms']:10.3f} {s['p95_ms']:10.3f}")
    print("memori RSS (MB):", meta["memori_rss_mb"])
    print("ditulis:", args.out)


if __name__ == "__main__":
    main()
