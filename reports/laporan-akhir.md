# Laporan Akhir: Penelitian Komparatif Liveness Detection dan Face Recognition untuk Absensi HRMS Mobile

Versi 1.0 (draf untuk ditinjau peneliti), 9 November 2026. Salinan uji `D:\dev\model-research-face-cc`.
Sumber angka: `results/liveness/metrik_{640,1280,penuh}.json`, `results/recognition/metrik_{640,1280,penuh}.json`,
`logs/experiment-log.md`. Penanda: [V] terverifikasi, [S] klaim sumber/sekunder, [T] belum terverifikasi.
Semua angka di bawah adalah **hasil eksperimen kita sendiri** pada 4 relawan, kecuali disebut lain.

## 1. Ringkasan untuk pengambil keputusan

| Peran | Pilihan | Status produksi |
|---|---|---|
| Liveness | **MiniFASNet V2 + V1SE** (terbaik relatif, satu-satunya yang lulus audit lisensi) | **BELUM LAYAK apa adanya.** Dengan aturan bawaan, 33-43% foto cetak lolos. Hanya dengan threshold yang dikalibrasi, kinerjanya mendekati berguna (ACER 8,1% pada 1280), dan itu pun belum cukup bukti. |
| Face recognition | **AuraFace-v1** (lisensi lulus audit; pemisahan sempurna, AUC 1,0) | **LAYAK BERSYARAT.** Kalibrasi threshold perlu data lebih banyak, enrollment harus sesi terpisah, dan detektor produksi harus diuji. |
| Detektor wajah | YuNet hanya untuk eksperimen; **BlazeFace** kandidat produksi | **BELUM ADA.** Data latih YuNet nonkomersial [S]; BlazeFace berlisensi Apache-2.0 [V] tetapi belum diuji dan titik wajahnya tidak cocok dengan alignment AuraFace. |

Kesimpulan jujur: **pipeline absensi wajah yang siap produksi belum ada.** Komponen pengenalan (AuraFace)
menjanjikan. Komponen liveness adalah titik lemah utama. Detektor produksi masih harus dipilih dan diuji.
Rekomendasinya adalah melanjutkan ke **tahap pilot terbatas**, bukan rilis produksi (lihat bagian 7).

## 2. Apa yang diuji

- Data: 4 relawan (S01-S04) dengan ponsel masing-masing, kamera depan, satu sesi pada hari yang sama. Liveness:
  160 foto (real 80, print 40, screen 40). Pengenalan: enrollment 5 per relawan, 62 probe, 186 pasangan impostor.
  Replay video, topeng 3D, dan injeksi kamera virtual **tidak diuji**.
- Protokol: `protokol-evaluasi-v1.0.md` (dibekukan) dengan amandemen 1-5:
  1. replay tidak dikumpulkan;
  2. potong tengah 3:4;
  3. foto enrollment yang identik dengan probe dikeluarkan;
  4. threshold EER pada lipatan latih, dan gagal deteksi dihitung ditolak;
  5. koreksi crop anti-spoof-mn3.
- Leave-one-subject-out: threshold dihitung dari 3 relawan lalu diuji pada relawan keempat. Ini meniru "pengguna baru dengan ponsel baru".
- Tiga skenario resolusi (sisi terpanjang): 640, 1280, penuh. Detektor YuNet 2023mar dipakai bersama oleh semua model.
- Semua run: 160/160 foto liveness dan 82/82 foto pengenalan diproses tanpa gagal deteksi.

## 3. Hasil liveness

### 3.1 Aturan keputusan bawaan tiap model (hasil utama protokol)

BPCER = foto asli yang ditolak (dari 80). APCER = serangan yang lolos (dari 40 per jenis). ACER = (APCER terburuk + BPCER)/2.

| Model | Skenario | BPCER | APCER print | APCER screen | ACER | AUC |
|---|---|---|---|---|---|---|
| MiniFASNet | 640 | 0/80 | 17/40 (42,5%) | 8/40 | 21,2% | 0,991 |
| | 1280 | 0/80 [0-4,5%] | 16/40 (40,0% [24,9-56,7]) | 7/40 | 20,0% | 0,995 |
| | penuh | 0/80 | 13/40 (32,5%) | 8/40 | 16,2% | 0,992 |
| face-antispoof-onnx | 640 | 3/80 | 16/40 | 16/40 | 21,9% | 0,875 |
| | 1280 | 4/80 | 17/40 | 14/40 | 23,8% | 0,878 |
| | penuh | 1/80 | 20/40 | 14/40 | 25,6% | 0,880 |
| anti-spoof-mn3 | 640 | 44/80 | 0/40 | 5/40 | 33,8% | 0,867 |
| | 1280 | 45/80 (56,2%) | 0/40 | 7/40 | 36,9% | 0,835 |
| | penuh | 44/80 | 0/40 | 6/40 | 35,0% | 0,829 |

### 3.2 Threshold EER dari relawan latih (analisis tambahan, amandemen 4)

| Model | 640 ACER | 1280 ACER (BPCER; print; screen) | penuh ACER |
|---|---|---|---|
| MiniFASNet | 13,1% | **8,1%** (7/80; 3/40 = 7,5% [1,6-20,4]; 0/40) | 7,5% |
| face-antispoof-onnx | 28,7% | 28,1% | 26,9% |
| anti-spoof-mn3 | 37,5% | 42,5% | 43,8% |

### 3.3 Cara membaca

- **MiniFASNet unggul di semua skenario.** Skornya memisahkan asli dan serangan dengan baik (AUC 0,99), tetapi
  aturan bawaannya terlalu longgar: tidak ada foto asli yang ditolak, sementara 13-17 dari 40 foto cetak lolos.
  Dengan threshold yang dikalibrasi, kesalahan turun ke sekitar 3/40 foto cetak lolos dan 7/80 foto asli ditolak (1280).
  Threshold per lipatan cukup stabil, yaitu p(real) 0,82-0,93.
- Perbedaan MiniFASNet dengan mn3 bermakna: McNemar p ≤ 0,007 di ketiga skenario. Dengan face-antispoof-onnx
  belum konsisten bermakna (p 0,024-0,121).
- **anti-spoof-mn3 menolak semua foto asli S02 dan S04** (20/20 masing-masing), jadi tidak dapat dipakai pada
  kamera relawan ini. Penyebabnya [T], dugaan terkuat adalah pergeseran domain. Lisensinya juga tertahan karena dilatih pada CelebA-Spoof yang nonkomersial.
- **face-antispoof-onnx** meloloskan semua serangan S01 (10/10 print, 10/10 screen pada 1280). Kinerjanya tidak
  stabil antarrelawan.
- Resolusi lebih tinggi membantu MiniFASNet (640 terburuk), tetapi selisih 1280 dan penuh kecil.
- Per cahaya (MiniFASNet, 1280): foto cetak lolos 10/20 pada cahaya terang dan 6/20 pada cahaya redup. Selang kepercayaannya tumpang tindih.

## 4. Hasil pengenalan wajah (verifikasi 1:1, threshold EER dari relawan latih)

FRR = orang yang benar ditolak (dari 62). FAR = orang lain diterima (dari 186). Kurung siku = selang kepercayaan 95% Clopper-Pearson.

| Model | Skenario | FRR | FAR | AUC | Median skor genuine / impostor |
|---|---|---|---|---|---|
| AuraFace | 640 | 1/62 | **0/186 [0-2,0%]** | 1,000 | |
| | 1280 | 1/62 [0-8,7%] | 2/186 (1,1% [0,1-3,8]) | 1,000 | 0,90 / 0,30 |
| | penuh | 1/62 | 15/186 (8,1% [4,6-13,0]) | 1,000 | |
| buffalo_l | semua | 0/62 | 0/186 | 1,000 | 0,90 / 0,12 |
| SFace | 640 / 1280 / penuh | 1/62 | 7 / 8 / 16 dari 186 | 0,999-1,000 | 0,92 / 0,31 |

- **buffalo_l paling bersih**, tetapi bobotnya berlisensi **riset saja** sehingga tidak boleh dipakai komersial tanpa lisensi dari InsightFace.
- **AuraFace** memisahkan genuine dan impostor dengan sempurna (AUC 1,0). Kenaikan FAR pada skenario penuh (15/186) disebabkan
  aturan threshold, bukan model. Data latih tiap lipatan terpisah sempurna, sehingga threshold EER jatuh di tengah celah
  (0,425-0,59), dan sebagian impostor relawan uji (S02, S03) masuk ke celah itu. Implikasi untuk produksi: threshold
  AuraFace harus dipilih untuk FAR rendah, tidak memakai EER, dan dikalibrasi pada data yang lebih banyak.
- SFace lebih lemah daripada AuraFace di semua skenario, dan lisensinya tertahan.
- Bias optimistis: enrollment dan probe diambil di sesi yang sama dan hanya ada 4 identitas. FAR di bawah sekitar 1,6% (3/186) tidak
  dapat dibuktikan dari data ini.

## 5. Latensi dan sumber daya (awal)

Angka dari laptop pengembangan (i7-11800H, CPU, 1 thread, gambar uji face.jpg 500x750; 5 November 2026, sebelum
amandemen 2 dan 5). Antar-sesi angkanya bergeser 35-60%, jadi hanya urutan besarnya yang dapat dipakai:

- YuNet sekitar 22 ms; ansambel MiniFASNet sekitar 11 ms; face-antispoof-onnx sekitar 5 ms; anti-spoof-mn3 sekitar 3 ms.
- Latensi model pengenalan **belum diukur** [T]. Ukuran bobot: AuraFace 261 MB, buffalo_l 174 MB, SFace 39 MB,
  MiniFASNet 2 x 1,8 MB.
- Kesimpulan [T]: biaya komputasi liveness kecil. Biaya terbesar per permintaan kemungkinan ada di AuraFace
  (ResNet-100) dan dekode/resize foto besar. Perlu benchmark di server target.

## 6. Status lisensi (ringkas; rinci di `audit/model-audit-v3.md`)

| Komponen | Kode | Bobot | Data latih | Status |
|---|---|---|---|---|
| MiniFASNet | Apache-2.0 [V] | Apache-2.0 (repo) [V] | Tidak dijelaskan [V: tidak ada] | Lulus audit awal |
| face-antispoof-onnx | Apache-2.0 [V] | Di repo; lisensi bobot mengikuti repo [T] | Tidak dinyatakan; kemungkinan CelebA-Spoof [T] | Tertahan sementara |
| anti-spoof-mn3 | MIT [V] | MIT [V] | CelebA-Spoof, nonkomersial [V] | Tertahan |
| AuraFace-v1 | Apache-2.0 [V] | Apache-2.0 [V] | Data komersial/publik menurut model card [V]; cakupan etnis terbatas [V] | Lulus audit awal |
| buffalo_l | | Model zoo: riset nonkomersial saja [V] | | Riset saja |
| SFace | Apache-2.0 [V] | Apache-2.0 [V] | Tidak disebut [V: tidak ada] | Tertahan |
| YuNet | MIT [V] | MIT | WIDER Face, CC BY-NC-ND 4.0 [S] | Tertahan untuk produksi |
| BlazeFace short-range | Apache-2.0 | Apache-2.0 [V, model card] | Foto berpersetujuan milik Google [V klaim] | Kandidat; model card menyatakan "identity recognition" di luar cakupan (tafsir hukum [T]) |

Lisensi kode tidak otomatis mencakup bobot dan data latih. Kelayakan akhir perlu ditinjau pihak hukum.

## 7. Rekomendasi

### 7.1 Keputusan model
1. **Liveness: MiniFASNet**, dengan status *kandidat terpilih untuk pilot*, bukan produksi. Syaratnya:
   - aturan bawaan **tidak boleh** dipakai; threshold dikalibrasi pada data pilot;
   - data pilot berisi lebih banyak relawan dan ponsel, termasuk serangan replay video;
   - liveness pasif ini tidak dijadikan satu-satunya pertahanan (lihat 7.3).
2. **Pengenalan: AuraFace-v1.** Threshold dipilih untuk FAR rendah dan dikalibrasi ulang pada data pilot, dengan
   enrollment dari sesi yang berbeda dari probe.
3. **Detektor: BlazeFace** sebagai kandidat yang harus diuji. Alignment 5 titik untuk AuraFace perlu sumber landmark
   lain (mis. FaceMesh, yang lisensinya harus diperiksa [T]) atau evaluasi ulang. Sampai diuji, belum ada detektor produksi.
4. Model lain tidak direkomendasikan: buffalo_l (lisensi), SFace (lebih lemah dan lisensi tertahan), anti-spoof-mn3
   (menolak semua foto asli dua relawan, lisensi tertahan), face-antispoof-onnx (tidak stabil, data latih tidak jelas).

### 7.2 Format foto dari aplikasi
- Kamera depan, potong ke 3:4, JPEG, **sisi terpanjang 1280 px**. Pada skenario ini MiniFASNet hampir sebaik resolusi
  penuh, sementara FAR AuraFace jauh lebih rendah daripada pada resolusi penuh. Ukuran unggahan juga jauh lebih kecil.
  Ini hasil dari 4 relawan dan perlu dikonfirmasi di pilot.

### 7.3 Pertahanan berlapis (karena liveness pasif terbatas)
- Liveness pasif berbasis satu foto tidak melindungi dari injeksi kamera virtual, emulator, atau topeng 3D.
- Lapisan tambahan yang disarankan, berupa desain dan belum diuji:
  - atestasi perangkat dan aplikasi (Play Integrity / App Attest);
  - pengambilan dari kamera di dalam aplikasi, bukan dari galeri;
  - tantangan aktif sederhana, misalnya beberapa frame dengan gerakan kepala;
  - pembatasan lokasi/jaringan kantor;
  - pemeriksaan manual atas kasus yang ditolak.

## 8. Analisis kelayakan integrasi Frappe (desain saja, tidak diimplementasikan)

### 8.1 Alur yang diusulkan
1. Aplikasi mobile mengambil foto dari kamera depan, memotongnya ke 3:4, mengubahnya ke 1280 px, lalu mengirimnya lewat
   HTTPS ke endpoint Frappe (`@frappe.whitelist()`), disertai token sesi karyawan.
2. Frappe meneruskan foto ke **layanan inferensi terpisah** (proses Python dengan onnxruntime, di jaringan internal).
   Layanan itu menjalankan deteksi → liveness → embedding AuraFace, lalu membandingkan hasilnya dengan templat karyawan.
3. Layanan mengembalikan keputusan dan skor. Frappe mencatat `Employee Checkin` hanya bila liveness dan
   verifikasi keduanya lolos. Kasus yang ditolak masuk antrean tinjauan manual.

### 8.2 Alasan layanan terpisah, bukan di dalam worker Frappe
- Bobot AuraFace sekitar 261 MB. Jika dimuat di tiap worker gunicorn, memori berlipat sesuai jumlah worker, dan proses
  pemuatannya lambat.
- MiniFASNet memakai PyTorch, dependensi besar yang tidak cocok di lingkungan bench Frappe. Ekspor ke ONNX
  mungkin bisa dilakukan, tetapi kesetaraan hasilnya harus diuji [T].
- Versi pustaka penglihatan komputer dan model dapat diperbarui terpisah dari Frappe.

### 8.3 Data dan privasi
- Templat wajah (embedding 512-d) adalah **data biometrik**, yang dalam UU PDP (UU 27/2022) termasuk data pribadi
  spesifik [T: konfirmasi hukum]. Kebutuhannya:
  - persetujuan eksplisit karyawan;
  - DPIA (penilaian dampak pelindungan data);
  - enkripsi saat disimpan;
  - akses dibatasi peran;
  - log audit;
  - prosedur hapus saat karyawan keluar.
- Simpan templat di DocType tersendiri yang terpisah dari profil karyawan, dengan izin ketat. Foto absensi sebaiknya tidak
  disimpan, atau disimpan singkat dengan masa retensi jelas untuk tinjauan sengketa.
- Threshold dan versi model disimpan sebagai konfigurasi bertanggal, dan setiap keputusan mencatat versi model.

### 8.4 Risiko kelayakan
- Kinerja liveness belum memadai (bagian 3), dan ini risiko terbesar.
- Detektor produksi belum diuji.
- Latensi AuraFace di server belum diukur.
- Kamera aplikasi HRMS mungkin memproses gambar berbeda dari kamera bawaan ponsel yang dipakai di penelitian ini.

## 9. Keterbatasan
- 4 relawan, 4 ponsel, 1 sesi. Hasil adalah perbandingan relatif, bukan akurasi populasi; tidak ada analisis demografis.
  Selang kepercayaan lebar dan optimistis, karena foto dari relawan yang sama saling berkorelasi.
- Serangan hanya foto cetak dan foto di layar; replay, topeng, dan injeksi tidak diuji.
- Ukuran dan EXIF foto asli berbeda dari foto serangan pada keempat relawan, sehingga ada kemungkinan model membedakan
  keduanya dari faktor itu (confound [T]). Pemotongan 3:4 hanya mengurangi sebagian.
- Enrollment dari sesi yang sama dengan probe, dan sebagian redup; 18 foto duplikat dikeluarkan dari probe.
- Model ponsel, OS, dan pengaturan kamera tidak dicatat (penanda di manifest).
- Latensi dari laptop pengembangan dan pengukuran awal.
- Model card AuraFace menyatakan cakupan etnis data latih terbatas [V]; kinerja pada populasi karyawan sebenarnya belum diketahui.
- Detektor eksperimen (YuNet) berbeda dari kandidat detektor produksi (BlazeFace), jadi hasil bisa berubah saat detektor diganti.

## 10. Langkah lanjutan yang disarankan
1. Uji BlazeFace dan sumber landmark untuk alignment pada data yang ada, lalu bandingkan hasil AuraFace dan MiniFASNet dengan hasil YuNet.
2. Benchmark latensi AuraFace dan pipeline lengkap di CPU.
3. Pilot data baru dengan protokol baru yang dibekukan sebelum pengambilan:
   - lebih banyak relawan dan ponsel;
   - enrollment dari sesi berbeda;
   - serangan replay;
   - foto dari kamera aplikasi HRMS sendiri.
4. Tinjauan hukum: lisensi bobot dan data latih (MiniFASNet, AuraFace, BlazeFace), pernyataan cakupan BlazeFace, serta UU PDP.

## 11. Reproduksibilitas
Kode, konfigurasi, hash bobot, versi pustaka, skor mentah per foto (CSV), dan metadata tiap run tercatat di repo
(lihat `logs/experiment-log.md`, `logs/checksums-*.txt`, `configs/requirements-stage4.txt`). Embedding
(`results/recognition/*.npz`) dan data relawan sengaja tidak masuk Git karena termasuk data biometrik.
