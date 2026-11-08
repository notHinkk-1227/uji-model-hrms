"""Pemeriksaan kualitas data uji internal (administratif; TIDAK menampilkan wajah).

1. Duplikat: berkas enrollment yang isinya identik (SHA-256) dengan berkas di raw/ (kebocoran
   enrollment -> probe). Hasil ditulis ke datasets/recognition/internal/duplikat_enrollment.csv.
2. Ringkasan per relawan: rasio gambar, orientasi EXIF, rentang ukuran (dari inventaris.csv),
   dan daftar berkas yang rasionya bukan 3:4.

Jalankan dari akar proyek, setelah inventaris_data.py:
    python scripts/periksa_data.py
"""
import csv
import hashlib
import os
from collections import Counter, defaultdict

RAW = "datasets/liveness/internal/raw"
ENR = "datasets/recognition/internal/enrollment"
INV = "datasets/liveness/internal/inventaris.csv"
OUT_DUP = "datasets/recognition/internal/duplikat_enrollment.csv"
TOLERANSI_RASIO = 0.03  # |rasio - 0,75| lebih dari ini dianggap bukan 3:4


def sha256(path):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for blok in iter(lambda: f.read(1 << 20), b""):
            h.update(blok)
    return h.hexdigest()


def berkas(root):
    for dp, _, fs in os.walk(root):
        for f in sorted(fs):
            yield os.path.join(dp, f).replace("\\", "/")


def relawan_dari(path):
    nama = os.path.basename(path)
    return nama.split("_")[0].upper()


print("=== 1. Duplikat enrollment <-> raw ===")
enr = defaultdict(list)
for p in berkas(ENR):
    enr[sha256(p)].append(p)
raw = defaultdict(list)
for p in berkas(RAW):
    raw[sha256(p)].append(p)

jumlah_enr = sum(len(v) for v in enr.values())
dup = [(e, r) for h, rs in raw.items() if h in enr for r in rs for e in enr[h]]
print(f"berkas enrollment: {jumlah_enr} | berkas raw: {sum(len(v) for v in raw.values())}")
print(f"pasangan enrollment-raw identik: {len(dup)}")
per_rel = Counter(relawan_dari(e) for e, _ in dup)
for rel in sorted({relawan_dari(p) for ps in enr.values() for p in ps}):
    n_enr = sum(1 for ps in enr.values() for p in ps if relawan_dari(p) == rel)
    print(f"  {rel}: {per_rel.get(rel, 0)} dari {n_enr} foto enrollment juga ada di raw")
os.makedirs(os.path.dirname(OUT_DUP), exist_ok=True)
with open(OUT_DUP, "w", newline="", encoding="utf-8") as f:
    w = csv.writer(f)
    w.writerow(["berkas_enrollment", "berkas_raw_identik"])
    w.writerows(dup)
print("daftar duplikat ditulis:", OUT_DUP)
kembar_raw = [ps for ps in raw.values() if len(ps) > 1]
print(f"kelompok berkas identik di dalam raw sendiri: {len(kembar_raw)}")

print("\n=== 2. Rasio, orientasi, ukuran per relawan (dari inventaris.csv) ===")
if not os.path.exists(INV):
    raise SystemExit("inventaris.csv belum ada; jalankan scripts/inventaris_data.py dulu.")
with open(INV, newline="", encoding="utf-8") as f:
    baris = [b for b in csv.DictReader(f) if b["status"] == "ok"]
per = defaultdict(list)
for b in baris:
    per[b["relawan"]].append(b)
for rel in sorted(per):
    bs = per[rel]
    rasio = Counter(round(float(b["rasio_wh"]), 2) for b in bs)
    ori = Counter(b["orientasi_exif"] for b in bs)
    lebar = [int(b["lebar"]) for b in bs]
    tinggi = [int(b["tinggi"]) for b in bs]
    print(f"{rel}: {len(bs)} berkas | ukuran lebar {min(lebar)}-{max(lebar)}, tinggi {min(tinggi)}-{max(tinggi)}")
    print(f"      rasio: {dict(rasio)} | orientasi EXIF: {dict(ori)}")
    bukan = [b for b in bs if abs(float(b["rasio_wh"]) - 0.75) > TOLERANSI_RASIO]
    if bukan:
        per_kelas = Counter(b["kelas"] for b in bukan)
        print(f"      BUKAN 3:4: {len(bukan)} berkas {dict(per_kelas)}; contoh: "
              + ", ".join(os.path.basename(b["path"]) for b in bukan[:3]))
