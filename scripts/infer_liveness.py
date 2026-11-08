"""Modul 3: jalankan tiga model liveness dan simpan skor mentah per sampel.

Pemakaian (dari akar proyek, venv utama aktif):
  python scripts/infer_liveness.py --image JALUR_GAMBAR
  python scripts/infer_liveness.py --manifest manifest.csv --root FOLDER --out results/liveness/hasil.csv

Manifest: CSV dengan kolom sample_id dan filename. Bila ada kolom subject dan device_code,
jalur gambar = root/subject/device_code/filename; selain itu root/filename.

Skor yang disimpan (aturan keputusan sesuai reports/spesifikasi-preprocessing-v2.md):
  MiniFASNet            softmax 3 kelas per model, rata-rata dua model, real bila argmax = indeks 1
  face-antispoof-onnx   dua logit [real, spoof], diff = real - spoof, real bila diff >= 0
  anti-spoof-mn3        dua probabilitas [real, spoof], real bila p_real > p_spoof
Sebelum pipeline, gambar dipotong tengah ke tepat 3:4 lalu dibatasi resolusinya (--max_side);
lihat reports/amandemen-protokol-2.md. Kolom crop34_* mencatat potongan pada gambar asli.
Tidak ada threshold yang disetel di sini. Waktu proses sengaja tidak diukur (modul latensi terpisah).
"""
import argparse
import csv
import hashlib
import json
import os
import subprocess
import sys
from datetime import datetime

import cv2
import numpy as np
import onnxruntime as ort
import torch
import torch.nn.functional as F

from common import (
    DETECTOR_CONFIG,
    create_detector,
    crop_to_3x4,
    detect_faces,
    limit_resolution,
    load_image,
    primary_face,
)
from preprocess_liveness import (
    _load_module,
    preprocess_antispoof_mn3,
    preprocess_facenox,
    preprocess_minifasnet,
)

MINIFAS_DIR = "repositories/Silent-Face-Anti-Spoofing"
MINIFAS_WEIGHTS = {
    "v2": f"{MINIFAS_DIR}/resources/anti_spoof_models/2.7_80x80_MiniFASNetV2.pth",
    "v1se": f"{MINIFAS_DIR}/resources/anti_spoof_models/4_0_0_80x80_MiniFASNetV1SE.pth",
}
FACENOX_ONNX = "repositories/face-antispoof-onnx/models/best/98.20/best_model.onnx"
MN3_ONNX = "models/anti-spoof-mn3/public/anti-spoof-mn3/anti-spoof-mn3.onnx"

FIELDS = [
    "sample_id", "filename", "status", "n_faces", "det_score",
    "bbox_x", "bbox_y", "bbox_w", "bbox_h", "edge_margin_px", "img_h", "img_w",
    "orig_h", "orig_w", "crop34_x", "crop34_y", "crop34_w", "crop34_h", "max_side",
    "minifas_v2_p0", "minifas_v2_p1", "minifas_v2_p2",
    "minifas_v1se_p0", "minifas_v1se_p1", "minifas_v1se_p2",
    "minifas_avg_p0", "minifas_avg_p1", "minifas_avg_p2", "minifas_pred_real",
    "facenox_logit_real", "facenox_logit_spoof", "facenox_diff", "facenox_pred_real",
    "mn3_p_real", "mn3_p_spoof", "mn3_pred_real",
]


class LivenessModels:
    def __init__(self, threads=None):
        """threads: jumlah thread CPU untuk PyTorch dan ONNX Runtime (None = bawaan pustaka)."""
        ort.set_default_logger_severity(3)
        opts = ort.SessionOptions()
        if threads:
            opts.intra_op_num_threads = int(threads)
            opts.inter_op_num_threads = 1
            torch.set_num_threads(int(threads))
        net = _load_module("minifas_net", f"{MINIFAS_DIR}/src/model_lib/MiniFASNet.py")
        util = _load_module("minifas_util", f"{MINIFAS_DIR}/src/utility.py")
        classes = {"MiniFASNetV2": net.MiniFASNetV2, "MiniFASNetV1SE": net.MiniFASNetV1SE}
        self.minifas = {}
        for key, path in MINIFAS_WEIGHTS.items():
            h, w, mtype, scale = util.parse_model_name(os.path.basename(path))
            model = classes[mtype](conv6_kernel=util.get_kernel(h, w))
            state = torch.load(path, map_location="cpu", weights_only=True)
            if next(iter(state)).startswith("module."):
                state = {k[7:]: v for k, v in state.items()}
            model.load_state_dict(state)
            model.eval()
            self.minifas[key] = (model, scale)
        self.facenox = ort.InferenceSession(FACENOX_ONNX, sess_options=opts, providers=["CPUExecutionProvider"])
        self.facenox_in = self.facenox.get_inputs()[0].name
        self.mn3 = ort.InferenceSession(MN3_ONNX, sess_options=opts, providers=["CPUExecutionProvider"])
        self.mn3_in = self.mn3.get_inputs()[0].name

    def minifas_probs(self, img, bbox):
        out = {}
        for key, (model, scale) in self.minifas.items():
            x = torch.from_numpy(preprocess_minifasnet(img, bbox, scale))
            with torch.no_grad():
                out[key] = F.softmax(model(x), dim=1)[0].numpy()
        return out

    def facenox_logits(self, img, bbox):
        x = preprocess_facenox(img, bbox)
        return self.facenox.run(None, {self.facenox_in: x})[0][0]

    def mn3_probs(self, img, bbox):
        x = preprocess_antispoof_mn3(img, bbox)
        return self.mn3.run(None, {self.mn3_in: x})[0][0]


def score_original(models, detector, orig, max_side=0):
    """Pipeline lengkap dari gambar asli: potong 3:4 (amandemen 2) -> batas resolusi -> score_image."""
    cut, info = crop_to_3x4(orig)
    row = score_image(models, detector, limit_resolution(cut, max_side), orig.shape[:2], max_side)
    row.update(info)
    return row


def score_image(models, detector, img, orig_hw=None, max_side=0):
    """Kembalikan dict skor untuk satu gambar BGR (kolom sesuai FIELDS).

    img adalah gambar yang diproses (setelah batas resolusi); orig_hw ukuran asli (tinggi, lebar).
    """
    row = {k: "" for k in FIELDS}
    h, w = img.shape[:2]
    row["img_h"], row["img_w"] = h, w
    row["orig_h"], row["orig_w"] = orig_hw if orig_hw else (h, w)
    row["max_side"] = max_side if max_side else "penuh"
    faces = detect_faces(img, detector)
    face, n = primary_face(faces)
    row["n_faces"] = n
    if face is None:
        row["status"] = "no_face"
        return row
    bbox = face["bbox_xywh"]
    x, y, bw, bh = bbox
    row["det_score"] = round(face["score"], 4)
    row["bbox_x"], row["bbox_y"], row["bbox_w"], row["bbox_h"] = (round(v, 1) for v in bbox)
    row["edge_margin_px"] = round(min(x, y, w - (x + bw), h - (y + bh)), 1)
    errors = []

    try:
        p = models.minifas_probs(img, bbox)
        avg = (p["v2"] + p["v1se"]) / 2
        for key in ("v2", "v1se"):
            for i in range(3):
                row[f"minifas_{key}_p{i}"] = float(p[key][i])
        for i in range(3):
            row[f"minifas_avg_p{i}"] = float(avg[i])
        row["minifas_pred_real"] = int(np.argmax(avg) == 1)
    except Exception as e:
        errors.append(f"minifas:{type(e).__name__}")

    try:
        logits = models.facenox_logits(img, bbox)
        diff = float(logits[0] - logits[1])
        row["facenox_logit_real"], row["facenox_logit_spoof"] = float(logits[0]), float(logits[1])
        row["facenox_diff"] = diff
        row["facenox_pred_real"] = int(diff >= 0)
    except Exception as e:
        errors.append(f"facenox:{type(e).__name__}")

    try:
        pr = models.mn3_probs(img, bbox)
        row["mn3_p_real"], row["mn3_p_spoof"] = float(pr[0]), float(pr[1])
        row["mn3_pred_real"] = int(pr[0] > pr[1])
    except Exception as e:
        errors.append(f"mn3:{type(e).__name__}")

    row["status"] = "ok" if not errors else "error:" + ",".join(errors)
    return row


def sha256_file(path):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def git_commit():
    try:
        return subprocess.run(["git", "rev-parse", "HEAD"], capture_output=True, text=True, timeout=5).stdout.strip()
    except Exception:
        return ""


def scripts_dirty():
    """True bila folder scripts punya perubahan yang belum di-commit (hash commit tidak mewakili kode)."""
    try:
        out = subprocess.run(["git", "status", "--porcelain", "--", "scripts"],
                             capture_output=True, text=True, timeout=10).stdout
        return bool(out.strip())
    except Exception:
        return None


def write_meta(path, n_rows, max_side=0):
    meta = {
        "dibuat": datetime.now().isoformat(timespec="seconds"),
        "batas_resolusi_sisi_terpanjang_px": max_side if max_side else "penuh (tanpa batas)",
        "git_commit_skrip": git_commit(),
        "skrip_belum_di_commit": scripts_dirty(),
        "jumlah_baris": n_rows,
        "versi": {"python": sys.version.split()[0], "torch": torch.__version__,
                  "onnxruntime": ort.__version__, "opencv": cv2.__version__, "numpy": np.__version__},
        "detektor": DETECTOR_CONFIG,
        "berkas_model_sha256": {
            "minifasnet_v2": sha256_file(MINIFAS_WEIGHTS["v2"]),
            "minifasnet_v1se": sha256_file(MINIFAS_WEIGHTS["v1se"]),
            "face_antispoof_onnx": sha256_file(FACENOX_ONNX),
            "anti_spoof_mn3": sha256_file(MN3_ONNX),
        },
        "aturan_keputusan": {
            "minifasnet": "rata-rata softmax dua model; real bila argmax = indeks 1 (menurut kode asli)",
            "face_antispoof_onnx": "real bila logit_real - logit_spoof >= 0",
            "anti_spoof_mn3": "real bila p_real > p_spoof",
        },
        "catatan": ["Crop anti-spoof-mn3 adalah ASUMSI (persegi x1,5) dan belum diverifikasi.",
                    "Makna indeks keluaran 0 dan 2 MiniFASNet belum diverifikasi.",
                    "Satu detektor YuNet (BGR) dipakai bersama; wajah terbesar dipilih."],
    }
    with open(path, "w", encoding="utf-8") as f:
        json.dump(meta, f, indent=2, ensure_ascii=False)


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--image")
    ap.add_argument("--manifest")
    ap.add_argument("--root", default=".")
    ap.add_argument("--out")
    ap.add_argument("--max_side", type=int, default=0,
                    help="batasi sisi terpanjang gambar (px) sebelum pipeline; 0 = resolusi penuh")
    args = ap.parse_args()
    if not args.image and not (args.manifest and args.out):
        ap.error("gunakan --image, atau --manifest bersama --out")

    models = LivenessModels()
    detector = create_detector()

    if args.image:
        row = score_original(models, detector, load_image(args.image), args.max_side)
        for k in FIELDS:
            print(f"{k:22s} {row[k]}")
        return

    with open(args.manifest, newline="", encoding="utf-8") as f:
        items = list(csv.DictReader(f))
    os.makedirs(os.path.dirname(args.out) or ".", exist_ok=True)
    with open(args.out, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=FIELDS)
        writer.writeheader()
        for i, item in enumerate(items, 1):
            parts = [args.root]
            if item.get("subject") and item.get("device_code"):
                parts += [item["subject"], item["device_code"]]
            path = os.path.join(*parts, item["filename"])
            try:
                row = score_original(models, detector, load_image(path), args.max_side)
            except Exception as e:
                row = {k: "" for k in FIELDS}
                row["status"] = f"error:load:{type(e).__name__}"
            row["sample_id"], row["filename"] = item.get("sample_id", ""), item["filename"]
            writer.writerow(row)
            if i % 25 == 0 or i == len(items):
                print(f"{i}/{len(items)} selesai")
    write_meta(args.out + ".meta.json", len(items), args.max_side)
    print("ditulis:", args.out, "dan", args.out + ".meta.json")


if __name__ == "__main__":
    main()
