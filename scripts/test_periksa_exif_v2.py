"""Uji periksa_exif_v2.py pada gambar TIRUAN berisi EXIF buatan (bukan foto relawan).
Jalankan dari akar proyek: python scripts/test_periksa_exif_v2.py"""
import hashlib
import json
import os
import sys
import tempfile

from PIL import Image

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import periksa_exif_v2 as P  # noqa: E402

HASIL = []


def cek(nama, kondisi, info=""):
    HASIL.append(bool(kondisi))
    print(("OK    " if kondisi else "GAGAL ") + nama + (f"  [{info}]" if info and not kondisi else ""))


def buat(path, ukuran=(30, 40), f=2.2, fokus=2.71, lens="front camera", ori=1):
    im = Image.new("RGB", ukuran, (5, 5, 5))
    ex = Image.Exif()
    if ori != 1:
        ex[0x0112] = ori
    sub = ex.get_ifd(0x8769)
    if f is not None:
        sub[0x829D] = f
    if fokus is not None:
        sub[0x920A] = fokus
    if lens is not None:
        sub[0xA434] = lens
    os.makedirs(os.path.dirname(path), exist_ok=True)
    im.save(path, exif=ex)


def sha(root):
    h = hashlib.sha256()
    for dp, _, fs in sorted(os.walk(root)):
        for f in sorted(fs):
            h.update(open(os.path.join(dp, f), "rb").read())
    return h.hexdigest()


with tempfile.TemporaryDirectory() as tmp:
    rr, rs = os.path.join(tmp, "raw"), os.path.join(tmp, "raw_v2")
    # S01: semuanya sama -> lulus. S02: panjang fokus serangan beda. S03: ukuran tak tumpang tindih. S04: EXIF lensa serangan hilang.
    for i in range(3):
        buat(os.path.join(rr, "S01", "own", f"a{i}.jpg")); buat(os.path.join(rs, "S01", "own", f"b{i}.jpg"))
        buat(os.path.join(rr, "S02", "own", f"a{i}.jpg")); buat(os.path.join(rs, "S02", "own", f"b{i}.jpg"), fokus=5.1, lens="back camera")
        buat(os.path.join(rr, "S03", "own", f"a{i}.jpg")); buat(os.path.join(rs, "S03", "own", f"b{i}.jpg"), ukuran=(60, 80))
        buat(os.path.join(rr, "S04", "own", f"a{i}.jpg")); buat(os.path.join(rs, "S04", "own", f"b{i}.jpg"), f=None, fokus=None, lens=None)
    t = lambda sub, nm: P.baca_tag(os.path.join(sub, nm))
    ra = lambda s: [t(rr, f"{s}/own/a{i}.jpg") for i in range(3)]
    rb = lambda s: [t(rs, f"{s}/own/b{i}.jpg") for i in range(3)]
    h1, h2, h3, h4 = (P.ringkas(ra(s), rb(s)) for s in ("S01", "S02", "S03", "S04"))
    cek("S01 semua sama: lensa sama dan ukuran tumpang tindih", h1["lensa_sama"] is True and h1["ukuran_tumpang_tindih"] is True, h1)
    cek("S02 panjang fokus beda: lensa tidak sama", h2["lensa_sama"] is False, h2)
    cek("S03 ukuran tidak tumpang tindih: syarat 2 gagal, lensa tetap sama", h3["ukuran_tumpang_tindih"] is False and h3["lensa_sama"] is True, h3)
    cek("S04 EXIF lensa hilang: lensa sama = None (tidak dapat dinilai)", h4["lensa_sama"] is None, h4)
    cek("arah kamera dari nama lensa (depan vs belakang)", h1["arah_serangan"] == {"depan": 3} and h2["arah_serangan"] == {"belakang": 3} and h4["arah_serangan"] == {"tidak_diketahui": 3})
    # orientasi: 40x30 dengan orientasi 6 -> ukuran efektif 30x40
    buat(os.path.join(tmp, "o.jpg"), ukuran=(40, 30), ori=6)
    cek("orientasi 6 menukar ukuran efektif", P.baca_tag(os.path.join(tmp, "o.jpg"))["ukuran"] == (30, 40))
    # vonis gabungan
    cek("vonis: semua True = LULUS; ada False = GAGAL; ada None = TIDAK DAPAT DINILAI",
        P.vonis([True, True]) == "LULUS" and P.vonis([True, False]) == "GAGAL" and P.vonis([True, None]) == "TIDAK DAPAT DINILAI")
    cek("vonis: kegagalan pasti (False) tidak tertutup oleh relawan yang tidak dapat dinilai (None)", P.vonis([False, None]) == "GAGAL" and P.vonis([True, None]) == "TIDAK DAPAT DINILAI")
    # berkas tidak terbaca
    open(os.path.join(tmp, "rusak.jpg"), "wb").write(b"bukan gambar")
    cek("berkas rusak: baca_tag None, dihitung tidak terbaca", P.baca_tag(os.path.join(tmp, "rusak.jpg")) is None
        and P.ringkas([None, t(rr, "S01/own/a0.jpg")], rb("S01"))["tidak_terbaca"]["real"] == 1)
    # tidak mengubah berkas
    a, b = sha(rr), sha(rs)
    for s in ("S01", "S02"):
        P.ringkas(ra(s), rb(s))
    cek("pemeriksaan tidak mengubah berkas", a == sha(rr) and b == sha(rs))
    # keluaran: hanya agregat, tanpa nama lensa/merek/model/nama berkas
    simpan = json.dumps({k: v for k, v in h1.items() if not k.startswith("_")})
    cek("ringkasan tidak memuat nama lensa atau nama berkas", "front camera" not in simpan and ".jpg" not in simpan, simpan)

n = sum(HASIL)
print(f"\n{n}/{len(HASIL)} lolos")
sys.exit(0 if n == len(HASIL) else 1)
