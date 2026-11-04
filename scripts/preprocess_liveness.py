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


def preprocess_antispoof_mn3(img_bgr, bbox_xywh, expansion=1.5, size=128):
    """anti-spoof-mn3 (model asli): RGB, (x - mean) / scale pada skala 0-255.

    ASUMSI (belum terverifikasi): dokumen OMZ tidak menjelaskan cara crop. Di sini dipakai
    crop persegi x1,5 yang sama dengan face-antispoof-onnx. Asumsi ini harus diperiksa
    terhadap kode pelatihan sumbernya sebelum hasil model ini dipakai untuk kesimpulan.
    """
    mod = _load_module("facenox_preprocess", FACENOX_PREPROCESS)
    x, y, w, h = bbox_xywh
    rgb = cv2.cvtColor(img_bgr, cv2.COLOR_BGR2RGB)
    face_crop = mod.crop(rgb, (x, y, x + w, y + h), expansion)
    interp = cv2.INTER_AREA if face_crop.shape[0] > size else cv2.INTER_LINEAR
    face_crop = cv2.resize(face_crop, (size, size), interpolation=interp)
    arr = (face_crop.astype(np.float32) - MN3_MEAN) / MN3_SCALE
    return arr.transpose(2, 0, 1)[None].astype(np.float32)
