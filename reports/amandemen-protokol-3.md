# Amandemen 3 untuk Protokol Evaluasi v1.0 (8 November 2026)

Melengkapi v1.0 dan amandemen 1-2; isinya tidak diubah. Diputuskan peneliti SEBELUM model pengenalan wajah
dijalankan pada foto relawan (belum ada skor yang dilihat).

## 1. Enrollment dipakai apa adanya; foto identik dikeluarkan dari probe (keputusan "B", final)

Fakta (`scripts/periksa_data.py`, hash SHA-256; lihat log 2026-11-08):
- 18 dari 20 foto enrollment identik dengan foto real di raw (S01 5/5, S02 5/5, S03 5/5, S04 3/5), pemetaan 1:1.
- 7 dari 18 foto itu berasal dari kondisi redup; enrollment dan probe berasal dari sesi yang sama.

Penyimpangan dari protokol v1.0 bagian 5 (enrollment "frontal, terang, sesi berbeda dari probe"): enrollment tidak
diambil ulang. Alasan peneliti: foto ini berperan sebagai foto pendaftaran, sehingga dianggap dapat diterima.

Aturan:
1. Enrollment = 5 foto per relawan di `datasets/recognition/internal/enrollment/` apa adanya (termasuk yang redup).
2. Probe = foto kelas real yang TIDAK tercantum di `duplikat_enrollment.csv` (pencocokan hash SHA-256 persis).
   Hasil: 62 probe (S01 15, S02 15, S03 15, S04 17; terang 29, redup 33).
3. Pasangan genuine: tiap probe vs enrollment relawannya sendiri (62). Pasangan impostor: tiap probe vs enrollment
   3 relawan lain (186). Batas atas FAR tanpa kesalahan (aturan 3/N) sekitar 1,6%; FAR di bawahnya tidak dapat dibuktikan.
4. Foto enrollment tidak dipakai untuk menentukan threshold liveness; pemotongan 3:4 (amandemen 2) berlaku juga untuk enrollment.

## 2. Keterbatasan yang wajib dilaporkan

- Enrollment dan probe dari sesi yang sama: FRR dan kemiripan genuine kemungkinan lebih baik daripada pemakaian nyata
  (absensi berhari-hari setelah pendaftaran, pakaian/rambut/cahaya berbeda). Bias optimistis, arah diketahui, besar [T].
- Pencocokan hash hanya menangkap salinan persis; foto yang hampir identik (mis. jepretan beruntun) tetap dapat
  menjadi probe [T].
- Enrollment campuran terang/redup berbeda dari rancangan; hasil per cahaya ditafsirkan dengan hati-hati.
