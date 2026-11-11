"""Uji siapkan_data_v2.py pada data TIRUAN (berkas kosong berisi byte acak; tanpa gambar relawan).
Jalankan dari akar proyek: python scripts/test_siapkan_data_v2.py"""
import csv
import os
import sys
import tempfile

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import siapkan_data_v2 as S  # noqa: E402

HASIL = []


def cek(nama, kondisi, info=""):
    HASIL.append(bool(kondisi))
    print(("OK    " if kondisi else "GAGAL ") + nama + (f"  [{info}]" if info and not kondisi else ""))


def buat_sumber(root, ubah=None):
    """4 relawan x (print, screen) x 10 foto; nama campuran gaya iPhone dan Android; huruf besar/kecil folder berbeda."""
    for k, rel in enumerate(["S01", "S02", "S03", "S04"]):
        for kelas, nm in (("print", "Print Kamera Depan" if k < 2 else "Print kamera depan"),
                          ("screen", "Screen Kamera Depan" if k < 2 else "Screen kamera depan")):
            d = os.path.join(root, rel, nm)
            os.makedirs(d)
            for i in range(10):
                n = f"IMG_{8273 + i}.JPG" if k % 2 == 0 else f"20261109_1522{i:02d}.jpg"
                with open(os.path.join(d, n), "wb") as f:
                    f.write(os.urandom(64) + bytes([k, i, 0 if kelas == "print" else 1]))


def manifest_lama(path):
    with open(path, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=S.KOLOM)
        w.writeheader()
        for rel in ["S01", "S02", "S03", "S04"]:
            for i in range(20):
                cah = "terang" if i < 10 else "redup"
                sid = f"{rel}_own_real_{cah}_{i % 10 + 1:03d}"
                w.writerow({**{k: "x" for k in S.KOLOM}, "sample_id": sid, "subject": rel, "device_code": "own", "class": "real",
                            "lighting": cah, "session": "sesi-1", "filename": sid + ".jpg"})


def baca(path):
    with open(path, newline="", encoding="utf-8") as f:
        return list(csv.DictReader(f))


with tempfile.TemporaryDirectory() as tmp:
    src, raw2, out = os.path.join(tmp, "src"), os.path.join(tmp, "raw_v2"), os.path.join(tmp, "out")
    ml, lg = os.path.join(tmp, "manifest.csv"), os.path.join(tmp, "log.csv")
    buat_sumber(src)
    manifest_lama(ml)
    sebelum = sorted(os.path.join(dp, f) for dp, _, fs in os.walk(src) for f in fs)

    # 1. Simulasi tidak mengubah apa pun
    rc = S.jalankan(src, raw2, ml, out, lg, apply=False)
    cek("simulasi: kode 0 dan tidak ada berkas tujuan dibuat", rc == 0 and not os.path.exists(raw2) and not os.path.exists(out))

    # 2. Rencana: 80 foto, nama baru benar, urutan mengikuti nama asal
    rencana, masalah = S.rencana(src)
    cek("rencana: 80 foto tanpa masalah", len(rencana) == 80 and not masalah, masalah)
    s1p = [r for r in rencana if r[0] == "S01" and r[1] == "print"]
    cek("nomor 101..110 dan nama S01_own_print_takdicatat_101.jpg", [r[3] for r in s1p] == [f"S01_own_print_takdicatat_{101 + i}.jpg" for i in range(10)])
    cek("urutan nomor mengikuti nama asal (IMG_8273 -> 101)", os.path.basename(s1p[0][2]) == "IMG_8273.JPG" and os.path.basename(s1p[-1][2]) == "IMG_8282.JPG")

    # 3. Apply
    rc = S.jalankan(src, raw2, ml, out, lg, apply=True)
    cek("apply: kode 0", rc == 0)
    dest = sorted(os.path.join(dp, f) for dp, _, fs in os.walk(raw2) for f in fs)
    cek("apply: 80 berkas di raw_v2/S0x/own/", len(dest) == 80 and all(os.sep + "own" + os.sep in d for d in dest))
    cek("apply: berkas asal tidak berubah dan tidak hilang", sorted(os.path.join(dp, f) for dp, _, fs in os.walk(src) for f in fs) == sebelum)
    cek("apply: ekstensi huruf kecil .jpg", all(d.endswith(".jpg") for d in dest))
    mv2, mr, ms = baca(os.path.join(out, "manifest_v2.csv")), baca(os.path.join(out, "manifest_v2_real.csv")), baca(os.path.join(out, "manifest_v2_serangan.csv"))
    cek("manifest: 160 gabungan = 80 real lama + 80 serangan baru", len(mv2) == 160 and len(mr) == 80 and len(ms) == 80)
    cek("manifest: sample_id unik", len({r["sample_id"] for r in mv2}) == 160)
    cek("manifest serangan: sesi-2, lighting tidak_dicatat, kelas print/screen 40:40",
        all(r["session"] == "sesi-2" and r["lighting"] == "tidak_dicatat" for r in ms)
        and sum(r["class"] == "print" for r in ms) == 40 and sum(r["class"] == "screen" for r in ms) == 40)
    cek("manifest real: tetap sesi-1 dan kelas real", all(r["session"] == "sesi-1" and r["class"] == "real" for r in mr))
    cek("manifest: filename sesuai berkas yang ada di raw_v2", all(os.path.exists(os.path.join(raw2, r["subject"], "own", r["filename"])) for r in ms))
    lgr = baca(lg)
    cek("catatan asal-nama: 80 baris dengan SHA-256", len(lgr) == 80 and all(len(r["sha256"]) == 64 for r in lgr))

    # 4. Tidak menimpa
    rc2 = S.jalankan(src, raw2, ml, out, lg, apply=True)
    cek("jalan kedua berhenti karena tujuan sudah ada (tidak menimpa)", rc2 == 1)

with tempfile.TemporaryDirectory() as tmp:
    # 5. Jumlah salah -> berhenti sebelum mengubah apa pun
    src, raw2, out = os.path.join(tmp, "src"), os.path.join(tmp, "raw_v2"), os.path.join(tmp, "out")
    ml, lg = os.path.join(tmp, "manifest.csv"), os.path.join(tmp, "log.csv")
    buat_sumber(src)
    manifest_lama(ml)
    d = os.path.join(src, "S03", "Screen kamera depan")
    os.remove(os.path.join(d, sorted(os.listdir(d))[0]))
    rc = S.jalankan(src, raw2, ml, out, lg, apply=True)
    cek("jumlah foto salah: berhenti, tidak ada yang disalin", rc == 1 and not os.path.exists(raw2))

with tempfile.TemporaryDirectory() as tmp:
    # 6. Format HEIC -> berhenti
    src, raw2, out = os.path.join(tmp, "src"), os.path.join(tmp, "raw_v2"), os.path.join(tmp, "out")
    ml, lg = os.path.join(tmp, "manifest.csv"), os.path.join(tmp, "log.csv")
    buat_sumber(src)
    manifest_lama(ml)
    d = os.path.join(src, "S01", "Print Kamera Depan")
    os.rename(os.path.join(d, "IMG_8273.JPG"), os.path.join(d, "IMG_8273.HEIC"))
    rc = S.jalankan(src, raw2, ml, out, lg, apply=True)
    cek("format HEIC: berhenti dan tidak mengonversi", rc == 1 and not os.path.exists(raw2))

n = sum(HASIL)
print(f"\n{n}/{len(HASIL)} lolos")
sys.exit(0 if n == len(HASIL) else 1)
