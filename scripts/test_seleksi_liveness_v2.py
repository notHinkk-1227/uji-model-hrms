"""Uji seleksi_liveness_v2.py pada skor TIRUAN (angka acak, bukan hasil model, bukan foto relawan).
Jalankan dari akar proyek: python scripts/test_seleksi_liveness_v2.py"""
import math
import os
import sys
from fractions import Fraction

import numpy as np

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import evaluasi as EV  # noqa: E402
import seleksi_liveness_v2 as S  # noqa: E402

HASIL = []


def cek(nama, kondisi, info=""):
    HASIL.append(bool(kondisi))
    print(("OK    " if kondisi else "GAGAL ") + nama + (f"  [{info}]" if info and not kondisi else ""))


def tabel_tiruan(rng, nama_skor):
    """4 relawan: 20 real, 10 print, 10 screen. nama_skor: fungsi (kelas, subjek, rng) -> skor. Hanya satu model dipakai tiap kali."""
    t = []
    for s in ("S01", "S02", "S03", "S04"):
        for kelas, n in (("real", 20), ("print", 10), ("screen", 10)):
            for i in range(n):
                row = {"sample_id": f"{s}_{kelas}_{i}", "subject": s, "class": kelas, "lighting": "x", "status": "ok"}
                for nm in EV.LIVENESS_MODELS:
                    sc = nama_skor(nm, kelas, s, rng)
                    row[f"{nm}_gagal"] = sc is None
                    row[f"{nm}_score"] = -math.inf if sc is None else sc
                    row[f"{nm}_pred"] = 0 if sc is None else int(sc >= 0.5)
                t.append(row)
    return t


def skor(nm, kelas, s, rng):
    nyata = kelas == "real"
    if nm == "minifasnet":      # terpisah sempurna
        return 0.9 + rng.random() * 0.05 if nyata else 0.1 + rng.random() * 0.05
    if nm == "face_antispoof_onnx":  # tumpang tindih sedang
        return 0.7 + rng.random() * 0.3 if nyata else rng.random() * 0.85
    # anti_spoof_mn3: gagal total pada S02 (semua real S02 skor rendah)
    if nyata:
        return 0.05 if s == "S02" else 0.9 + rng.random() * 0.05
    return 0.1 + rng.random() * 0.05


rng = np.random.default_rng(1)
t = tabel_tiruan(rng, skor)

# 1. Ringkas model sama dengan evaluasi.liveness_eval (ACER EER-LOSO dan BPCER total)
ev = EV.liveness_eval(t)
for nm in EV.LIVENESS_MODELS:
    r = S.ringkas_model(t, nm)
    ref = ev["model"][nm]["tambahan_eer_loso"]["metrik_gabungan"]
    cek(f"{nm}: ACER sama dengan evaluasi.liveness_eval (EER-LOSO)", math.isclose(float(r["acer"]), ref["acer"], abs_tol=1e-12), (float(r["acer"]), ref["acer"]))
    cek(f"{nm}: BPCER per relawan menjumlah ke BPCER gabungan", sum(k for k, _ in r["bpcer_per_relawan"].values()) == r["bpcer"][0] == ref["bpcer"]["k"])

# 2. Syarat per relawan: mn3 menolak semua real S02 -> tidak lolos syarat
rm = S.ringkas_model(t, "anti_spoof_mn3")
ok, alasan = S.memenuhi_syarat(rm)
cek("mn3 gagal total pada satu relawan: tidak memenuhi syarat", (not ok) and any("S02" in a for a in alasan), alasan)

# 3. Keputusan pada data tiruan: minifasnet menang jelas (ACER ~0), mn3 tersingkir
ring = {nm: S.ringkas_model(t, nm) for nm in EV.LIVENESS_MODELS}
k = S.putuskan(ring)
cek("pemenang jelas: minifasnet; mn3 tidak ikut peringkat", k["pemenang"] == "minifasnet" and "anti_spoof_mn3" not in k["peringkat"], k)


def R(acer_k_ap, n_ap, bp_k, bp_n=80, per=None):
    """Buat ringkasan buatan untuk menguji aturan keputusan secara langsung."""
    ap_p, ap_s = acer_k_ap
    ap_terburuk = max(Fraction(ap_p, n_ap), Fraction(ap_s, n_ap))
    return {"bpcer": (bp_k, bp_n), "apcer": {"print": (ap_p, n_ap), "screen": (ap_s, n_ap)},
            "bpcer_per_relawan": per or {s: (bp_k // 4, 20) for s in ("S01", "S02", "S03", "S04")},
            "apcer_terburuk": ap_terburuk, "acer": (ap_terburuk + Fraction(bp_k, bp_n)) / 2, "gagal_deteksi_atau_proses": 0}


# 4. Batas persis
cek("ACER tepat 25% memenuhi syarat (<=)", S.memenuhi_syarat(R((20, 8), 40, 0))[0] is True and R((20, 8), 40, 0)["acer"] == Fraction(1, 4))
cek("ACER sedikit di atas 25% tidak memenuhi syarat", S.memenuhi_syarat(R((21, 0), 40, 0))[0] is False)
per_ok = {"S01": (10, 20), "S02": (0, 20), "S03": (0, 20), "S04": (0, 20)}
per_buruk = {"S01": (11, 20), "S02": (0, 20), "S03": (0, 20), "S04": (0, 20)}
cek("BPCER relawan tepat 50% (10/20) memenuhi syarat; 11/20 tidak", S.memenuhi_syarat(R((0, 0), 40, 10, per=per_ok))[0] and not S.memenuhi_syarat(R((0, 0), 40, 11, per=per_buruk))[0])

# 5. Tidak ada yang memenuhi syarat
semua_buruk = {"a": R((30, 30), 40, 0), "b": R((35, 20), 40, 0)}
k = S.putuskan(semua_buruk, lisensi={"a": False, "b": False}, latensi={"a": 1, "b": 2})
cek("tidak ada yang memenuhi syarat: belum ada model terpilih (syarat tidak diturunkan)", k["pemenang"] is None and k["status"] == "belum_ada_model_terpilih", k)

# 6. Selisih > 5 poin: ACER terendah menang walau lisensinya tertahan
r1, r2 = R((4, 4), 40, 0), R((8, 8), 40, 0)  # ACER 5% vs 10%
k = S.putuskan({"a": r1, "b": r2}, lisensi={"a": False, "b": True}, latensi={"a": 9, "b": 1})
cek("selisih 5 poin penuh (5% vs 10%): aturan seri berlaku (selisih <= 5 inklusif), lisensi memutuskan", k["status"] == "seri_diputuskan_lisensi" and k["pemenang"] == "b", k)
r2b = R((9, 9), 40, 0)  # ACER 11.25% vs 5% = 6.25 poin
k = S.putuskan({"a": r1, "b": r2b}, lisensi={"a": False, "b": True}, latensi={"a": 9, "b": 1})
cek("selisih 6,25 poin: ACER terendah menang walau lisensi tertahan", k["status"] == "pemenang_menurut_acer" and k["pemenang"] == "a", k)

# 7. Seri: urutan lisensi -> APCER terburuk -> latensi
x, y = R((4, 4), 40, 0), R((6, 2), 40, 0)  # ACER 5% vs 7.5%
cek("seri: lisensi sama, APCER terburuk lebih rendah menang", S.putuskan({"x": x, "y": y}, lisensi={"x": True, "y": True}, latensi={"x": 9, "y": 1})["pemenang"] == "x")
x2, y2 = R((4, 4), 40, 0), R((4, 4), 40, 1)  # ACER 5% vs 6.25%; APCER terburuk sama 10%
k = S.putuskan({"x": x2, "y": y2}, lisensi={"x": False, "y": False}, latensi={"x": 9, "y": 1})
cek("seri: lisensi dan APCER sama, latensi lebih rendah menang", k["pemenang"] == "y" and k["status"] == "seri_diputuskan_latensi", k)
k = S.putuskan({"x": x2, "y": y2}, lisensi={"x": False, "y": False}, latensi={"x": 5, "y": 5})
cek("seri total: tidak diputuskan diam-diam", k["pemenang"] is None and k["status"] == "seri_tidak_dapat_diputuskan", k)

# 8. Satu-satunya yang memenuhi syarat
k = S.putuskan({"a": R((4, 4), 40, 0), "b": R((30, 30), 40, 0)})
cek("hanya satu memenuhi syarat: dia pemenang", k["pemenang"] == "a" and k["status"] == "satu_satunya_memenuhi_syarat", k)

n = sum(HASIL)
print(f"\n{n}/{len(HASIL)} lolos")
sys.exit(0 if n == len(HASIL) else 1)
