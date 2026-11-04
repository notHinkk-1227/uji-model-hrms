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

DETECTOR_CONFIG = {
    "model": "face_detection_yunet_2023mar.onnx",
    "conf_threshold": CONF_THRESHOLD,
    "nms_threshold": NMS_THRESHOLD,
    "top_k": TOP_K,
    "opencv": cv2.__version__,
}


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


def detect_faces(img_bgr, detector):
    """Kembalikan daftar wajah, diurutkan dari yang terbesar.

    Tiap wajah: {"bbox_xywh": (x, y, w, h), "landmarks": array (5, 2), "score": float}.
    Daftar kosong bila tidak ada wajah (dicatat pemanggil sebagai kegagalan deteksi).
    """
    h, w = img_bgr.shape[:2]
    detector.setInputSize((w, h))
    _, faces = detector.detect(img_bgr)
    if faces is None or len(faces) == 0:
        return []
    out = []
    for f in faces:
        x, y, bw, bh = (float(v) for v in f[:4])
        landmarks = np.asarray(f[4:14], dtype=np.float32).reshape(5, 2)
        out.append({"bbox_xywh": (x, y, bw, bh), "landmarks": landmarks, "score": float(f[14])})
    out.sort(key=lambda d: d["bbox_xywh"][2] * d["bbox_xywh"][3], reverse=True)
    return out


def primary_face(faces):
    """Pilih wajah terbesar. Kembalikan (wajah atau None, jumlah wajah)."""
    if not faces:
        return None, 0
    return faces[0], len(faces)
