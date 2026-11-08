"""Preprocessing tiga model liveness, sesuai reports/spesifikasi-preprocessing-v2.md.

Fungsi crop/preprocess milik repositori sumber dipakai langsung (dimuat lewat jalur berkas
dengan nama modul unik agar paket "src" kedua repositori tidak bertabrakan), bukan disalin.

Semua fungsi menerima:
  img_bgr     gambar BGR uint8 (hasil cv2.imread)
  bbox_xywh   kotak wajah (x, y, w, h) dari common.detect_faces
dan mengembalikan tensor float32 berbentuk (1, 3, H, W).
"""
import importlib.util

import cv2
import numpy as np

MINIFAS_GENERATE_PATCHES = "repositories/Silent-Face-Anti-Spoofing/src/generate_patches.py"
FACENOX_PREPROCESS = "repositories/face-antispoof-onnx/src/inference/preprocess.py"

# Skala crop MiniFASNet menurut nama berkas bobot (parse_model_name di repositori sumber)
MINIFAS_SCALES = {"2.7_80x80_MiniFASNetV2": 2.7, "4_0_0_80x80_MiniFASNetV1SE": 4.0}

# anti-spoof-mn3 (dokumen OMZ, model asli): RGB, skala 0-255, (x - mean) / scale
MN3_MEAN = np.array([151.2405, 119.5950, 107.8395], dtype=np.float32)
MN3_SCALE = np.array([63.0105, 56.4570, 55.0035], dtype=np.float32)

_cache = {}


def _load_module(name, path):
    if name not in _cache:
        spec = importlib.util.spec_from_file_location(name, path)
        mod = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(mod)
        _cache[name] = mod
    return _cache[name]


def preprocess_minifasnet(img_bgr, bbox_xywh, scale, size=80):
    """MiniFASNet: BGR, nilai 0-255, tanpa normalisasi, crop berskala (CropImage asli).

    Catatan: repositori asli menghitung lebar kotak sebagai (kanan - kiri + 1); di sini
    lebar/tinggi dari YuNet dibulatkan ke int. Selisih kecil ini dicatat sebagai penyimpangan.
    """
    mod = _load_module("minifas_generate_patches", MINIFAS_GENERATE_PATCHES)
    x, y, w, h = bbox_xywh
    bbox = [int(x), int(y), int(w), int(h)]
    patch = mod.CropImage().crop(
        org_img=img_bgr, bbox=bbox, scale=scale, out_w=size, out_h=size, crop=True
    )
    return patch.transpose(2, 0, 1).astype(np.float32)[None]


def preprocess_facenox(img_bgr, bbox_xywh, expansion=1.5, size=128):
    """face-antispoof-onnx: RGB, nilai 0-1, crop persegi x1,5 dengan padding refleksi."""
    mod = _load_module("facenox_preprocess", FACENOX_PREPROCESS)
    x, y, w, h = bbox_xywh
    rgb = cv2.cvtColor(img_bgr, cv2.COLOR_BGR2RGB)
    face_crop = mod.crop(rgb, (x, y, x + w, y + h), expansion)  # bbox = (x1, y1, x2, y2)
    return mod.preprocess(face_crop, size)[None]


MN3_EXPAND = (1.1, 1.05)  # (lebar, tinggi), FaceDetector.expand_ratio di demo_tools/wrapers.py


def mn3_crop_box(bbox_xywh, expand=MN3_EXPAND):
    """Kotak crop anti-spoof-mn3 (left, top, right, bottom) persis seperti demo penulis (amandemen 5).

    Sumber: kprokofi/light-weight-face-anti-spoofing commit 82a2c26, FaceDetector.__decode_detections.
    """
    x, y, w, h = bbox_xywh
    left, top, right, bottom = int(x), int(y), int(x + w), int(y + h)
    dw = (right - left) * (expand[0] - 1.0) / 2
    dh = (bottom - top) * (expand[1] - 1.0) / 2
    return max(int(left - dw), 0), max(int(top - dh), 0), int(right + dw), int(bottom + dh)


def preprocess_antispoof_mn3(img_bgr, bbox_xywh, size=128):
    """anti-spoof-mn3 (model asli): crop kotak diperluas 1,1 x 1,05 (tidak persegi), resize 128x128 INTER_CUBIC,
    RGB, (x - mean) / scale pada skala 0-255. Terverifikasi dari kode sumber (amandemen 5)."""
    left, top, right, bottom = mn3_crop_box(bbox_xywh)
    face_crop = img_bgr[top:bottom, left:right]  # seperti demo: tepi kanan/bawah dibatasi oleh slicing
    face_crop = cv2.resize(face_crop, (size, size), interpolation=cv2.INTER_CUBIC)
    rgb = cv2.cvtColor(face_crop, cv2.COLOR_BGR2RGB)
    arr = (rgb.astype(np.float32) - MN3_MEAN) / MN3_SCALE
    return arr.transpose(2, 0, 1)[None].astype(np.float32)
