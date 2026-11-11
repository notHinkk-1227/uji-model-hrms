"""Terapkan kriteria pemilihan model liveness (amandemen 7 bagian 6, DIBEKUKAN) secara mekanis pada skor v2.

Aturan (jangan diubah tanpa amandemen baru yang dibuat SEBELUM foto baru dievaluasi):
  Dasar : foto asli lama (80) + serangan baru (print 40, screen 40); skenario 1280; threshold EER per lipatan latih
          leave-one-subject-out; ACER = (APCER terburuk dari print dan screen + BPCER) / 2; gagal deteksi dihitung ditolak.
  1. Syarat ikut peringkat: ACER <= 25% DAN BPCER tiap relawan <= 50%.
  2. Pemenang: yang memenuhi syarat dengan ACER terendah.
  3. Bila selisih ACER dua teratas <= 5 poin persentase: berurutan (a) lisensi lulus audit, (b) APCER terburuk lebih rendah,
     (c) latensi median lebih rendah.
  4. Bila tidak ada yang memenuhi syarat: "belum ada model liveness terpilih" (syarat tidak diturunkan).
  5. Hanya dilaporkan: skenario lain, aturan bawaan, per pencahayaan, gagal deteksi.
  6. Pemenang kinerja dengan lisensi tertahan tetap pemenang kinerja; kelayakan produksi menunggu gerbang lisensi.

Memakai evaluasi.py (liveness_table dan pembentukan threshold yang sama). Hanya membaca skor dan manifest; tidak membuka gambar.

Jalankan dari akar proyek:
  python scripts/seleksi_liveness_v2.py --scores results/liveness/v2_skor_real_1280.csv results/liveness/v2_skor_serangan_1280.csv
"""
import argparse
import json
import os
import sys
from collections import Counter
from fractions import Fraction

import numpy as np

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import evaluasi as EV  # noqa: E402
import metrics as M  # noqa: E402

ACER_MAKS = Fraction(1, 4)          # 25%
BPCER_RELAWAN_MAKS = Fraction(1, 2)  # 50%
SELISIH_SERI = Fraction(5, 100)     # 5 poin persentase
# Lisensi lulus audit (laporan akhir bagian 6): hanya MiniFASNet. Latensi median ms (laporan akhir bagian 5, benchmark 2026-11-05;
# hanya urutan besar yang dapat dipakai). Dipakai HANYA bila aturan seri berlaku.
LISENSI_LULUS = {"minifasnet": True, "face_antispoof_onnx": False, "anti_spoof_mn3": False}
LATENSI_MS = {"minifasnet": 11.0, "face_antispoof_onnx": 5.0, "anti_spoof_mn3": 3.0}


def pred_eer_loso(tabel, nm):
    """Prediksi real/spoof per sampel dengan threshold EER dari relawan latih (sama dengan evaluasi.liveness_eval)."""
    kelas = np.array([r["class"] for r in tabel])
    real = kelas == "real"
    sc = np.array([r[f"{nm}_score"] for r in tabel])
    subj = np.array([r["subject"] for r in tabel])
    pred = np.zeros(len(tabel), dtype=int)
    for _, tr, te in M.loso_folds(subj):
        tr_ok = [i for i in tr if not tabel[i][f"{nm}_gagal"]]
        t = M.threshold_eer(sc[[i for i in tr_ok if real[i]]], sc[[i for i in tr_ok if not real[i]]])
        for i in te:
            pred[i] = int((not tabel[i][f"{nm}_gagal"]) and sc[i] >= t)
    return pred


def ringkas_model(tabel, nm):
    """Angka mentah (pecahan eksak) untuk kriteria. Tidak ada pembulatan sebelum keputusan."""
    pred = pred_eer_loso(tabel, nm)
    kelas = [r["class"] for r in tabel]
    subj = [r["subject"] for r in tabel]
    real_idx = [i for i, c in enumerate(kelas) if c == "real"]
    bp = (sum(1 for i in real_idx if pred[i] == 0), len(real_idx))
    ap = {}
    for jenis in sorted(set(kelas) - {"real"}):
        idx = [i for i, c in enumerate(kelas) if c == jenis]
        ap[jenis] = (sum(1 for i in idx if pred[i] == 1), len(idx))
    per_rel = {}
    for s in sorted(set(subj)):
        idx = [i for i in real_idx if subj[i] == s]
        per_rel[s] = (sum(1 for i in idx if pred[i] == 0), len(idx))
    ap_terburuk = max(Fraction(k, n) for k, n in ap.values())
    bpcer = Fraction(*bp)
    gagal = sum(1 for r in tabel if r[f"{nm}_gagal"])
    return {"bpcer": bp, "apcer": ap, "bpcer_per_relawan": per_rel, "apcer_terburuk": ap_terburuk,
            "acer": (ap_terburuk + bpcer) / 2, "gagal_deteksi_atau_proses": gagal}


def memenuhi_syarat(r):
    alasan = []
    if r["acer"] > ACER_MAKS:
        alasan.append(f"ACER {float(r['acer']) * 100:.1f}% > 25%")
    for s, (k, n) in r["bpcer_per_relawan"].items():
        if Fraction(k, n) > BPCER_RELAWAN_MAKS:
            alasan.append(f"BPCER {s} {k}/{n} > 50%")
    return (not alasan), alasan


def putuskan(ring, lisensi=None, latensi=None):
    """ring: {nama_model: hasil ringkas_model}. Kembalikan dict keputusan dengan jejak alasan."""
    lisensi, latensi = lisensi or LISENSI_LULUS, latensi or LATENSI_MS
    jejak, lolos, gagal = [], [], {}
    for nm, r in ring.items():
        ok, alasan = memenuhi_syarat(r)
        (lolos.append(nm) if ok else gagal.__setitem__(nm, alasan))
    for nm, a in gagal.items():
        jejak.append(f"{nm}: tidak ikut peringkat ({'; '.join(a)})")
    if not lolos:
        jejak.append("Tidak ada model yang memenuhi syarat: belum ada model liveness terpilih (syarat tidak diturunkan).")
        return {"pemenang": None, "status": "belum_ada_model_terpilih", "peringkat": [], "jejak": jejak}
    urut = sorted(lolos, key=lambda n: (ring[n]["acer"], n))
    jejak.append("Peringkat menurut ACER (EER-LOSO): " + ", ".join(f"{n} {float(ring[n]['acer']) * 100:.1f}%" for n in urut))
    if len(urut) == 1:
        jejak.append(f"{urut[0]} satu-satunya yang memenuhi syarat: pemenang.")
        return {"pemenang": urut[0], "status": "satu_satunya_memenuhi_syarat", "peringkat": urut, "jejak": jejak}
    a, b = urut[0], urut[1]
    selisih = ring[b]["acer"] - ring[a]["acer"]
    if selisih > SELISIH_SERI:
        jejak.append(f"Selisih ACER {a} dan {b} = {float(selisih) * 100:.1f} poin > 5: pemenang {a} (ACER terendah).")
        return {"pemenang": a, "status": "pemenang_menurut_acer", "peringkat": urut, "jejak": jejak}
    jejak.append(f"Selisih ACER {a} dan {b} = {float(selisih) * 100:.1f} poin <= 5: aturan seri berlaku.")
    if lisensi.get(a) != lisensi.get(b):
        w = a if lisensi.get(a) else b
        jejak.append(f"(a) lisensi lulus audit hanya pada {w}: pemenang {w}.")
        return {"pemenang": w, "status": "seri_diputuskan_lisensi", "peringkat": urut, "jejak": jejak}
    jejak.append("(a) lisensi tidak membedakan.")
    if ring[a]["apcer_terburuk"] != ring[b]["apcer_terburuk"]:
        w = a if ring[a]["apcer_terburuk"] < ring[b]["apcer_terburuk"] else b
        jejak.append(f"(b) APCER terburuk lebih rendah pada {w}: pemenang {w}.")
        return {"pemenang": w, "status": "seri_diputuskan_apcer", "peringkat": urut, "jejak": jejak}
    jejak.append("(b) APCER terburuk sama.")
    if latensi.get(a) != latensi.get(b):
        w = a if latensi[a] < latensi[b] else b
        jejak.append(f"(c) latensi median lebih rendah pada {w}: pemenang {w}.")
        return {"pemenang": w, "status": "seri_diputuskan_latensi", "peringkat": urut, "jejak": jejak}
    jejak.append("(c) latensi sama: aturan tidak dapat memutuskan; dilaporkan apa adanya.")
    return {"pemenang": None, "status": "seri_tidak_dapat_diputuskan", "peringkat": urut, "jejak": jejak}


def periksa_meta(path, izinkan_skenario_lain):
    meta_path = path + ".meta.json"
    if not os.path.exists(meta_path):
        return [f"{path}: tidak ada .meta.json (asal skor tidak dapat diperiksa)"], []
    meta = json.load(open(meta_path, encoding="utf-8"))
    galat, peringatan = [], []
    if meta.get("batas_resolusi_sisi_terpanjang_px") != 1280 and not izinkan_skenario_lain:
        galat.append(f"{path}: skenario {meta.get('batas_resolusi_sisi_terpanjang_px')}, kriteria bagian 6 memakai 1280")
    if meta.get("skrip_belum_di_commit"):
        peringatan.append(f"{path}: dihasilkan saat skrip belum di-commit")
    return galat, peringatan


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--scores", nargs="+", required=True)
    ap.add_argument("--manifest", default="datasets/liveness/internal/manifest_v2.csv")
    ap.add_argument("--out", default="results/liveness/v2_seleksi_1280.json")
    ap.add_argument("--izinkan_skenario_lain", action="store_true")
    a = ap.parse_args()
    galat, peringatan = [], []
    for p in a.scores:
        g, w = periksa_meta(p, a.izinkan_skenario_lain)
        galat += g; peringatan += w
    if galat:
        print("BERHENTI:"); [print("  -", g) for g in galat]
        return 1
    baris = [r for p in a.scores for r in EV.read_csv(p)]
    ids = [r["sample_id"] for r in baris]
    if len(set(ids)) != len(ids):
        print("BERHENTI: sample_id ganda di antara berkas skor"); return 1
    tabel = EV.liveness_table(EV.read_csv(a.manifest), baris)
    kom = Counter(r["class"] for r in tabel)
    if dict(kom) != {"real": 80, "print": 40, "screen": 40}:
        print(f"BERHENTI: komposisi {dict(kom)} bukan 80 real, 40 print, 40 screen"); return 1
    ring = {nm: ringkas_model(tabel, nm) for nm in EV.LIVENESS_MODELS}
    kep = putuskan(ring)
    for w in peringatan:
        print("PERINGATAN:", w)
    print("Kriteria bagian 6 (skenario 1280, EER-LOSO), hanya angka agregat:")
    for nm, r in ring.items():
        ok, alasan = memenuhi_syarat(r)
        pr = ", ".join(f"{s} {k}/{n}" for s, (k, n) in r["bpcer_per_relawan"].items())
        print(f"  {nm}: ACER {float(r['acer']) * 100:.1f}% | APCER print {r['apcer']['print'][0]}/{r['apcer']['print'][1]}, "
              f"screen {r['apcer']['screen'][0]}/{r['apcer']['screen'][1]} | BPCER {r['bpcer'][0]}/{r['bpcer'][1]} (per relawan: {pr}) | "
              f"gagal deteksi/proses {r['gagal_deteksi_atau_proses']} | syarat: {'LOLOS' if ok else 'TIDAK'}")
    print("\nKeputusan:")
    for j in kep["jejak"]:
        print("  -", j)
    print(f"\nPEMENANG KINERJA: {kep['pemenang'] or 'belum ada model terpilih'}  [{kep['status']}]")
    if kep["pemenang"] and not LISENSI_LULUS.get(kep["pemenang"]):
        print("CATATAN: lisensi model ini tertahan; kelayakan produksi menunggu gerbang lisensi (aturan 6).")
    ser = {nm: {"acer": float(r["acer"]), "apcer": {k: list(v) for k, v in r["apcer"].items()}, "bpcer": list(r["bpcer"]),
                "bpcer_per_relawan": {s: list(v) for s, v in r["bpcer_per_relawan"].items()},
                "gagal_deteksi_atau_proses": r["gagal_deteksi_atau_proses"], "memenuhi_syarat": memenuhi_syarat(r)[0]}
           for nm, r in ring.items()}
    os.makedirs(os.path.dirname(a.out) or ".", exist_ok=True)
    json.dump({"skenario": "1280", "sumber_skor": a.scores, "model": ser, "keputusan": kep}, open(a.out, "w", encoding="utf-8"), indent=1, ensure_ascii=False)
    print("Tersimpan:", a.out)
    return 0


if __name__ == "__main__":
    sys.exit(main())
