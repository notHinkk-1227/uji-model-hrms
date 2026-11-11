"""Siapkan data liveness v2 (amandemen 7): salin foto serangan baru ke raw_v2 dengan nama baku dan buat manifest v2.

Tidak membuka atau menampilkan gambar: hanya membaca NAMA berkas dan menghitung SHA-256 (untuk memastikan salinan identik).
Berkas asal TIDAK diubah, dipindah, atau dihapus. Berkas tujuan tidak pernah ditimpa. Default adalah SIMULASI.

Struktur sumber yang diharapkan:  SUMBER/S01/<folder berisi 'print'>/*.jpg   dan   SUMBER/S01/<folder berisi 'screen'>/*.jpg
(huruf besar/kecil tidak dibedakan). Tiap relawan harus punya tepat 10 foto print dan 10 foto screen.

Nama baru:  S01_own_print_takdicatat_101.jpg  (relawan_perangkat_kelas_cahaya_nomor). Nomor mulai 101 agar tidak bentrok dengan
penomoran lama. Urutan nomor mengikuti NAMA berkas asal (urutan pengambilan pada IMG_xxxx dan tanggal_jam), bukan waktu simpan.
Pencahayaan tidak dibedakan saat pengambilan (keputusan peneliti), jadi diisi 'takdicatat' pada nama dan 'tidak_dicatat' pada manifest.

Keluaran (di --out_dir, default datasets/liveness/internal):
  manifest_v2.csv           foto asli lama (sesi-1) + foto serangan baru (sesi-2), untuk evaluasi
  manifest_v2_real.csv      hanya foto asli lama  (dipakai infer_liveness dengan --root datasets/liveness/internal/raw)
  manifest_v2_serangan.csv  hanya serangan baru   (dipakai infer_liveness dengan --root datasets/liveness/internal/raw_v2)
Catatan asal-nama: datasets/rename_log_v2.csv

Contoh (dari akar proyek):
  python scripts/siapkan_data_v2.py --src /d/dataset-kp/new-dataset            (simulasi)
  python scripts/siapkan_data_v2.py --src /d/dataset-kp/new-dataset --apply    (jalankan)
"""
import argparse
import csv
import hashlib
import os
import re
import shutil
import sys

KOLOM = ["sample_id", "subject", "device_code", "device_model", "os", "camera", "class", "lighting", "pose",
         "attack_display", "session", "mirror_setting", "lux_catatan", "night_mode", "screen_brightness", "filename"]
TIDAK_DICATAT = "sesuai_protokol_tidak_dicatat"
DISPLAY = {"print": "cetak_tidak_dicatat", "screen": "layar_tidak_dicatat"}
POLA_REL = re.compile(r"^S\d{2}$")
NOMOR_AWAL = 101
JUMLAH_PER_KELAS = 10
EKSTENSI = {".jpg", ".jpeg"}


def sha256(path):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for blok in iter(lambda: f.read(1 << 20), b""):
            h.update(blok)
    return h.hexdigest()


def rencana(src):
    """Kembalikan (daftar (relawan, kelas, jalur_asal, nama_baru), daftar masalah). Hanya membaca nama."""
    masalah, hasil = [], []
    if not os.path.isdir(src):
        return [], [f"folder sumber tidak ada: {src}"]
    relawan = sorted(d for d in os.listdir(src) if os.path.isdir(os.path.join(src, d)))
    if not relawan:
        return [], ["tidak ada subfolder relawan di sumber"]
    for rel in relawan:
        if not POLA_REL.match(rel):
            masalah.append(f"nama folder relawan tidak sesuai pola S01..: {rel}")
            continue
        for kelas in ("print", "screen"):
            cocok = [d for d in os.listdir(os.path.join(src, rel))
                     if os.path.isdir(os.path.join(src, rel, d)) and kelas in d.lower()]
            if len(cocok) != 1:
                masalah.append(f"{rel}: harus ada tepat 1 folder berisi '{kelas}', ditemukan {len(cocok)}")
                continue
            folder = os.path.join(src, rel, cocok[0])
            berkas = sorted(f for f in os.listdir(folder) if os.path.isfile(os.path.join(folder, f)) and not f.startswith("."))
            buruk = [f for f in berkas if os.path.splitext(f)[1].lower() not in EKSTENSI]
            if buruk:
                masalah.append(f"{rel}/{kelas}: format bukan JPEG, jangan dikonversi sendiri: {buruk[:3]}")
                continue
            if len(berkas) != JUMLAH_PER_KELAS:
                masalah.append(f"{rel}/{kelas}: {len(berkas)} foto, seharusnya {JUMLAH_PER_KELAS}")
                continue
            for i, nama in enumerate(berkas):
                baru = f"{rel}_own_{kelas}_takdicatat_{NOMOR_AWAL + i}.jpg"
                hasil.append((rel, kelas, os.path.join(folder, nama), baru))
    return hasil, masalah


def baris_manifest_baru(rel, kelas, baru):
    return {"sample_id": os.path.splitext(baru)[0], "subject": rel, "device_code": "own", "device_model": f"HP-{rel}",
            "os": "tidak_dicatat", "camera": "depan", "class": kelas, "lighting": "tidak_dicatat", "pose": "frontal",
            "attack_display": DISPLAY[kelas], "session": "sesi-2", "mirror_setting": TIDAK_DICATAT,
            "lux_catatan": TIDAK_DICATAT, "night_mode": TIDAK_DICATAT, "screen_brightness": TIDAK_DICATAT, "filename": baru}


def tulis_csv(path, baris):
    with open(path, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=KOLOM)
        w.writeheader()
        w.writerows(baris)


def jalankan(src, raw_v2, manifest_lama, out_dir, log_path, apply):
    """Kembalikan 0 bila berhasil (atau simulasi bersih), 1 bila ada masalah."""
    rc, masalah = rencana(src)
    if masalah:
        print("BERHENTI: ada masalah pada sumber (tidak ada yang diubah):")
        for m in masalah:
            print("  -", m)
        return 1
    if not os.path.exists(manifest_lama):
        print(f"BERHENTI: manifest lama tidak ada: {manifest_lama}")
        return 1
    with open(manifest_lama, newline="", encoding="utf-8") as f:
        lama = [r for r in csv.DictReader(f) if r["class"] == "real"]
    if len(lama) != 80:
        print(f"BERHENTI: foto asli lama di manifest = {len(lama)}, diharapkan 80")
        return 1
    tujuan = [os.path.join(raw_v2, rel, "own", baru) for rel, _, _, baru in rc]
    ada = [t for t in tujuan if os.path.exists(t)]
    if ada:
        print(f"BERHENTI: {len(ada)} berkas tujuan sudah ada (tidak ditimpa), mis. {ada[0]}")
        return 1
    print(f"{'SIMULASI' if not apply else 'MENJALANKAN'}: {len(rc)} foto -> {raw_v2}")
    per = {}
    for rel, kelas, _, _ in rc:
        per[(rel, kelas)] = per.get((rel, kelas), 0) + 1
    for (rel, kelas), n in sorted(per.items()):
        print(f"  {rel} {kelas}: {n}")
    print("  contoh:", os.path.basename(rc[0][2]), "->", rc[0][3], "| ", os.path.basename(rc[-1][2]), "->", rc[-1][3])
    if not apply:
        print("Tidak ada berkas diubah. Tambahkan --apply untuk menjalankan.")
        return 0
    catatan = []
    for (rel, kelas, asal, baru), t in zip(rc, tujuan):
        os.makedirs(os.path.dirname(t), exist_ok=True)
        shutil.copy2(asal, t)
        h1, h2 = sha256(asal), sha256(t)
        if h1 != h2:
            print(f"BERHENTI: salinan tidak identik: {asal}")
            return 1
        catatan.append({"asal": asal.replace("\\", "/"), "baru": os.path.relpath(t, raw_v2).replace("\\", "/"), "sha256": h1})
    baru_rows = [baris_manifest_baru(rel, kelas, baru) for rel, kelas, _, baru in rc]
    ids = [r["sample_id"] for r in lama + baru_rows]
    if len(set(ids)) != len(ids):
        print("BERHENTI: sample_id ganda pada manifest gabungan (salinan sudah dibuat; periksa).")
        return 1
    os.makedirs(out_dir, exist_ok=True)
    tulis_csv(os.path.join(out_dir, "manifest_v2.csv"), lama + baru_rows)
    tulis_csv(os.path.join(out_dir, "manifest_v2_real.csv"), lama)
    tulis_csv(os.path.join(out_dir, "manifest_v2_serangan.csv"), baru_rows)
    with open(log_path, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=["asal", "baru", "sha256"])
        w.writeheader()
        w.writerows(catatan)
    print(f"Selesai: {len(rc)} foto disalin dan diverifikasi SHA-256; manifest v2 ditulis di {out_dir}; catatan di {log_path}")
    return 0


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--src", required=True)
    ap.add_argument("--raw_v2", default="datasets/liveness/internal/raw_v2")
    ap.add_argument("--manifest_lama", default="datasets/liveness/internal/manifest.csv")
    ap.add_argument("--out_dir", default="datasets/liveness/internal")
    ap.add_argument("--log", default="datasets/rename_log_v2.csv")
    ap.add_argument("--apply", action="store_true")
    a = ap.parse_args()
    sys.exit(jalankan(a.src, a.raw_v2, a.manifest_lama, a.out_dir, a.log, a.apply))


if __name__ == "__main__":
    main()
