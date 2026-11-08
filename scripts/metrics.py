"""Modul 5: metrik evaluasi (fungsi murni; tanpa data, tanpa threshold dari data uji).

Hanya numpy + pustaka standar (tanpa scipy). Diuji dengan scripts/test_metrics.py (data tiruan, jawaban diketahui).

Definisi
  Liveness (ISO/IEC 30107-3; ACER mengikuti protokol OULU-NPU):
    APCER(jenis)  = serangan jenis itu yang DITERIMA sebagai real / jumlah serangan jenis itu
    BPCER         = real yang DITOLAK / jumlah real
    ACER          = (APCER terburuk antarjenis + BPCER) / 2
  Pengenalan (verifikasi 1:1; diterima bila skor >= threshold):
    FAR = pasangan impostor diterima / jumlah impostor;  FRR = pasangan genuine ditolak / jumlah genuine
  AUC: statistik Mann-Whitney (skor lebih tinggi = lebih "positif"; skor sama dihitung 0,5).
  Clopper-Pearson: selang eksak binomial dua sisi; batas dicari dengan bisection pada CDF binomial eksak.
  McNemar eksak: uji binomial dua sisi pada sampel sumbang (benar di satu model, salah di model lain).
  Threshold EER: dari kandidat titik tengah antarskor unik (ditambah dua ujung), pilih |FAR - FRR| terkecil;
    seri dipecah dengan FAR + FRR terkecil, lalu threshold terbesar (lebih ketat).
"""
import math

import numpy as np


# ---------- statistik dasar ----------

def _binom_cdf(k, n, p):
    """P(X <= k) untuk X ~ Binomial(n, p), dihitung eksak lewat log-gamma."""
    if k < 0:
        return 0.0
    if k >= n:
        return 1.0
    if p <= 0.0:
        return 1.0
    if p >= 1.0:
        return 0.0
    lp, lq = math.log(p), math.log1p(-p)
    total = 0.0
    for i in range(k + 1):
        total += math.exp(math.lgamma(n + 1) - math.lgamma(i + 1) - math.lgamma(n - i + 1) + i * lp + (n - i) * lq)
    return min(total, 1.0)


def _bisect(f, lo=0.0, hi=1.0, iters=200):
    """Akar f pada [lo, hi] untuk f menurun monoton (f(lo) > 0 > f(hi))."""
    for _ in range(iters):
        mid = (lo + hi) / 2
        if f(mid) > 0:
            lo = mid
        else:
            hi = mid
    return (lo + hi) / 2


def clopper_pearson(k, n, conf=0.95):
    """Selang kepercayaan eksak (dua sisi) untuk proporsi k/n. Kembalikan (bawah, atas)."""
    if n <= 0:
        return (float("nan"), float("nan"))
    a = (1 - conf) / 2
    # bawah: p dengan P(X >= k) = a;  atas: p dengan P(X <= k) = a  (keduanya fungsi menurun untuk bisection)
    lower = 0.0 if k == 0 else _bisect(lambda p: a - (1 - _binom_cdf(k - 1, n, p)))
    upper = 1.0 if k == n else _bisect(lambda p: _binom_cdf(k, n, p) - a)
    return (lower, upper)


def upper_bound_zero_errors(n, conf=0.95):
    """Batas atas satu sisi bila 0 kesalahan dari n: eksak 1-(1-conf)^(1/n) dan aturan 3/N (95%)."""
    return {"eksak": 1 - (1 - conf) ** (1 / n), "aturan_3_per_n": 3 / n}


def proportion(k, n, conf=0.95):
    """Proporsi k/n beserta jumlah mentah dan selang Clopper-Pearson."""
    lo, hi = clopper_pearson(k, n, conf)
    return {"k": int(k), "n": int(n), "nilai": (k / n) if n else float("nan"), "ci_bawah": lo, "ci_atas": hi}


def auc(scores_pos, scores_neg):
    """AUC Mann-Whitney: peluang skor positif > skor negatif (seri = 0,5)."""
    p = np.asarray(scores_pos, dtype=float)
    q = np.asarray(scores_neg, dtype=float)
    if p.size == 0 or q.size == 0:
        return float("nan")
    gt = (p[:, None] > q[None, :]).sum()
    eq = (p[:, None] == q[None, :]).sum()
    return float((gt + 0.5 * eq) / (p.size * q.size))


def mcnemar_exact(benar_a, benar_b):
    """Perbandingan berpasangan dua model pada sampel yang sama (array boolean 'keputusan benar').

    b = A benar & B salah, c = A salah & B benar; p = 2 * P(X <= min(b, c)), X ~ Bin(b+c, 0,5), maks 1.
    """
    a = np.asarray(benar_a, dtype=bool)
    bb = np.asarray(benar_b, dtype=bool)
    if a.shape != bb.shape:
        raise ValueError("benar_a dan benar_b harus berpasangan (panjang sama)")
    b = int((a & ~bb).sum())
    c = int((~a & bb).sum())
    p = 1.0 if b + c == 0 else min(1.0, 2 * _binom_cdf(min(b, c), b + c, 0.5))
    return {"a_benar_b_salah": b, "a_salah_b_benar": c, "p_value": p}


# ---------- liveness ----------

def liveness_metrics(kelas, pred_real, conf=0.95):
    """kelas: 'real' atau nama jenis serangan per sampel; pred_real: 1 bila model menyatakan real.

    Sampel gagal deteksi/gagal proses TIDAK boleh dimasukkan diam-diam; pemanggil menentukan perlakuannya.
    """
    k = np.asarray(kelas)
    pr = np.asarray(pred_real).astype(int)
    if k.shape != pr.shape:
        raise ValueError("kelas dan pred_real harus sama panjang")
    real = k == "real"
    out = {"bpcer": proportion(int((pr[real] == 0).sum()), int(real.sum()), conf), "apcer": {}}
    for jenis in sorted(set(k[~real].tolist())):
        m = k == jenis
        out["apcer"][jenis] = proportion(int((pr[m] == 1).sum()), int(m.sum()), conf)
    if out["apcer"]:
        terburuk = max(out["apcer"], key=lambda j: out["apcer"][j]["nilai"])
        out["apcer_terburuk"] = terburuk
        out["acer"] = (out["apcer"][terburuk]["nilai"] + out["bpcer"]["nilai"]) / 2
    out["confusion"] = {j: {"diterima_real": int((pr[k == j] == 1).sum()), "ditolak": int((pr[k == j] == 0).sum())}
                        for j in sorted(set(k.tolist()))}
    return out


# ---------- pengenalan ----------

def far_frr(genuine, impostor, threshold, conf=0.95):
    """FAR/FRR pada threshold (diterima bila skor >= threshold), dengan jumlah mentah dan CI."""
    g = np.asarray(genuine, dtype=float)
    i = np.asarray(impostor, dtype=float)
    out = {"threshold": float(threshold),
           "far": proportion(int((i >= threshold).sum()), i.size, conf),
           "frr": proportion(int((g < threshold).sum()), g.size, conf)}
    if out["far"]["k"] == 0 and i.size:
        out["far_batas_atas_tanpa_kesalahan"] = upper_bound_zero_errors(i.size, conf)
    return out


def threshold_eer(pos, neg):
    """Threshold EER dari skor positif (seharusnya diterima) dan negatif (seharusnya ditolak).

    HANYA boleh dipanggil dengan data lipatan latih. Diterima bila skor >= threshold.
    """
    p = np.asarray(pos, dtype=float)
    q = np.asarray(neg, dtype=float)
    u = np.unique(np.concatenate([p, q]))
    kandidat = np.concatenate([[u[0] - 1e-6], (u[:-1] + u[1:]) / 2, [u[-1] + 1e-6]])
    terbaik = None
    for t in kandidat:
        far = float((q >= t).mean())
        frr = float((p < t).mean())
        kunci = (abs(far - frr), far + frr, -t)
        if terbaik is None or kunci < terbaik[0]:
            terbaik = (kunci, float(t))
    return terbaik[1]


# ---------- pembagian data ----------

def loso_folds(subjects):
    """Leave-one-subject-out: hasilkan (subjek_uji, indeks_latih, indeks_uji) untuk tiap subjek."""
    s = np.asarray(subjects)
    for subj in sorted(set(s.tolist())):
        yield subj, np.where(s != subj)[0], np.where(s == subj)[0]
