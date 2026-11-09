"""Analisis celah skor pengenalan wajah per skenario resolusi (tindak lanjut laporan-akhir bagian 4).

Tujuan: memisahkan dua penyebab FAR AuraFace 15/186 pada resolusi penuh: (1) aturan threshold EER pada data latih
yang terpisah sempurna, atau (2) celah antara skor genuine dan impostor yang memang menyempit pada resolusi tinggi.
Hanya membaca embedding (.npz) dan manifest.csv yang SUDAH ada; tidak menjalankan model, tidak membuka gambar.
Keluaran hanya angka agregat (min/maks skor, jumlah, posisi threshold); tidak ada vektor embedding yang dicetak.

Perintah (dari akar proyek, venv aktif):
  python scripts/analisis_celah.py --emb results/recognition/emb_640.npz results/recognition/emb_1280.npz \
      results/recognition/emb_penuh.npz --out results/recognition/analisis_celah.json
"""
import argparse
import json
import math
import os
import sys

import numpy as np

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import evaluasi as EV  # noqa: E402  (memakai pembentukan pasangan dan threshold yang sama dengan evaluasi utama)


def pairs_dari_npz(path, manifest=None):
    """Bentuk pasangan per model dengan aturan yang sama seperti evaluasi.recognition_from_npz."""
    z = np.load(path, allow_pickle=False)
    meta = json.loads(str(z["meta"]))
    man = {m["sample_id"]: m for m in EV.read_csv(manifest or EV.MANIFEST)}
    hasil = {}
    for nm in meta["models"]:
        E = z[nm]
        emb_probe, emb_enroll, probes = {}, {}, []
        for i, (jenis, sid, subj) in enumerate(zip(meta["jenis"], meta["id"], meta["subject"])):
            v = None if np.isnan(E[i]).any() else E[i]
            if jenis == "probe":
                probes.append({"sample_id": sid, "subject": subj, "lighting": man[sid]["lighting"]})
                emb_probe[sid] = v
            else:
                emb_enroll.setdefault(subj, [])
                if v is not None:
                    emb_enroll[subj].append(v)
        pairs, _ = EV.recognition_pairs(probes, emb_probe, emb_enroll)
        hasil[nm] = pairs
    return hasil


def _min_maks(pairs):
    g = [p["score"] for p in pairs if p["genuine"] and not p["gagal"]]
    im = [p["score"] for p in pairs if (not p["genuine"]) and not p["gagal"]]
    return (min(g) if g else None), (max(im) if im else None), len(g), len(im)


def ringkas_celah(pairs):
    """Ringkasan celah (hanya angka agregat) dari daftar pasangan hasil evaluasi.recognition_pairs."""
    min_g, max_i, ng, ni = _min_maks(pairs)
    sc_i = [p["score"] for p in pairs if (not p["genuine"]) and not p["gagal"]]
    sc_g = [p["score"] for p in pairs if p["genuine"] and not p["gagal"]]
    gabungan = {
        "skor_genuine_min": min_g, "skor_impostor_maks": max_i,
        "celah_gabungan": None if min_g is None or max_i is None else min_g - max_i,
        "impostor_di_atas_genuine_min": sum(1 for s in sc_i if s >= min_g),
        "genuine_di_bawah_impostor_maks": sum(1 for s in sc_g if s <= max_i),
        "n_genuine": ng, "n_impostor": ni,
    }
    ev = EV.recognition_eval(pairs)
    lipatan = {}
    for s in sorted({p["probe_subject"] for p in pairs}):
        latih = [p for p in pairs if p["probe_subject"] != s and p["claim"] != s and not p["gagal"]]
        uji = [p for p in pairs if p["probe_subject"] == s]
        gl, il, _, _ = _min_maks(latih)
        gu, iu, _, _ = _min_maks(uji)
        thr = ev["lipatan"][s]["threshold"]
        celah_latih = gl - il
        posisi = (thr - il) / celah_latih if celah_latih > 0 else None
        lipatan[s] = {
            "threshold": thr, "latih_genuine_min": gl, "latih_impostor_maks": il, "celah_latih": celah_latih,
            "posisi_threshold_di_celah_latih": posisi,  # 0 = tepi bawah (impostor maks), 1 = tepi atas (genuine min)
            "uji_genuine_min": gu, "uji_impostor_maks": iu,
            "uji_impostor_di_atas_threshold": sum(1 for p in uji if (not p["genuine"]) and not p["gagal"] and p["score"] >= thr),
            "uji_genuine_di_bawah_threshold": sum(1 for p in uji if p["genuine"] and (p["gagal"] or p["score"] < thr)),
        }
    return {"gabungan": gabungan, "lipatan": lipatan}


def _fmt(x, d=3):
    return "-" if x is None else f"{x:.{d}f}"


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--emb", nargs="+", required=True)
    ap.add_argument("--out", required=True)
    ap.add_argument("--manifest", default=None)
    a = ap.parse_args()
    keluaran = {}
    for path in a.emb:
        nama = os.path.splitext(os.path.basename(path))[0].replace("emb_", "")
        keluaran[nama] = {nm: ringkas_celah(pairs) for nm, pairs in pairs_dari_npz(path, a.manifest).items()}
    os.makedirs(os.path.dirname(os.path.abspath(a.out)), exist_ok=True)
    with open(a.out, "w", encoding="utf-8") as f:
        json.dump(keluaran, f, indent=1, ensure_ascii=False)
    print("== Celah gabungan (genuine min - impostor maks; positif = ada ambang tanpa kesalahan)")
    print("skenario  model       gen_min  imp_maks  celah   imp>=gen_min  gen<=imp_maks")
    for sk, d in keluaran.items():
        for nm, r in d.items():
            g = r["gabungan"]
            print(f"{sk:8s}  {nm:10s}  {_fmt(g['skor_genuine_min'])}   {_fmt(g['skor_impostor_maks'])}    {_fmt(g['celah_gabungan'])}  "
                  f"{g['impostor_di_atas_genuine_min']:>6d}        {g['genuine_di_bawah_impostor_maks']:>6d}")
    print("\n== Per lipatan (threshold vs celah data latih; posisi 0 = tepi bawah, 1 = tepi atas)")
    print("skenario  model       lipatan  thr     celah_latih  posisi  uji_imp_maks  FA  FR")
    for sk, d in keluaran.items():
        for nm, r in d.items():
            for s, l in r["lipatan"].items():
                print(f"{sk:8s}  {nm:10s}  {s:6s}  {_fmt(l['threshold'])}  {_fmt(l['celah_latih']):>9s}  "
                      f"{_fmt(l['posisi_threshold_di_celah_latih'], 2):>6s}  {_fmt(l['uji_impostor_maks']):>10s}  "
                      f"{l['uji_impostor_di_atas_threshold']:>3d} {l['uji_genuine_di_bawah_threshold']:>3d}")
    print(f"\nTersimpan: {a.out}")


if __name__ == "__main__":
    main()
