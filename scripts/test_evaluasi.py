"""Uji evaluasi.py dengan data PALSU berjawaban diketahui (tanpa data relawan, tanpa model).

Jalankan dari akar proyek:  python scripts/test_evaluasi.py
"""
import math

import numpy as np

import evaluasi as E

hasil = []


def cek(nama, nilai, harapan, tol=1e-9):
    if isinstance(harapan, float):
        ok = nilai is not None and abs(nilai - harapan) <= tol
    else:
        ok = nilai == harapan
    print(f"[{'OK' if ok else 'SALAH'}] {nama}: {nilai} | harapan {harapan}")
    hasil.append(ok)


# ---------------- LIVENESS ----------------
# 4 relawan x (real 4, print 2, screen 2) = 32 sampel. Skor "normal": real 0,9 / serangan 0,1, keputusan benar.
manifest, skor = [], []
for s in ["S01", "S02", "S03", "S04"]:
    for kelas, n in [("real", 4), ("print", 2), ("screen", 2)]:
        for i in range(1, n + 1):
            sid = f"{s}_{kelas}_{i}"
            manifest.append({"sample_id": sid, "subject": s, "class": kelas, "lighting": "terang" if i % 2 else "redup"})
            v, p = (0.9, 1) if kelas == "real" else (0.1, 0)
            skor.append({"sample_id": sid, "status": "ok",
                         "minifas_avg_p1": v, "minifas_pred_real": p,
                         "facenox_diff": v, "facenox_pred_real": p,
                         "mn3_p_real": v, "mn3_pred_real": p})
by = {r["sample_id"]: r for r in skor}
# MiniFASNet: S01 real_1 ditolak (0,3); S02 print_1 diterima (0,8)
by["S01_real_1"].update(minifas_avg_p1=0.3, minifas_pred_real=0)
by["S02_print_1"].update(minifas_avg_p1=0.8, minifas_pred_real=1)
# S03 real_1: tidak ada wajah -> semua model gagal (kolom kosong)
by["S03_real_1"].update(status="no_face", **{k: "" for k in ["minifas_avg_p1", "minifas_pred_real", "facenox_diff",
                                                                 "facenox_pred_real", "mn3_p_real", "mn3_pred_real"]})
# face-antispoof-onnx: S04 print_1 gagal proses khusus model ini
by["S04_print_1"].update(status="error:facenox:RuntimeError", facenox_diff="", facenox_pred_real="")
# anti-spoof-mn3: semua serangan S02 diterima
for sid in ["S02_print_1", "S02_print_2", "S02_screen_1", "S02_screen_2"]:
    by[sid].update(mn3_p_real=0.7, mn3_pred_real=1)

L = E.liveness_eval(E.liveness_table(manifest, skor))
mf, fx, mn = (L["model"][k]["utama_aturan_bawaan"] for k in ["minifasnet", "face_antispoof_onnx", "anti_spoof_mn3"])
# MiniFASNet: real ditolak = S01_real_1 + S03_real_1 (no_face) = 2/16; print diterima 1/8; screen 0/8
cek("MiniFAS BPCER 2/16", (mf["bpcer"]["k"], mf["bpcer"]["n"]), (2, 16))
cek("MiniFAS APCER print 1/8", (mf["apcer"]["print"]["k"], mf["apcer"]["print"]["n"]), (1, 8))
cek("MiniFAS APCER screen 0/8", mf["apcer"]["screen"]["k"], 0)
cek("MiniFAS ACER (1/8 + 2/16)/2", mf["acer"], 0.125)
# facenox: hanya no_face real yang salah; print gagal proses = ditolak (benar)
cek("facenox BPCER 1/16", fx["bpcer"]["k"], 1)
cek("facenox APCER print 0/8 (gagal = ditolak)", fx["apcer"]["print"]["k"], 0)
cek("facenox jumlah gagal 2 (no_face + error)", L["model"]["face_antispoof_onnx"]["gagal"]["jumlah"], 2)
cek("MiniFAS jumlah gagal 1", L["model"]["minifasnet"]["gagal"]["jumlah"], 1)
# mn3: APCER print 2/8, screen 2/8
cek("mn3 APCER print 2/8", mn["apcer"]["print"]["k"], 2)
cek("mn3 APCER screen 2/8", mn["apcer"]["screen"]["k"], 2)
cek("mn3 per relawan S02 APCER print 2/2", L["model"]["anti_spoof_mn3"]["per_relawan"]["S02"]["apcer"]["print"]["nilai"], 1.0)
# McNemar MiniFAS vs facenox: MiniFAS salah pada S01_real_1, S02_print_1 (facenox benar) -> b=0, c=2, p = 2*0,25
mc = L["berpasangan_mcnemar_aturan_bawaan"]["minifasnet_vs_face_antispoof_onnx"]
cek("McNemar MiniFAS vs facenox (b, c)", (mc["a_benar_b_salah"], mc["a_salah_b_benar"]), (0, 2))
cek("McNemar p = 0,5", mc["p_value"], 0.5)
# EER LOSO MiniFAS lipatan S03 (latih S01,S02,S04): real {0,3, 0,9 x11}, serangan {0,8, 0,1 x11} -> threshold 0,55
cek("MiniFAS EER lipatan S03 = 0,55", L["model"]["minifasnet"]["tambahan_eer_loso"]["lipatan"]["S03"]["threshold"], 0.55, 1e-12)
# facenox EER: terpisah sempurna -> threshold 0,5 di semua lipatan; metrik gabungan = hanya no_face salah
fxe = L["model"]["face_antispoof_onnx"]["tambahan_eer_loso"]
cek("facenox EER semua lipatan 0,5", sorted({round(v["threshold"], 12) for v in fxe["lipatan"].values()}), [0.5])
cek("facenox EER gabungan BPCER 1/16", fxe["metrik_gabungan"]["bpcer"]["k"], 1)
# AUC facenox: real 15 x 0,9 + 1 x -inf; serangan 15 x 0,1 + 1 x -inf -> (15*16 + 0,5*1)/(16*16)
cek("facenox AUC dengan gagal = -inf", L["model"]["face_antispoof_onnx"]["auc_gabungan"], (15 * 16 + 0.5) / 256)
# Kebocoran: ubah ekstrem skor relawan S01 -> threshold lipatan S01 tidak boleh berubah
skor2 = [dict(r) for r in skor]
for r in skor2:
    if r["sample_id"].startswith("S01") and r["status"] == "ok":
        r["minifas_avg_p1"] = 0.0 if "real" in r["sample_id"] else 1.0
L2 = E.liveness_eval(E.liveness_table(manifest, skor2))
cek("threshold lipatan S01 tidak dipengaruhi skor S01",
    L2["model"]["minifasnet"]["tambahan_eer_loso"]["lipatan"]["S01"]["threshold"],
    L["model"]["minifasnet"]["tambahan_eer_loso"]["lipatan"]["S01"]["threshold"])
try:
    E.liveness_table(manifest, skor[:-1])
    cek("sampel tanpa skor ditolak", False, True)
except ValueError:
    cek("sampel tanpa skor ditolak", True, True)

# ---------------- PENGENALAN ----------------
I = np.eye(8)
subj = ["S01", "S02", "S03", "S04"]
basis = {s: I[k] for k, s in enumerate(subj)}
enroll = {s: [basis[s], basis[s]] for s in subj}           # templat = basis relawan
probes, emb = [], {}
for s in subj:
    for i in range(1, 4):
        sid = f"{s}_p{i}"
        probes.append({"sample_id": sid, "subject": s, "lighting": "terang" if i % 2 else "redup"})
        emb[sid] = basis[s]
emb["S02_p1"] = 0.6 * basis["S02"] + 0.8 * basis["S03"]   # genuine 0,6; impostor vs S03 0,8
emb["S04_p3"] = None                                        # probe gagal deteksi
pairs, templat = E.recognition_pairs(probes, emb, enroll)
R = E.recognition_eval(pairs)
cek("jumlah pasangan genuine/impostor", (R["jumlah_pasangan"]["genuine"], R["jumlah_pasangan"]["impostor"]), (12, 36))
cek("probe gagal 1", R["probe_gagal"], 1)
# Threshold (hitung tangan): S01 0,3 (seri |FAR-FRR| dipecah FAR+FRR); S02 0,5 (latih terpisah sempurna); S03 0,3; S04 0,3
th = {s: round(R["lipatan"][s]["threshold"], 12) for s in subj}
cek("threshold per lipatan", th, {"S01": 0.3, "S02": 0.5, "S03": 0.3, "S04": 0.3})
# lipatan S01: latih S02, S03, S04 tanpa S04_p3 (gagal) -> genuine 3+3+2 = 8, impostor 8 probe x 2 identitas = 16
cek("pasangan latih lipatan S01 (gagal dikeluarkan)",
    (R["lipatan"]["S01"]["pasangan_latih_genuine"], R["lipatan"]["S01"]["pasangan_latih_impostor"]), (8, 16))
cek("pasangan latih lipatan S03 (gagal dikeluarkan)",
    (R["lipatan"]["S03"]["pasangan_latih_genuine"], R["lipatan"]["S03"]["pasangan_latih_impostor"]), (8, 16))
# Gabungan: FA = S02_p1 vs S03 (0,8 >= 0,5) -> 1/36; FR = S04_p3 gagal -> 1/12
cek("FAR gabungan 1/36", (R["gabungan_loso"]["far"]["k"], R["gabungan_loso"]["far"]["n"]), (1, 36))
cek("FRR gabungan 1/12", (R["gabungan_loso"]["frr"]["k"], R["gabungan_loso"]["frr"]["n"]), (1, 12))
cek("templat rata-rata [e0, e1] = (e0+e1)/sqrt2", float(np.dot(E._template([I[0], I[1]]), I[0])), 1 / math.sqrt(2))
# Kebocoran: ubah embedding probe S01 -> threshold lipatan S01 tetap
emb2 = dict(emb)
for i in range(1, 4):
    emb2[f"S01_p{i}"] = basis["S02"]
R2 = E.recognition_eval(E.recognition_pairs(probes, emb2, enroll)[0])
cek("threshold lipatan S01 tidak dipengaruhi probe S01", R2["lipatan"]["S01"]["threshold"], R["lipatan"]["S01"]["threshold"])
try:
    E.recognition_pairs(probes, emb, {**enroll, "S04": []})
    cek("enrollment gagal semua -> berhenti", False, True)
except ValueError:
    cek("enrollment gagal semua -> berhenti", True, True)
# probe_list: hanya real, tanpa duplikat (cocok nama berkas)
man = [{"class": "real", "filename": "a.jpg"}, {"class": "real", "filename": "b.jpg"}, {"class": "print", "filename": "c.jpg"}]
cek("probe_list mengecualikan duplikat dan serangan",
    [m["filename"] for m in E.probe_list(man, [{"berkas_raw_identik": "x\\y/a.jpg"}])], ["b.jpg"])

print(f"\n{sum(hasil)}/{len(hasil)} lolos")
print("SEMUA OK" if all(hasil) else "ADA YANG SALAH: jangan lanjut, kirim output ini.")
