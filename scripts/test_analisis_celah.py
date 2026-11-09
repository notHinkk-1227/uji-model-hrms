"""Uji analisis_celah.py pada data TIRUAN (tanpa model, tanpa data relawan).
Jalankan dari akar proyek: python scripts/test_analisis_celah.py"""
import csv
import json
import math
import os
import sys
import tempfile

import numpy as np

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import analisis_celah as AC  # noqa: E402
import evaluasi as EV  # noqa: E402

HASIL = []


def cek(nama, kondisi, info=""):
    HASIL.append(bool(kondisi))
    print(("OK    " if kondisi else "GAGAL ") + nama + (f"  [{info}]" if info and not kondisi else ""))


def buat_pairs(skor_genuine, skor_impostor, subjek=("S01", "S02", "S03", "S04")):
    """Pasangan tiruan: tiap subjek 3 probe; genuine memakai skor_genuine, impostor skor_impostor (siklus)."""
    pairs, gi, ii = [], 0, 0
    for s in subjek:
        for k in range(3):
            for c in subjek:
                gen = s == c
                if gen:
                    sc = skor_genuine[gi % len(skor_genuine)]; gi += 1
                else:
                    sc = skor_impostor[ii % len(skor_impostor)]; ii += 1
                pairs.append({"probe": f"{s}-{k}", "probe_subject": s, "claim": c, "lighting": "terang",
                              "genuine": gen, "gagal": False, "score": float(sc)})
    return pairs


# 1. Terpisah sempurna: genuine 0.80-0.90, impostor 0.10-0.30 -> celah gabungan = 0.80 - 0.30 = 0.50 (hitung tangan)
gen = [0.80, 0.85, 0.90]
imp = [0.10, 0.20, 0.30]
r = AC.ringkas_celah(buat_pairs(gen, imp))
g = r["gabungan"]
cek("celah gabungan = min genuine - maks impostor (0,80-0,30)", math.isclose(g["celah_gabungan"], 0.50, abs_tol=1e-9), g)
cek("jumlah pasangan 12 genuine dan 36 impostor", g["n_genuine"] == 12 and g["n_impostor"] == 36, g)
cek("terpisah sempurna: tidak ada tumpang tindih", g["impostor_di_atas_genuine_min"] == 0 and g["genuine_di_bawah_impostor_maks"] == 0, g)
posisi = [l["posisi_threshold_di_celah_latih"] for l in r["lipatan"].values()]
cek("data terpisah sempurna: threshold EER tepat di tengah celah latih (posisi 0,50)",
    all(p is not None and math.isclose(p, 0.5, abs_tol=1e-9) for p in posisi), posisi)
cek("threshold tiap lipatan = (maks impostor + min genuine)/2 pada data latih",
    all(math.isclose(l["threshold"], (l["latih_impostor_maks"] + l["latih_genuine_min"]) / 2, abs_tol=1e-9)
        for l in r["lipatan"].values()))
cek("tanpa kesalahan pada lipatan uji", all(l["uji_impostor_di_atas_threshold"] == 0 and l["uji_genuine_di_bawah_threshold"] == 0
                                            for l in r["lipatan"].values()))

# 2. Ada tumpang tindih: satu impostor 0.82 (di atas genuine min 0.80)
pairs = buat_pairs(gen, imp)
tgt = next(p for p in pairs if not p["genuine"] and p["probe_subject"] == "S02")
tgt["score"] = 0.82
r2 = AC.ringkas_celah(pairs)
g2 = r2["gabungan"]
cek("tumpang tindih: celah gabungan negatif (0,80-0,82)", math.isclose(g2["celah_gabungan"], -0.02, abs_tol=1e-9), g2)
cek("tumpang tindih: 1 impostor di atas genuine min; genuine <= impostor maks dihitung benar",
    g2["impostor_di_atas_genuine_min"] == 1 and g2["genuine_di_bawah_impostor_maks"] == sum(1 for p in pairs if p["genuine"] and p["score"] <= 0.82), g2)
cek("tumpang tindih pada data latih: posisi threshold None bila celah latih <= 0",
    any(l["posisi_threshold_di_celah_latih"] is None for l in r2["lipatan"].values() if l["celah_latih"] <= 0))

# 3. Pasangan gagal tidak ikut menentukan min/maks
pairs = buat_pairs(gen, imp)
pairs[0]["gagal"] = True
pairs[0]["score"] = -math.inf
cek("pasangan gagal (-inf) tidak merusak min/maks", AC.ringkas_celah(pairs)["gabungan"]["skor_genuine_min"] >= 0.80)

# 4. Pemuat npz sama dengan evaluasi.recognition_from_npz (data acak, bukan wajah)
rng = np.random.default_rng(0)
subjek = ["S01", "S02", "S03", "S04"]
pusat = {s: rng.normal(size=16) for s in subjek}
jenis, ids, subj, E = [], [], [], []
man_rows = []
for s in subjek:
    for k in range(4):
        sid = f"{s}-p{k}"
        v = pusat[s] + rng.normal(scale=0.6, size=16)
        jenis.append("probe"); ids.append(sid); subj.append(s); E.append(v / np.linalg.norm(v))
        man_rows.append({"sample_id": sid, "class": "real", "filename": sid + ".jpg", "lighting": "terang" if k % 2 else "redup"})
    for k in range(3):
        v = pusat[s] + rng.normal(scale=0.6, size=16)
        jenis.append("enroll"); ids.append(f"{s}-e{k}"); subj.append(s); E.append(v / np.linalg.norm(v))
with tempfile.TemporaryDirectory() as tmp:
    mpath = os.path.join(tmp, "manifest.csv")
    with open(mpath, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=["sample_id", "class", "filename", "lighting"])
        w.writeheader(); w.writerows(man_rows)
    npz = os.path.join(tmp, "emb_x.npz")
    meta = {"models": ["modelx"], "jenis": jenis, "id": ids, "subject": subj, "status": ["ok"] * len(ids), "n_faces": [1] * len(ids)}
    np.savez(npz, meta=np.array(json.dumps(meta)), modelx=np.array(E))
    EV.MANIFEST = mpath
    ref = EV.recognition_from_npz(npz)["model"]["modelx"]
    pairs = AC.pairs_dari_npz(npz, mpath)["modelx"]
    mine = EV.recognition_eval(pairs)
    cek("pemuat npz: FAR/FRR sama dengan evaluasi.recognition_from_npz",
        mine["gabungan_loso"]["far"]["k"] == ref["gabungan_loso"]["far"]["k"] and mine["gabungan_loso"]["frr"]["k"] == ref["gabungan_loso"]["frr"]["k"])
    cek("pemuat npz: AUC dan jumlah pasangan sama", math.isclose(mine["auc_gabungan"], ref["auc_gabungan"]) and mine["jumlah_pasangan"] == ref["jumlah_pasangan"])
    cek("pemuat npz: threshold tiap lipatan sama",
        all(math.isclose(mine["lipatan"][s]["threshold"], ref["lipatan"][s]["threshold"]) for s in subjek))
    r4 = AC.ringkas_celah(pairs)
    cek("jumlah FA di ringkasan = FAR k evaluasi utama",
        sum(l["uji_impostor_di_atas_threshold"] for l in r4["lipatan"].values()) == ref["gabungan_loso"]["far"]["k"])
    cek("jumlah FR di ringkasan = FRR k evaluasi utama",
        sum(l["uji_genuine_di_bawah_threshold"] for l in r4["lipatan"].values()) == ref["gabungan_loso"]["frr"]["k"])

    # 5. Privasi: keluaran hanya skalar (tidak ada vektor embedding)
    def hanya_skalar(o):
        if isinstance(o, dict):
            return all(hanya_skalar(v) for v in o.values())
        return o is None or isinstance(o, (int, float, bool))
    cek("keluaran ringkasan hanya berisi angka agregat (tidak ada vektor)", hanya_skalar(r4))

n = sum(HASIL)
print(f"\n{n}/{len(HASIL)} lolos")
sys.exit(0 if n == len(HASIL) else 1)
