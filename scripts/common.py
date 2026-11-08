"""Modul bersama: pemuat gambar dan detektor wajah (YuNet 2023mar).

Sesuai reports/spesifikasi-preprocessing-v2.md:
- gambar dibaca dengan cv2.imread (BGR) dan dimasukkan ke detektor dalam BGR;
- satu deteksi per gambar dipakai bersama semua model;
- baris keluaran YuNet: kolom 0-3 = kotak (x, y, lebar, tinggi), kolom 4-13 = 5 landmark,
  kolom 14 = skor.
"""
import cv2
import numpy as np

YUNET_PATH = "models/yunet/face_detection_yunet_2023mar.onnx"
CONF_THRESHOLD = 0.8   # sama dengan referensi face-antispoof-onnx; dicatat di setiap hasil
NMS_THRESHOLD = 0.3
TOP_K = 5000

DETECT_MAX_SIDE = 640  # deteksi pada salinan diperkecil (sisi terpanjang maks 640 px); None = nonaktif

DETECTOR_CONFIG = {
    "model": "face_detection_yunet_2023mar.onnx",
    "conf_threshold": CONF_THRESHOLD,
    "nms_threshold": NMS_THRESHOLD,
    "top_k": TOP_K,
    "detect_max_side": DETECT_MAX_SIDE,
    "pemotongan_rasio": "tengah, tepat 3:4, sebelum batas resolusi (amandemen-protokol-2)",
    "opencv": cv2.__version__,
}


def crop_to_3x4(img_bgr):
    """Potong tengah ke ukuran TEPAT 3:4 (lebar:tinggi); lihat reports/amandemen-protokol-2.md.

    k = min(floor(lebar/3), floor(tinggi/4)); ukuran baru (3k, 4k); offset floor((lebar-3k)/2),
    floor((tinggi-4k)/2). Hanya memotong, tidak mengubah nilai piksel. Gambar yang sudah tepat 3:4
    tidak berubah. Dipanggil setelah load_image dan SEBELUM limit_resolution.

    Mengembalikan (gambar_terpotong, info) dengan info = {"crop34_x", "crop34_y", "crop34_w", "crop34_h"}.
    """
    h, w = img_bgr.shape[:2]
    k = min(w // 3, h // 4)
    if k < 1:
        raise ValueError(f"Gambar terlalu kecil untuk dipotong 3:4: {w}x{h}")
    nw, nh = 3 * k, 4 * k
    ox, oy = (w - nw) // 2, (h - nh) // 2
    out = np.ascontiguousarray(img_bgr[oy:oy + nh, ox:ox + nw])
    return out, {"crop34_x": ox, "crop34_y": oy, "crop34_w": nw, "crop34_h": nh}


def limit_resolution(img_bgr, max_side):
    """Perkecil gambar (INTER_AREA) hingga sisi terpanjang <= max_side; tidak pernah memperbesar.

    max_side 0 atau None = tanpa batas (resolusi penuh). Dipakai untuk skenario resolusi
    (mis. 640, 1280, penuh) sebelum seluruh pipeline; lihat reports/amandemen-protokol-1.md.
    """
    h, w = img_bgr.shape[:2]
    if not max_side or max(h, w) <= max_side:
        return img_bgr
    s = max_side / float(max(h, w))
    return cv2.resize(img_bgr, (int(round(w * s)), int(round(h * s))), interpolation=cv2.INTER_AREA)


def load_image(path):
    """Baca gambar sebagai BGR (uint8). Mengangkat ValueError bila gagal."""
    img = cv2.imread(path)
    if img is None:
        raise ValueError(f"Gagal membaca gambar: {path}")
    return img


def create_detector(model_path=YUNET_PATH):
    return cv2.FaceDetectorYN.create(
        model_path, "", (320, 320), CONF_THRESHOLD, NMS_THRESHOLD, TOP_K
    )


def detect_faces(img_bgr, detector, max_side=DETECT_MAX_SIDE):
    """Kembalikan daftar wajah, diurutkan dari yang terbesar.

    Tiap wajah: {"bbox_xywh": (x, y, w, h), "landmarks": array (5, 2), "score": float}.
    Daftar kosong bila tidak ada wajah (dicatat pemanggil sebagai kegagalan deteksi).

    Bila sisi terpanjang gambar > max_side, deteksi dijalankan pada salinan yang diperkecil
    (INTER_AREA), lalu kotak dan landmark dikembalikan ke koordinat gambar ASLI. Alasan: YuNet
    gagal pada wajah yang sangat besar (lihat catatan 2026-11-05) dan waktu deteksi naik
    seiring jumlah piksel. Crop untuk model liveness/pengenalan tetap diambil dari gambar asli.
    """
    h, w = img_bgr.shape[:2]
    scale = 1.0
    work = img_bgr
    if max_side and max(h, w) > max_side:
        scale = max_side / float(max(h, w))
        work = cv2.resize(img_bgr, (int(round(w * scale)), int(round(h * scale))),
                          interpolation=cv2.INTER_AREA)
    wh, ww = work.shape[:2]
    detector.setInputSize((ww, wh))
    _, faces = detector.detect(work)
    if faces is None or len(faces) == 0:
        return []
    out = []
    for f in faces:
        x, y, bw, bh = (float(v) / scale for v in f[:4])
        landmarks = np.asarray(f[4:14], dtype=np.float32).reshape(5, 2) / scale
        out.append({"bbox_xywh": (x, y, bw, bh), "landmarks": landmarks, "score": float(f[14])})
    out.sort(key=lambda d: d["bbox_xywh"][2] * d["bbox_xywh"][3], reverse=True)
    return out


def primary_face(faces):
    """Pilih wajah terbesar. Kembalikan (wajah atau None, jumlah wajah)."""
    if not faces:
        return None, 0
    return faces[0], len(faces)
