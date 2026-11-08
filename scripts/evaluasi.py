"""Modul 6: evaluasi penuh (K9) sesuai protokol v1.0 + amandemen 1-4.

Tiga sub-perintah (dari akar proyek, venv aktif):
  python scripts/evaluasi.py liveness --scores results/liveness/skor_1280.csv --out results/liveness/metrik_1280.json
  python scripts/evaluasi.py embed --max_side 1280 --out results/recognition/emb_1280.npz
  python scripts/evaluasi.py recognition --emb results/recognition/emb_1280.npz --out results/recognition/metrik_1280.json
Skor liveness dibuat lebih dulu dengan infer_liveness.py --manifest (potong 3:4 dan batas resolusi di sana).

Aturan (amandemen 4):
- Liveness utama: aturan bawaan tiap model (kolom *_pred_real), tanpa threshold dari data.
- Liveness tambahan: threshold EER per lipatan LOSO dari relawan latih (real vs semua serangan), plus AUC.
- Pengenalan: templat = rata-rata embedding enrollment ternormalisasi; threshold EER per lipatan LOSO dari pasangan
  yang probe DAN identitas klaimnya relawan latih; pasangan uji = probe relawan uji vs keempat templat.
- Gagal deteksi/proses = DITOLAK: keputusan 0 (liveness: real -> kesalahan BPCER, serangan -> benar;
  pengenalan: genuine -> FRR, impostor -> benar); AUC memberi skor -inf. Sampel gagal TIDAK dipakai untuk
  menentukan threshold (tidak ada skor). Jumlah kegagalan dilaporkan.
"""
import argparse
import csv
import json
import math
import os
import sys
from collections import Counter
from datetime import datetime

import numpy as np

import metrics as M

MANIFEST = "datasets/liveness/internal/manifest.csv"
RAW = "datasets/liveness/internal/raw"
ENROLL = "datasets/recognition/internal/enrollment"
DUPLIKAT = "datasets/recognition/internal/duplikat_enrollment.csv"

LIVENESS_MODELS = {  # nama: (kolom skor kontinu "makin besar makin real", kolom keputusan bawaan)
    "minifasnet": ("minifas_avg_p1", "minifas_pred_real"),
    "face_antispoof_onnx": ("facenox_diff", "facenox_pred_real"),
    "anti_spoof_mn3": ("mn3_p_real", "mn3_pred_real"),
}


def _bersih(o):
    """Ubah tipe numpy/inf/nan agar dapat ditulis JSON."""
    if isinstance(o, dict):
        return {str(k): _bersih(v) for k, v in o.items()}
    if isinstance(o, (list, tuple)):
        return [_bersih(v) for v in o]
    if isinstance(o, (np.integer,)):
        return int(o)
    if isinstance(o, (np.floating, float)):
        f = float(o)
        return None if (math.isnan(f) or math.isinf(f)) else f
    if isinstance(o, np.bool_):
        return bool(o)
    return o


def read_csv(path):
    with open(path, newline="", encoding="utf-8") as f:
        return list(csv.DictReader(f))


# ======================= LIVENESS =======================

def liveness_table(manifest_rows, score_rows):
    """Gabungkan manifest dan skor per sample_id. Berhenti bila ada sampel manifest tanpa skor (tidak diam-diam)."""
    skor = {r["sample_id"]: r for r in score_rows}
    hilang = [m["sample_id"] for m in manifest_rows if m["sample_id"] not in skor]
    if hilang:
        raise ValueError(f"{len(hilang)} sampel manifest tidak punya skor, mis. {hilang[:3]}")
    tabel = []
    for m in manifest_rows:
        s = skor[m["sample_id"]]
        row = {"sample_id": m["sample_id"], "subject": m["subject"], "class": m["class"],
               "lighting": m["lighting"], "status": s["status"]}
        for nm, (kol_skor, kol_pred) in LIVENESS_MODELS.items():
            ok = s.get(kol_pred, "") not in ("", None) and s.get(kol_skor, "") not in ("", None)
            row[f"{nm}_gagal"] = not ok
            row[f"{nm}_pred"] = int(s[kol_pred]) if ok else 0          # gagal = ditolak
            row[f"{nm}_score"] = float(s[kol_skor]) if ok else -math.inf  # gagal = paling "spoof"
        tabel.append(row)
    return tabel


def _per_kelompok(tabel, nm, kunci):
    out = {}
    for g in sorted({r[kunci] for r in tabel}):
        sub = [r for r in tabel if r[kunci] == g]
        out[g] = M.liveness_metrics([r["class"] for r in sub], [r[f"{nm}_pred"] for r in sub])
    return out


def liveness_eval(tabel):
    hasil = {"jumlah_sampel": len(tabel), "kelas": dict(Counter(r["class"] for r in tabel)),
             "status": dict(Counter(r["status"] for r in tabel)), "model": {}}
    kelas = [r["class"] for r in tabel]
    benar = {}
    for nm in LIVENESS_MODELS:
        pred = [r[f"{nm}_pred"] for r in tabel]
        sc = np.array([r[f"{nm}_score"] for r in tabel])
        real = np.array([c == "real" for c in kelas])
        gagal = [r for r in tabel if r[f"{nm}_gagal"]]
        h = {"gagal": {"jumlah": len(gagal), "per_kelas": dict(Counter(r["class"] for r in gagal)),
                       "per_relawan": dict(Counter(r["subject"] for r in gagal))},
             "utama_aturan_bawaan": M.liveness_metrics(kelas, pred),
             "per_relawan": _per_kelompok(tabel, nm, "subject"),
             "per_cahaya": _per_kelompok(tabel, nm, "lighting"),
             "auc_gabungan": M.auc(sc[real], sc[~real])}
        # tambahan: threshold EER per lipatan LOSO dari relawan latih (sampel gagal tidak ikut menentukan threshold)
        subj = np.array([r["subject"] for r in tabel])
        pred_eer = np.zeros(len(tabel), dtype=int)
        lipatan = {}
        for s, tr, te in M.loso_folds(subj):
            tr_ok = [i for i in tr if not tabel[i][f"{nm}_gagal"]]
            t = M.threshold_eer(sc[[i for i in tr_ok if real[i]]], sc[[i for i in tr_ok if not real[i]]])
            for i in te:
                pred_eer[i] = int((not tabel[i][f"{nm}_gagal"]) and sc[i] >= t)
            lipatan[s] = {"threshold": t, "auc_uji": M.auc(sc[te][real[te]], sc[te][~real[te]])}
        h["tambahan_eer_loso"] = {"lipatan": lipatan, "metrik_gabungan": M.liveness_metrics(kelas, pred_eer.tolist())}
        hasil["model"][nm] = h
        benar[nm] = [(p == 1) == (c == "real") for p, c in zip(pred, kelas)]
    nama = list(LIVENESS_MODELS)
    hasil["berpasangan_mcnemar_aturan_bawaan"] = {
        f"{a}_vs_{b}": M.mcnemar_exact(benar[a], benar[b]) for i, a in enumerate(nama) for b in nama[i + 1:]}
    return hasil


# ======================= PENGENALAN =======================

def probe_list(manifest_rows, duplikat_rows):
    """Probe = kelas real yang tidak identik dengan foto enrollment (amandemen 3)."""
    dup = {os.path.basename(r["berkas_raw_identik"].replace("\\", "/")) for r in duplikat_rows}
    return [m for m in manifest_rows if m["class"] == "real" and m["filename"] not in dup]


def recognition_pairs(probes, emb_probe, emb_enroll):
    """probes: list dict (sample_id, subject, lighting); emb_probe: {sample_id: vektor atau None};
    emb_enroll: {subject: [vektor, ...]} (hanya enrollment yang berhasil). Kembalikan (pasangan, templat)."""
    templat = {}
    for s, embs in sorted(emb_enroll.items()):
        if not embs:
            raise ValueError(f"semua foto enrollment {s} gagal; harus diputuskan dulu (amandemen 4)")
        templat[s] = _template(embs)
    pairs = []
    for p in probes:
        e = emb_probe.get(p["sample_id"])
        for s, t in templat.items():
            pairs.append({"probe": p["sample_id"], "probe_subject": p["subject"], "claim": s,
                          "lighting": p["lighting"], "genuine": p["subject"] == s,
                          "gagal": e is None, "score": -math.inf if e is None else float(np.dot(e, t))})
    return pairs, templat


def _template(embs):
    v = np.mean([np.asarray(e, dtype=np.float64) / np.linalg.norm(e) for e in embs], axis=0)
    return v / np.linalg.norm(v)


def _far_frr_pairs(pairs, thr_per_pair):
    g = [p for p in pairs if p["genuine"]]
    im = [p for p in pairs if not p["genuine"]]
    fr = sum(1 for p in g if p["gagal"] or p["score"] < thr_per_pair(p))
    fa = sum(1 for p in im if (not p["gagal"]) and p["score"] >= thr_per_pair(p))
    out = {"frr": M.proportion(fr, len(g)), "far": M.proportion(fa, len(im))}
    if fa == 0 and im:
        out["far_batas_atas_tanpa_kesalahan"] = M.upper_bound_zero_errors(len(im))
    return out


def recognition_eval(pairs):
    subj = sorted({p["probe_subject"] for p in pairs})
    lipatan, thr = {}, {}
    for s in subj:
        latih = [p for p in pairs if p["probe_subject"] != s and p["claim"] != s and not p["gagal"]]
        t = M.threshold_eer([p["score"] for p in latih if p["genuine"]], [p["score"] for p in latih if not p["genuine"]])
        uji = [p for p in pairs if p["probe_subject"] == s]
        thr[s] = t
        lipatan[s] = {"threshold": t, "pasangan_latih_genuine": sum(p["genuine"] for p in latih),
                      "pasangan_latih_impostor": sum(not p["genuine"] for p in latih),
                      **_far_frr_pairs(uji, lambda p: t)}
    by = lambda p: thr[p["probe_subject"]]
    sc = np.array([p["score"] for p in pairs])
    gen = np.array([p["genuine"] for p in pairs])
    return {"jumlah_pasangan": {"genuine": int(gen.sum()), "impostor": int((~gen).sum())},
            "probe_gagal": len({p["probe"] for p in pairs if p["gagal"]}),
            "gabungan_loso": _far_frr_pairs(pairs, by),
            "per_cahaya": {c: _far_frr_pairs([p for p in pairs if p["lighting"] == c], by)
                           for c in sorted({p["lighting"] for p in pairs})},
            "lipatan": lipatan,
            "auc_gabungan": M.auc(sc[gen], sc[~gen]),
            "skor_genuine_median": float(np.median(sc[gen & np.isfinite(sc)])) if (gen & np.isfinite(sc)).any() else None,
            "skor_impostor_median": float(np.median(sc[~gen & np.isfinite(sc)])) if (~gen & np.isfinite(sc)).any() else None}


# ======================= INFERENSI EMBEDDING =======================

def embed_all(max_side, threads=None):
    """Embedding semua probe dan enrollment untuk tiga model (berat; tidak dipakai di uji data palsu)."""
    from common import create_detector, crop_to_3x4, detect_faces, limit_resolution, load_image, primary_face
    from recognition import RecognitionModels
    models, det = RecognitionModels(threads=threads), create_detector()
    man = read_csv(MANIFEST)
    probes = probe_list(man, read_csv(DUPLIKAT))
    items = [("probe", p["sample_id"], p["subject"], os.path.join(RAW, p["subject"], p["device_code"], p["filename"]))
             for p in probes]
    for s in sorted(os.listdir(ENROLL)):
        for f in sorted(os.listdir(os.path.join(ENROLL, s))):
            items.append(("enroll", os.path.splitext(f)[0], s, os.path.join(ENROLL, s, f)))
    data = {"jenis": [], "id": [], "subject": [], "status": [], "n_faces": []}
    emb = {nm: [] for nm in models.NAMES}
    for k, (jenis, sid, subj, path) in enumerate(items, 1):
        status, n = "ok", 0
        try:
            img = limit_resolution(crop_to_3x4(load_image(path))[0], max_side)
            face, n = primary_face(detect_faces(img, det))
            if face is None:
                status = "no_face"
        except Exception as e:
            status, face = f"error:load:{type(e).__name__}", None
        for nm in models.NAMES:
            v = None
            if face is not None:
                try:
                    v = models.embed(nm, img, face)
                except Exception:
                    v = None
            dim = 128 if nm == "sface" else 512
            emb[nm].append(np.full(dim, np.nan) if v is None else v)
        for key, val in zip(data, (jenis, sid, subj, status, n)):
            data[key].append(val)
        if k % 20 == 0 or k == len(items):
            print(f"{k}/{len(items)} selesai")
    return data, {nm: np.array(v) for nm, v in emb.items()}


def recognition_from_npz(path):
    z = np.load(path, allow_pickle=False)
    meta = json.loads(str(z["meta"]))
    man = {m["sample_id"]: m for m in read_csv(MANIFEST)}
    hasil = {}
    for nm in meta["models"]:
        E = z[nm]
        emb_probe, emb_enroll, probes = {}, {}, []
        for i, (jenis, sid, subj) in enumerate(zip(meta["jenis"], meta["id"], meta["subject"])):
            v = None if np.isnan(E[i]).any() else E[i]
            if jenis == "probe":
                probes.append({"sample_id": sid, "subject": subj, "lighting": man[sid]["lighting"]})
                emb_probe[sid] = v
            else:
                emb_enroll.setdefault(subj, [])
                if v is not None:
                    emb_enroll[subj].append(v)
        pairs, _ = recognition_pairs(probes, emb_probe, emb_enroll)
        hasil[nm] = {"enrollment_dipakai": {s: len(v) for s, v in emb_enroll.items()}, **recognition_eval(pairs)}
    return {"sumber_embedding": path, "status_deteksi": dict(Counter(meta["status"])), "model": hasil}


def jejak_embed(threads):
    """Jejak reproduksibilitas (aturan 6): commit kode, status kode, versi pustaka, hash bobot, konfigurasi."""
    import cv2
    import onnxruntime as ort
    from common import DETECTOR_CONFIG
    from infer_liveness import git_commit, scripts_dirty, sha256_file
    from recognition import AURAFACE_ONNX, BUFFALO_ONNX, SFACE_ONNX
    return {"git_commit_skrip": git_commit(), "skrip_belum_di_commit": scripts_dirty(), "threads": threads,
            "versi": {"python": sys.version.split()[0], "numpy": np.__version__, "onnxruntime": ort.__version__,
                      "opencv": cv2.__version__},
            "detektor": DETECTOR_CONFIG,
            "berkas_model_sha256": {"auraface": sha256_file(AURAFACE_ONNX), "buffalo_l": sha256_file(BUFFALO_ONNX),
                                    "sface": sha256_file(SFACE_ONNX)},
            "templat": "rata-rata embedding enrollment ternormalisasi L2, lalu L2 (amandemen 4)"}


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sp = ap.add_subparsers(dest="cmd", required=True)
    a = sp.add_parser("liveness"); a.add_argument("--scores", required=True); a.add_argument("--manifest", default=MANIFEST); a.add_argument("--out", required=True)
    b = sp.add_parser("embed"); b.add_argument("--max_side", type=int, default=0); b.add_argument("--threads", type=int); b.add_argument("--out", required=True)
    c = sp.add_parser("recognition"); c.add_argument("--emb", required=True); c.add_argument("--out", required=True)
    args = ap.parse_args()
    os.makedirs(os.path.dirname(args.out) or ".", exist_ok=True)
    if args.cmd == "embed":
        data, emb = embed_all(args.max_side, args.threads)
        meta = {**data, "models": list(emb), "max_side": args.max_side or "penuh",
                "dibuat": datetime.now().isoformat(timespec="seconds"), **jejak_embed(args.threads)}
        np.savez(args.out, meta=json.dumps(meta), **emb)
        print("ditulis:", args.out, "| status:", dict(Counter(data["status"])))
        return
    if args.cmd == "liveness":
        hasil = liveness_eval(liveness_table(read_csv(args.manifest), read_csv(args.scores)))
        hasil["sumber_skor"] = args.scores
    else:
        hasil = recognition_from_npz(args.emb)
    hasil["dibuat"] = datetime.now().isoformat(timespec="seconds")
    with open(args.out, "w", encoding="utf-8") as f:
        json.dump(_bersih(hasil), f, indent=2, ensure_ascii=False)
    print("ditulis:", args.out)


if __name__ == "__main__":
    sys.exit(main())
