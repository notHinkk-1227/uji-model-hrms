"""Periksa syarat lolos amandemen 7 bagian 4 dari header EXIF (TANPA membaca piksel; hanya ukuran dan tag tertentu).

Tag yang diambil: orientasi, bukaan (FNumber), panjang fokus, nama lensa (hanya untuk menentukan arah kamera depan/belakang;
nama tidak dicetak). GPS, tanggal, nomor seri, merek, model, dan software TIDAK diambil. Keluaran hanya agregat per relawan.

Syarat per relawan (amandemen 7 bagian 4):
  1. foto serangan baru dan foto asli lama memakai lensa yang sama (himpunan pasangan bukaan + panjang fokus identik);
  2. himpunan ukuran asli (setelah orientasi) foto serangan baru dan foto asli lama tumpang tindih.
Butir 3 (kontrol sesi) tidak berlaku: foto kontrol tidak diambil. Tambahan informatif: jumlah foto menurut arah kamera dari nama lensa.

Jalankan dari akar proyek:
  python scripts/periksa_exif_v2.py [--rinci]
"""
import argparse
import csv
import json
import os
import sys
from collections import Counter, defaultdict

from PIL import Image

IFD_EXIF, T_ORI, T_F, T_FOKUS, T_LENS = 0x8769, 0x0112, 0x829D, 0x920A, 0xA434


def arah_kamera(nama):
    if not nama:
        return "tidak_diketahui"
    s = str(nama).lower()
    if "front" in s or "depan" in s:
        return "depan"
    if "back" in s or "rear" in s or "belakang" in s:
        return "belakang"
    return "tidak_diketahui"


def baca_tag(path):
    """Kembalikan dict agregat-aman: ukuran efektif, bukaan, panjang fokus, arah. None bila tidak terbaca."""
    try:
        with Image.open(path) as im:
            w, h = im.size
            ex = im.getexif()
            ori = ex.get(T_ORI, 1)
            sub = ex.get_ifd(IFD_EXIF)
            f, fokus, lens = sub.get(T_F), sub.get(T_FOKUS), sub.get(T_LENS)
    except Exception:
        return None
    if ori in (5, 6, 7, 8):
        w, h = h, w
    return {"ukuran": (int(w), int(h)),
            "lensa": (round(float(f), 2), round(float(fokus), 2)) if f is not None and fokus is not None else None,
            "arah": arah_kamera(lens)}


def ringkas(real, serangan):
    """real dan serangan: daftar hasil baca_tag (None = tidak terbaca) untuk satu relawan."""
    r_ok, s_ok = [t for t in real if t], [t for t in serangan if t]
    out = {"n_real": len(real), "n_serangan": len(serangan),
           "tidak_terbaca": {"real": len(real) - len(r_ok), "serangan": len(serangan) - len(s_ok)},
           "arah_real": dict(Counter(t["arah"] for t in r_ok)), "arah_serangan": dict(Counter(t["arah"] for t in s_ok))}
    lr, ls = {t["lensa"] for t in r_ok}, {t["lensa"] for t in s_ok}
    out["jumlah_kombinasi_lensa"] = {"real": len(lr - {None}), "serangan": len(ls - {None})}
    if len(r_ok) != len(real) or len(s_ok) != len(serangan) or None in lr or None in ls:
        out["lensa_sama"] = None  # tidak dapat dinilai: ada foto tanpa EXIF lensa atau tidak terbaca
    else:
        out["lensa_sama"] = lr == ls
    ur, us = {t["ukuran"] for t in r_ok}, {t["ukuran"] for t in s_ok}
    out["ukuran_real"] = sorted(f"{w}x{h}" for w, h in ur)
    out["ukuran_serangan"] = sorted(f"{w}x{h}" for w, h in us)
    out["ukuran_tumpang_tindih"] = bool(ur & us) if ur and us else None
    out["_kombinasi"] = {"real": sorted(map(str, lr)), "serangan": sorted(map(str, ls))}
    return out


def vonis(nilai):
    """Kegagalan pasti pada satu relawan tidak boleh tertutup oleh relawan lain yang tidak dapat dinilai."""
    if any(v is False for v in nilai):
        return "GAGAL"
    if any(v is None for v in nilai):
        return "TIDAK DAPAT DINILAI"
    return "LULUS"


def baca_manifest(path):
    with open(path, newline="", encoding="utf-8") as f:
        return list(csv.DictReader(f))


def kumpulkan(manifest, root):
    per = defaultdict(list)
    for m in manifest:
        per[m["subject"]].append(baca_tag(os.path.join(root, m["subject"], m["device_code"], m["filename"])))
    return per


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    base = "datasets/liveness/internal"
    ap.add_argument("--real", default=f"{base}/manifest_v2_real.csv")
    ap.add_argument("--serangan", default=f"{base}/manifest_v2_serangan.csv")
    ap.add_argument("--root_real", default=f"{base}/raw")
    ap.add_argument("--root_serangan", default=f"{base}/raw_v2")
    ap.add_argument("--out", default="results/liveness/v2_syarat_exif.json")
    ap.add_argument("--rinci", action="store_true", help="cetak juga kombinasi bukaan dan panjang fokus")
    a = ap.parse_args()
    pr, ps = kumpulkan(baca_manifest(a.real), a.root_real), kumpulkan(baca_manifest(a.serangan), a.root_serangan)
    hasil = {s: ringkas(pr.get(s, []), ps.get(s, [])) for s in sorted(set(pr) | set(ps))}
    s1 = vonis([h["lensa_sama"] for h in hasil.values()])
    s2 = vonis([h["ukuran_tumpang_tindih"] for h in hasil.values()])
    print("Per relawan (hanya agregat; tidak ada gambar dibuka, hanya header):")
    for s, h in hasil.items():
        print(f"  {s}: real {h['n_real']} | serangan {h['n_serangan']} | tidak terbaca {h['tidak_terbaca']} | "
              f"kombinasi lensa {h['jumlah_kombinasi_lensa']} | lensa sama: {h['lensa_sama']} | ukuran tumpang tindih: {h['ukuran_tumpang_tindih']}")
        print(f"      arah kamera (informatif) real {h['arah_real']} | serangan {h['arah_serangan']}")
        print(f"      ukuran real {h['ukuran_real']} | ukuran serangan {h['ukuran_serangan']}")
        if a.rinci:
            print(f"      kombinasi bukaan,fokus real {h['_kombinasi']['real']} | serangan {h['_kombinasi']['serangan']}")
    print(f"\nSYARAT 1 (lensa sama, semua relawan): {s1}")
    print(f"SYARAT 2 (ukuran tumpang tindih, semua relawan): {s2}")
    print("BUTIR 3 (kontrol sesi): tidak berlaku, foto kontrol tidak diambil")
    simpan = {s: {k: v for k, v in h.items() if not k.startswith("_")} for s, h in hasil.items()}
    os.makedirs(os.path.dirname(a.out) or ".", exist_ok=True)
    with open(a.out, "w", encoding="utf-8") as f:
        json.dump({"syarat_1_lensa_sama": s1, "syarat_2_ukuran_tumpang_tindih": s2, "per_relawan": simpan}, f, indent=1, ensure_ascii=False)
    print("Tersimpan:", a.out)
    return 0 if s1 == "LULUS" and s2 == "LULUS" else 2


if __name__ == "__main__":
    sys.exit(main())
