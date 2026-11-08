"""Modul pengenalan wajah: alignment, embedding, templat enrollment, cosine.

Sumber (dibaca langsung 2026-11-08; lihat logs/experiment-log.md):
- ArcFace (AuraFace glintr100, buffalo_l w600k_r50): insightface commit ffa12d315041c0505b077c7ff057ca914bb8dc7e
  python-package/insightface/utils/face_align.py (SHA-256 berkas a8b34ddd...d922): templat ARCFACE_DST, estimate_norm
  (SimilarityTransform skimage), norm_crop (cv2.warpAffine 112x112, borderValue 0);
  python-package/insightface/model_zoo/arcface_onnx.py (SHA-256 89041694...81a9): blobFromImages(1/std, mean, swapRB=True);
  mean = std = 127,5 karena 8 node pertama kedua model tidak memuat Sub/Mul (scripts/onnx_nodes.py).
  Penyimpangan: skimage tidak terpasang; transformasi kemiripan dihitung dengan Umeyama (kuadrat terkecil) di numpy,
  diuji di scripts/test_pengenalan.py.
- SFace: cv2.FaceRecognizerSF (alignCrop dari baris YuNet 15 kolom, feature) sesuai spesifikasi-preprocessing-v2.
Semua embedding dinormalisasi L2. Templat enrollment = rata-rata embedding ternormalisasi, lalu dinormalisasi L2
lagi (keputusan peneliti 2026-11-08). Skor pasangan = cosine (dot product vektor ternormalisasi).
"""
import cv2
import numpy as np
import onnxruntime as ort

AURAFACE_ONNX = "models/auraface/glintr100.onnx"
BUFFALO_ONNX = "models/buffalo_l/w600k_r50.onnx"
SFACE_ONNX = "models/sface/face_recognition_sface_2021dec.onnx"

ARCFACE_DST = np.array([[38.2946, 51.6963], [73.5318, 51.5014], [56.0252, 71.7366],
                        [41.5493, 92.3655], [70.7299, 92.2041]], dtype=np.float32)
ARCFACE_MEAN = 127.5
ARCFACE_STD = 127.5
SIZE = 112


def similarity_umeyama(src, dst):
    """Transformasi kemiripan (skala, rotasi, translasi) kuadrat terkecil src -> dst (Umeyama 1991). Matriks 2x3."""
    src = np.asarray(src, dtype=np.float64)
    dst = np.asarray(dst, dtype=np.float64)
    mu_s, mu_d = src.mean(0), dst.mean(0)
    s, d = src - mu_s, dst - mu_d
    cov = d.T @ s / len(src)
    u, sig, vt = np.linalg.svd(cov)
    e = np.eye(2)
    if np.linalg.det(u) * np.linalg.det(vt) < 0:
        e[1, 1] = -1
    r = u @ e @ vt
    var_s = (s ** 2).sum() / len(src)
    scale = (sig * np.diag(e)).sum() / var_s
    t = mu_d - scale * r @ mu_s
    return np.hstack([scale * r, t[:, None]])


def align_arcface(img_bgr, landmarks):
    """norm_crop insightface: 5 landmark (urutan YuNet = urutan templat) -> wajah 112x112 BGR."""
    m = similarity_umeyama(landmarks, ARCFACE_DST)
    return cv2.warpAffine(img_bgr, m, (SIZE, SIZE), borderValue=0.0)


def l2n(v):
    v = np.asarray(v, dtype=np.float64).ravel()
    return v / np.linalg.norm(v)


def template(embeddings):
    """Templat enrollment: rata-rata embedding ternormalisasi, dinormalisasi L2 lagi."""
    return l2n(np.mean([l2n(e) for e in embeddings], axis=0))


def cosine(a, b):
    return float(np.dot(l2n(a), l2n(b)))


def yunet_row(face):
    """Bangun kembali baris YuNet (x, y, w, h, 10 landmark, skor) dari keluaran common.detect_faces."""
    return np.array([*face["bbox_xywh"], *np.asarray(face["landmarks"]).ravel(), face["score"]],
                    dtype=np.float32).reshape(1, 15)


class RecognitionModels:
    NAMES = ("auraface", "buffalo_l", "sface")

    def __init__(self, threads=None):
        ort.set_default_logger_severity(3)
        opts = ort.SessionOptions()
        if threads:
            opts.intra_op_num_threads = int(threads)
            opts.inter_op_num_threads = 1
        prov = ["CPUExecutionProvider"]
        self.arc = {"auraface": ort.InferenceSession(AURAFACE_ONNX, sess_options=opts, providers=prov),
                    "buffalo_l": ort.InferenceSession(BUFFALO_ONNX, sess_options=opts, providers=prov)}
        self.sface = cv2.FaceRecognizerSF.create(SFACE_ONNX, "")

    def aligned(self, name, img_bgr, face):
        if name == "sface":
            return self.sface.alignCrop(img_bgr, yunet_row(face))
        return align_arcface(img_bgr, face["landmarks"])

    def embed(self, name, img_bgr, face):
        """Embedding ternormalisasi L2 untuk satu wajah (face dari common.detect_faces pada img_bgr)."""
        crop = self.aligned(name, img_bgr, face)
        if name == "sface":
            return l2n(self.sface.feature(crop))
        sess = self.arc[name]
        blob = cv2.dnn.blobFromImages([crop], 1.0 / ARCFACE_STD, (SIZE, SIZE),
                                      (ARCFACE_MEAN, ARCFACE_MEAN, ARCFACE_MEAN), swapRB=True)
        out = sess.run(None, {sess.get_inputs()[0].name: np.ascontiguousarray(blob, dtype=np.float32)})[0]
        return l2n(out)
