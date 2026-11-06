"""Beri nama baku dan pindahkan foto per batch ke struktur dataset.

Cara kerja: taruh foto satu batch dalam satu folder di datasets/_masuk/ dengan nama folder
yang menyatakan isinya, lalu jalankan skrip ini. Parameter dibaca dari NAMA FOLDER.

Nama folder batch liveness : S01_own_real_terang   (relawan_perangkat_kelas_cahaya)
Nama folder batch enrollment: S01_enroll            (foto pendaftaran wajah, untuk pengenalan)

Contoh:
  python scripts/rename_foto.py --src datasets/_masuk/S01_own_real_terang           (simulasi)
  python scripts/rename_foto.py --src datasets/_masuk/S01_own_real_terang --apply   (jalankan)
  python scripts/rename_foto.py --semua                                             (simulasi semua batch)
  python scripts/rename_foto.py --semua --apply

Default adalah SIMULASI: tidak ada berkas yang diubah sebelum --apply. Berkas tidak pernah
ditimpa; penomoran melanjutkan nomor terbesar yang sudah ada. Urutan nomor mengikuti waktu
modifikasi berkas (urutan pengambilan), lalu nama berkas.
"""
import argparse
import csv
import os
import re
import shutil
import sys
from datetime import datetime

LOG = "datasets/rename_log.csv"  # catatan nama asal -> nama baru (jejak asal berkas)
MASUK = "datasets/_masuk"
RAW = "datasets/liveness/internal/raw"
ENROLL = "datasets/recognition/internal/enrollment"
POLA_BATCH = re.compile(r"^(S\d{2})_(own|anchor|stress)_(real|print|screen|replay)_(terang|redup)$")
POLA_ENROLL = re.compile(r"^(S\d{2})_enroll$")
POLA_FILE = re.compile(r"^(S\d{2})_(own|anchor|stress)_(real|print|screen|replay)_(terang|redup)_(\d+)\.\w+$")
POLA_FILE_ENROLL = re.compile(r"^(S\d{2})_enroll_(\d+)\.\w+$")
TARGET = {"real": 10, "print": 5, "screen": 5, "replay": 5}  # per relawan per perangkat per cahaya (protokol v1.0)
EKSTENSI = {".jpg": ".jpg", ".jpeg": ".jpg", ".png": ".png"}


def daftar_berkas(folder):
    nama = [f for f in os.listdir(folder) if os.path.isfile(os.path.join(folder, f)) and not f.startswith(".")]
    return sorted(nama, key=lambda f: (os.path.getmtime(os.path.join(folder, f)), f))


def proses_batch(folder, apply, diam=False):
    """Kembalikan jumlah berkas yang direncanakan, 0 bila dilewati, -1 bila ada masalah."""
    nama = os.path.basename(os.path.normpath(folder))
    m1, m2 = POLA_BATCH.match(nama), POLA_ENROLL.match(nama)
    if not (m1 or m2):
        if not diam:
            print(f"[lewati] nama folder tidak sesuai pola: {nama}")
        return 0
    files = daftar_berkas(folder)
    buruk = [f for f in files if os.path.splitext(f)[1].lower() not in EKSTENSI]
    if buruk:
        print(f"[BERHENTI] {nama}: format tidak didukung (mis. HEIC): {buruk[:5]}. "
              "Jangan dikonversi sendiri; tanyakan dulu.")
        return -1

    if m1:
        relawan, perangkat, kelas, cahaya = m1.groups()
        tujuan = os.path.join(RAW, relawan, perangkat)
        awalan = f"{relawan}_{perangkat}_{kelas}_{cahaya}_"
        ada = [int(m.group(5)) for f in (os.listdir(tujuan) if os.path.isdir(tujuan) else [])
               for m in [POLA_FILE.match(f)] if m and m.groups()[:4] == (relawan, perangkat, kelas, cahaya)]
        info_target = f"(protokol: {TARGET[kelas]})"
    else:
        relawan = m2.group(1)
        tujuan = os.path.join(ENROLL, relawan)
        awalan = f"{relawan}_enroll_"
        ada = [int(m.group(2)) for f in (os.listdir(tujuan) if os.path.isdir(tujuan) else [])
               for m in [POLA_FILE_ENROLL.match(f)] if m]
        info_target = "(protokol: 5)"
    mulai = max(ada) + 1 if ada else 1
    rencana = [(f, f"{awalan}{mulai + i:02d}{EKSTENSI[os.path.splitext(f)[1].lower()]}") for i, f in enumerate(files)]
    if not diam:
        print(f"\n{nama}: {len(files)} berkas {info_target}; sudah ada di tujuan: {len(ada)}; mulai nomor {mulai:02d}")
        for f, baru in rencana:
            print(f"  {f}  ->  {tujuan.replace(os.sep, '/')}/{baru}")
    if apply:
        os.makedirs(tujuan, exist_ok=True)
        os.makedirs(os.path.dirname(LOG), exist_ok=True)
        log_baru = not os.path.exists(LOG)
        with open(LOG, "a", newline="", encoding="utf-8") as lf:
            w = csv.writer(lf)
            if log_baru:
                w.writerow(["waktu", "batch", "nama_asal", "nama_baru"])
            for f, baru in rencana:
                dst = os.path.join(tujuan, baru)
                if os.path.exists(dst):
                    sys.exit(f"Tujuan sudah ada, dibatalkan: {dst}")
                shutil.move(os.path.join(folder, f), dst)
                w.writerow([datetime.now().isoformat(timespec="seconds"), nama, f, baru])
    return len(rencana)


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--src", help="satu folder batch di datasets/_masuk")
    ap.add_argument("--semua", action="store_true", help="proses semua subfolder di datasets/_masuk")
    ap.add_argument("--apply", action="store_true", help="benar-benar memindahkan dan mengganti nama")
    args = ap.parse_args()
    if bool(args.src) == bool(args.semua):
        ap.error("pilih salah satu: --src FOLDER atau --semua")

    folders = [args.src] if args.src else [
        os.path.join(MASUK, d) for d in sorted(os.listdir(MASUK)) if os.path.isdir(os.path.join(MASUK, d))]
    if not folders:
        sys.exit(f"Tidak ada folder batch di {MASUK}")

    if args.apply:  # periksa semua dulu; jangan mengubah apa pun bila ada masalah
        if any(proses_batch(f, False, diam=True) == -1 for f in folders):
            sys.exit("Ada masalah pada salah satu batch; tidak ada yang dipindahkan.")
    total = sum(max(proses_batch(f, args.apply), 0) for f in folders)
    print(f"\nTotal berkas {'dipindahkan' if args.apply else 'direncanakan (SIMULASI, belum ada yang diubah)'}: {total}")


if __name__ == "__main__":
    main()
