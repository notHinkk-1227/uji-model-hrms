"""Uji modul pengenalan (recognition.py). Tanpa data relawan: hanya data sintetis dan face.jpg (dokumentasi repo).

1. Umeyama: memulihkan transformasi kemiripan yang diketahui secara eksak; pada data berderau, hasilnya optimum
   kuadrat terkecil (residu tidak pernah lebih besar daripada 2000 transformasi kemiripan hasil gangguan acak).
2. face.jpg: landmark hasil transformasi berada dekat templat ArcFace (RMS dilaporkan; batas 5 px dari 112).
3. Embedding: dimensi 512/512/128, norma 1, deterministik (gambar sama -> cosine 1).
4. Informatif (BUKAN uji lulus, BUKAN pengukuran kinerja): cosine face.jpg vs versinya yang diperkecil,
   dikompres JPEG, dan dicerminkan (identitas sama). Uji "identitas berbeda" tidak dapat dilakukan tanpa wajah
   kedua yang boleh dipakai (aturan privasi).
Jalankan dari akar proyek:  python scripts/test_pengenalan.py
"""
import cv2
import numpy as np

from common import create_detector, crop_to_3x4, detect_faces, load_image, primary_face
from recognition import ARCFACE_DST, RecognitionModels, align_arcface, cosine, similarity_umeyama, template

hasil = []
rng = np.random.default_rng(0)


def cek(nama, ok, detail=""):
    print(f"[{'OK' if ok else 'SALAH'}] {nama} {detail}")
    hasil.append(bool(ok))


def apply(m, pts):
    return pts @ m[:, :2].T + m[:, 2]


def sim_matrix(scale, theta, tx, ty):
    c, s = np.cos(theta), np.sin(theta)
    return np.array([[scale * c, -scale * s, tx], [scale * s, scale * c, ty]])


# 1a. pemulihan eksak
m_true = sim_matrix(0.37, np.deg2rad(-23.0), 41.0, -12.5)
src = rng.uniform(100, 900, size=(5, 2))
m_est = similarity_umeyama(src, apply(m_true, src))
cek("Umeyama memulihkan transformasi eksak", np.abs(m_est - m_true).max() < 1e-9, f"(galat maks {np.abs(m_est - m_true).max():.2e})")

# 1b. optimum kuadrat terkecil pada data berderau
dst = apply(m_true, src) + rng.normal(0, 3.0, size=(5, 2))
m_ls = similarity_umeyama(src, dst)
res = lambda m: ((apply(m, src) - dst) ** 2).sum()
a, b = m_ls[0, 0], m_ls[1, 0]
lebih_baik = 0
for _ in range(2000):
    da, db, dx, dy = rng.normal(0, [0.01, 0.01, 1.0, 1.0])
    mp = np.array([[a + da, -(b + db), m_ls[0, 2] + dx], [b + db, a + da, m_ls[1, 2] + dy]])
    lebih_baik += res(mp) < res(m_ls) - 1e-9
cek("Umeyama optimum kuadrat terkecil", lebih_baik == 0, f"(gangguan dengan residu lebih kecil: {lebih_baik}/2000)")
cek("Umeyama tanpa pencerminan (det > 0)", np.linalg.det(m_ls[:, :2]) > 0)

# 2. face.jpg
img, _ = crop_to_3x4(load_image("repositories/face-antispoof-onnx/assets/docs/face.jpg"))
det = create_detector()
face, n = primary_face(detect_faces(img, det))
cek("face.jpg: 1 wajah", n == 1)
lm = np.asarray(face["landmarks"], dtype=np.float64)
cek("urutan landmark YuNet = urutan templat (mata kiri-gambar dulu, mulut kiri-gambar dulu)",
    lm[0, 0] < lm[1, 0] and lm[3, 0] < lm[4, 0] and lm[2, 1] > lm[0, 1] and lm[3, 1] > lm[2, 1], f"{lm.round(1).tolist()}")
m = similarity_umeyama(lm, ARCFACE_DST)
rms = float(np.sqrt(((apply(m, lm) - ARCFACE_DST) ** 2).sum(1).mean()))
crop = align_arcface(img, lm)
cek("aligned 112x112x3 uint8", crop.shape == (112, 112, 3) and crop.dtype == np.uint8)
cek("RMS landmark ke templat <= 5 px", rms <= 5.0, f"(RMS {rms:.2f} px)")

# 3. embedding
models = RecognitionModels(threads=1)
dim = {"auraface": 512, "buffalo_l": 512, "sface": 128}
emb = {}
for nm in models.NAMES:
    e1 = models.embed(nm, img, face)
    e2 = models.embed(nm, img, face)
    emb[nm] = e1
    cek(f"{nm}: dimensi {dim[nm]}, norma 1, deterministik", e1.shape == (dim[nm],) and abs(np.linalg.norm(e1) - 1) < 1e-6
        and cosine(e1, e2) > 1 - 1e-6, f"(cos sama-gambar {cosine(e1, e2):.6f})")
t = template([emb["auraface"]] * 3)
cek("templat dari embedding identik = embedding itu", cosine(t, emb["auraface"]) > 1 - 1e-9)

# 4. informatif: identitas sama, gambar diubah
varian = {
    "diperkecil 0,5x": cv2.resize(img, None, fx=0.5, fy=0.5, interpolation=cv2.INTER_AREA),
    "JPEG kualitas 60": cv2.imdecode(cv2.imencode(".jpg", img, [cv2.IMWRITE_JPEG_QUALITY, 60])[1], cv2.IMREAD_COLOR),
    "dicerminkan": cv2.flip(img, 1),
}
print("\nInformatif (identitas sama; bukan pengukuran kinerja):")
for vn, vimg in varian.items():
    vf, vn_faces = primary_face(detect_faces(vimg, det))
    if vf is None:
        print(f"  {vn}: wajah tidak terdeteksi")
        continue
    print(f"  {vn}: " + ", ".join(f"{nm} cos {cosine(emb[nm], models.embed(nm, vimg, vf)):.3f}" for nm in models.NAMES))

print(f"\n{sum(hasil)}/{len(hasil)} lolos")
print("SEMUA OK" if all(hasil) else "ADA YANG SALAH: jangan lanjut, kirim output ini.")
