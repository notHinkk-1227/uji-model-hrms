"""Inventaris administratif data uji internal (TIDAK menampilkan atau menganalisis wajah).

Hanya membaca nama berkas dan header gambar (ukuran, format, orientasi EXIF), lalu mencetak
ringkasan dan menulis CSV inventaris. Jalankan dari akar proyek:
    python scripts/inventaris_data.py [folder_raw]

Pola nama yang diharapkan: S01_own_real_terang_01.jpg
  relawan (S01..S04) _ perangkat (own/anchor/stress) _ kelas (real/print/screen/replay)
  _ cahaya (terang/redup) _ nomor . ekstensi
Berkas yang tidak cocok pola atau tidak terbaca dilaporkan, tidak dibuang.
"""
import csv
import os
import re
import sys
from collections import Counter, defaultdict

from PIL import Image

ROOT = sys.argv[1] if len(sys.argv) > 1 else "datasets/liveness/internal/raw"
OUT = "datasets/liveness/internal/inventaris.csv"
POLA = re.compile(r"^(S\d{2})_(own|anchor|stress)_(real|print|screen|replay)_(terang|redup)_(\d+)\.(\w+)$", re.I)

baris = []
ekstensi = Counter()
for dirpath, _, files in os.walk(ROOT):
    for nama in sorted(files):
        path = os.path.join(dirpath, nama)
        ext = os.path.splitext(nama)[1].lower().lstrip(".")
        ekstensi[ext] += 1
        m = POLA.match(nama)
        rec = {"path": path.replace("\\", "/"), "ekstensi": ext, "pola_nama": "ok" if m else "TIDAK_COCOK",
               "relawan": "", "perangkat": "", "kelas": "", "cahaya": "", "nomor": "",
               "lebar": "", "tinggi": "", "orientasi_exif": "", "rasio_wh": "", "status": ""}
        if m:
            rec.update(relawan=m.group(1).upper(), perangkat=m.group(2).lower(), kelas=m.group(3).lower(),
                       cahaya=m.group(4).lower(), nomor=m.group(5))
        try:
            with Image.open(path) as im:
                w, h = im.size
                ori = im.getexif().get(274, 1)
            if ori in (5, 6, 7, 8):  # cv2.imread menerapkan orientasi EXIF; ukuran efektif tertukar
                w, h = h, w
            rec.update(lebar=w, tinggi=h, orientasi_exif=ori, rasio_wh=round(w / h, 3), status="ok")
        except Exception as e:
            rec["status"] = f"TIDAK_TERBACA:{type(e).__name__}"
        baris.append(rec)

if not baris:
    sys.exit(f"Tidak ada berkas di {ROOT}")

os.makedirs(os.path.dirname(OUT), exist_ok=True)
with open(OUT, "w", newline="", encoding="utf-8") as f:
    wr = csv.DictWriter(f, fieldnames=list(baris[0].keys()))
    wr.writeheader()
    wr.writerows(baris)

print(f"Total berkas: {len(baris)} | ekstensi: {dict(ekstensi)}")
tak_cocok = [b for b in baris if b["pola_nama"] != "ok"]
tak_baca = [b for b in baris if b["status"] != "ok"]
print(f"Nama tidak cocok pola: {len(tak_cocok)} | tidak terbaca: {len(tak_baca)}")
for b in (tak_cocok + tak_baca)[:10]:
    print("  perlu dicek:", b["path"], "|", b["pola_nama"], "|", b["status"])

hit = defaultdict(Counter)
for b in baris:
    if b["pola_nama"] == "ok":
        hit[(b["relawan"], b["perangkat"])][b["kelas"]] += 1
kelas_urut = ["real", "print", "screen", "replay"]
print("\nrelawan  perangkat  " + "  ".join(f"{k:>6s}" for k in kelas_urut) + "   total")
for (r, p), c in sorted(hit.items()):
    print(f"{r:8s} {p:9s}  " + "  ".join(f"{c[k]:6d}" for k in kelas_urut) + f"   {sum(c.values()):5d}")

cahaya = Counter((b["kelas"], b["cahaya"]) for b in baris if b["pola_nama"] == "ok")
print("\nkelas x cahaya:", {f"{k}/{c}": n for (k, c), n in sorted(cahaya.items())})

ok = [b for b in baris if b["status"] == "ok"]
if ok:
    lebar = [b["lebar"] for b in ok]
    tinggi = [b["tinggi"] for b in ok]
    rasio = Counter(round(b["rasio_wh"], 2) for b in ok)
    print(f"\nukuran efektif: lebar {min(lebar)}-{max(lebar)} px, tinggi {min(tinggi)}-{max(tinggi)} px")
    print("rasio lebar/tinggi (dibulatkan 0,01), 5 terbanyak:", rasio.most_common(5), "(3:4 potret = 0,75)")
    print("orientasi EXIF:", dict(Counter(b["orientasi_exif"] for b in ok)))
print("\nCSV inventaris:", OUT)
