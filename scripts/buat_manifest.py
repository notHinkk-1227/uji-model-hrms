"""Buat manifest 16 kolom (protokol v1.0 bagian 9 dan 11) dari nama berkas di raw/.

Hanya membaca NAMA berkas (tidak membuka gambar). Kolom yang detailnya tidak dicatat peneliti diisi
penanda eksplisit, bukan tebakan (keputusan peneliti 2026-11-08; lihat logs/experiment-log.md):
  device_model   inisial samaran HP-<relawan> (model ponsel tidak dicatat; hanya penamaan/pembanding)
  os             tidak_dicatat
  mirror_setting, lux_catatan, night_mode, screen_brightness
                 sesuai_protokol_tidak_dicatat (peneliti: diatur sesuai protokol, detail tidak dicatat)
  attack_display real: -, print: cetak_tidak_dicatat, screen: layar_tidak_dicatat
  session        sesi-1 (semua foto diambil pada hari yang sama)
  pose           frontal (protokol)

Jalankan dari akar proyek:  python scripts/buat_manifest.py [--out JALUR]
Berkas tujuan yang sudah berisi baris data tidak ditimpa kecuali dengan --timpa.
"""
import argparse
import csv
import os
import re
import sys
from collections import Counter

RAW = "datasets/liveness/internal/raw"
OUT = "datasets/liveness/internal/manifest.csv"
POLA = re.compile(r"^(S\d{2})_(own|anchor|stress)_(real|print|screen|replay)_(terang|redup)_(\d+)\.(jpg|png)$")
KOLOM = ["sample_id", "subject", "device_code", "device_model", "os", "camera", "class", "lighting", "pose",
         "attack_display", "session", "mirror_setting", "lux_catatan", "night_mode", "screen_brightness", "filename"]
TIDAK_DICATAT = "sesuai_protokol_tidak_dicatat"
DISPLAY = {"real": "-", "print": "cetak_tidak_dicatat", "screen": "layar_tidak_dicatat", "replay": "layar_tidak_dicatat"}

ap = argparse.ArgumentParser()
ap.add_argument("--out", default=OUT)
ap.add_argument("--timpa", action="store_true")
args = ap.parse_args()

if os.path.exists(args.out) and not args.timpa:
    with open(args.out, newline="", encoding="utf-8") as f:
        if sum(1 for _ in f) > 1:
            sys.exit(f"{args.out} sudah berisi data; pakai --timpa bila memang ingin menimpa.")

baris, salah = [], []
for dp, _, fs in os.walk(RAW):
    for nama in sorted(fs):
        m = POLA.match(nama)
        if not m:
            salah.append(os.path.join(dp, nama))
            continue
        rel, dev, kelas, cahaya, _, _ = m.groups()
        if os.path.normpath(dp) != os.path.normpath(os.path.join(RAW, rel, dev)):
            salah.append(os.path.join(dp, nama))  # folder tidak sesuai nama berkas
            continue
        baris.append({
            "sample_id": os.path.splitext(nama)[0], "subject": rel, "device_code": dev,
            "device_model": f"HP-{rel}", "os": "tidak_dicatat", "camera": "depan", "class": kelas,
            "lighting": cahaya, "pose": "frontal", "attack_display": DISPLAY[kelas], "session": "sesi-1",
            "mirror_setting": TIDAK_DICATAT, "lux_catatan": TIDAK_DICATAT, "night_mode": TIDAK_DICATAT,
            "screen_brightness": TIDAK_DICATAT if kelas in ("screen", "replay") else "-", "filename": nama,
        })

if salah:
    print("BERHENTI: berkas tidak sesuai pola/folder (manifest tidak ditulis):")
    for s in salah[:10]:
        print("  ", s.replace("\\", "/"))
    sys.exit(1)
ids = Counter(b["sample_id"] for b in baris)
if any(n > 1 for n in ids.values()):
    sys.exit("BERHENTI: sample_id ganda.")

with open(args.out, "w", newline="", encoding="utf-8") as f:
    w = csv.DictWriter(f, fieldnames=KOLOM)
    w.writeheader()
    w.writerows(baris)

print(f"baris: {len(baris)} | kolom: {len(KOLOM)} | ditulis: {args.out}")
for rel in sorted({b['subject'] for b in baris}):
    c = Counter((b["class"], b["lighting"]) for b in baris if b["subject"] == rel)
    print(f"  {rel}: " + ", ".join(f"{k}/{l} {n}" for (k, l), n in sorted(c.items())))
