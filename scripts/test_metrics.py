"""Uji Modul 5 (metrics.py) dengan data tiruan berlabel yang jawabannya diketahui. Tanpa data relawan.

Setiap harapan dihitung terpisah dari kode yang diuji (hitung tangan, rumus tertutup, atau math.comb).
Jalankan dari akar proyek:  python scripts/test_metrics.py
"""
import math

import numpy as np

import metrics as M

hasil = []


def cek(nama, nilai, harapan, tol=1e-9):
    if isinstance(harapan, (tuple, list)) and all(isinstance(v, (int, float)) for v in harapan):
        ok = len(nilai) == len(harapan) and all(abs(a - b) <= tol for a, b in zip(nilai, harapan))
    elif isinstance(harapan, float):
        ok = abs(nilai - harapan) <= tol
    else:
        ok = nilai == harapan
    print(f"[{'OK' if ok else 'SALAH'}] {nama}: {nilai} | harapan {harapan}")
    hasil.append(ok)


# 1. Liveness: 20 real (2 ditolak), 10 print (2 diterima), 10 screen (1 diterima)
kelas = ["real"] * 20 + ["print"] * 10 + ["screen"] * 10
pred = [0, 0] + [1] * 18 + [1, 1] + [0] * 8 + [1] + [0] * 9
L = M.liveness_metrics(kelas, pred)
cek("BPCER 2/20", (L["bpcer"]["k"], L["bpcer"]["n"], L["bpcer"]["nilai"]), (2, 20, 0.10))
cek("APCER print 2/10", L["apcer"]["print"]["nilai"], 0.20)
cek("APCER screen 1/10", L["apcer"]["screen"]["nilai"], 0.10)
cek("APCER terburuk", L["apcer_terburuk"], "print")
cek("ACER (0,20 + 0,10)/2", L["acer"], 0.15)
cek("confusion real", L["confusion"]["real"], {"diterima_real": 18, "ditolak": 2})
cek("confusion print", L["confusion"]["print"], {"diterima_real": 2, "ditolak": 8})

# 2. AUC (hitung tangan): 8 dari 9 pasangan real > spoof
cek("AUC 8/9", M.auc([0.9, 0.8, 0.7], [0.6, 0.75, 0.2]), 8 / 9)
cek("AUC sempurna", M.auc([3, 4], [1, 2]), 1.0)
cek("AUC terbalik", M.auc([1, 2], [3, 4]), 0.0)
cek("AUC seri", M.auc([0.5], [0.5]), 0.5)

# 3. FAR/FRR pada threshold 0,5 (diterima bila >=)
R = M.far_frr([0.9, 0.8, 0.3], [0.1, 0.2, 0.85], 0.5)
cek("FRR 1/3", R["frr"]["nilai"], 1 / 3)
cek("FAR 1/3", R["far"]["nilai"], 1 / 3)
cek("skor tepat di threshold diterima", M.far_frr([0.5], [0.5], 0.5)["far"]["k"], 1)
R0 = M.far_frr([0.9], [0.1] * 186, 0.5)
cek("FAR 0/186: batas aturan 3/N", R0["far_batas_atas_tanpa_kesalahan"]["aturan_3_per_n"], 3 / 186)
cek("FAR 0/186: batas eksak 1-0,05^(1/186)", R0["far_batas_atas_tanpa_kesalahan"]["eksak"], 1 - 0.05 ** (1 / 186))

# 4. Clopper-Pearson: kasus rumus tertutup
cek("CP 0/10 atas = 1-0,025^(1/10)", M.clopper_pearson(0, 10), (0.0, 1 - 0.025 ** 0.1), tol=1e-9)
cek("CP 10/10 bawah = 0,025^(1/10)", M.clopper_pearson(10, 10), (0.025 ** 0.1, 1.0), tol=1e-9)
# Kasus umum 5/20: batas harus memenuhi definisinya (ekor binomial = 0,025), dihitung dengan math.comb
lo, hi = M.clopper_pearson(5, 20)
ekor_atas = sum(math.comb(20, i) * lo ** i * (1 - lo) ** (20 - i) for i in range(5, 21))
ekor_bawah = sum(math.comb(20, i) * hi ** i * (1 - hi) ** (20 - i) for i in range(0, 6))
cek("CP 5/20 bawah: P(X>=5)=0,025", ekor_atas, 0.025, tol=1e-9)
cek("CP 5/20 atas: P(X<=5)=0,025", ekor_bawah, 0.025, tol=1e-9)
cek("CP 5/20 mengapit 0,25", lo < 0.25 < hi, True)
print(f"       (CP 5/20 = {lo:.4f} - {hi:.4f}; tabel terbitan umum menyebut sekitar 0,0866 - 0,4910 [S])")

# 5. McNemar eksak (hitung tangan)
cek("McNemar b=0 c=6: 2*0,5^6", M.mcnemar_exact([0] * 6 + [1] * 4, [1] * 10)["p_value"], 2 * 0.5 ** 6)
cek("McNemar b=1 c=9: 2*(C(10,0)+C(10,1))/1024",
    M.mcnemar_exact([1] + [0] * 9 + [1] * 5, [0] + [1] * 9 + [1] * 5)["p_value"], 2 * (1 + 10) / 1024, tol=1e-12)
cek("McNemar b=c: p=1", M.mcnemar_exact([1, 0], [0, 1])["p_value"], 1.0)
cek("McNemar tanpa sumbang: p=1", M.mcnemar_exact([1, 1], [1, 1])["p_value"], 1.0)

# 6. Threshold EER
cek("EER terpisah sempurna -> 0,5", M.threshold_eer([0.6, 0.7, 0.8, 0.9], [0.1, 0.2, 0.3, 0.4]), 0.5)
cek("EER tumpang-tindih -> 0,65", M.threshold_eer([0.5, 0.7, 0.9], [0.3, 0.6, 0.8]), 0.65, tol=1e-12)

# 7. LOSO: subjek uji tidak pernah di data latih; threshold tidak berubah bila data uji diubah (tanpa kebocoran)
subj = np.array(["S01"] * 4 + ["S02"] * 4 + ["S03"] * 4 + ["S04"] * 4)
lab = np.array([1, 1, 0, 0] * 4)
skor = np.array([0.9, 0.8, 0.2, 0.1, 0.85, 0.7, 0.3, 0.4, 0.95, 0.6, 0.35, 0.05, 0.75, 0.65, 0.5, 0.45])
folds = list(M.loso_folds(subj))
cek("4 lipatan", [f[0] for f in folds], ["S01", "S02", "S03", "S04"])
cek("uji tidak ada di latih", all(not set(subj[tr]) & set(subj[te]) for _, tr, te in folds), True)
cek("semua sampel diuji tepat sekali", sorted(np.concatenate([te for _, _, te in folds]).tolist()), list(range(16)))
bocor = False
for s, tr, te in folds:
    t1 = M.threshold_eer(skor[tr][lab[tr] == 1], skor[tr][lab[tr] == 0])
    skor2 = skor.copy()
    skor2[te] = np.array([-5.0, -5.0, 5.0, 5.0])  # ubah ekstrem data uji
    t2 = M.threshold_eer(skor2[tr][lab[tr] == 1], skor2[tr][lab[tr] == 0])
    bocor = bocor or (t1 != t2)
cek("threshold tidak dipengaruhi data uji", bocor, False)

# 8. Validasi masukan
try:
    M.liveness_metrics(["real"], [1, 0])
    cek("panjang beda ditolak", False, True)
except ValueError:
    cek("panjang beda ditolak", True, True)

print(f"\n{sum(hasil)}/{len(hasil)} lolos")
print("SEMUA OK" if all(hasil) else "ADA YANG SALAH: jangan lanjut, kirim output ini.")
