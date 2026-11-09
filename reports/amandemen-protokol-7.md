# Amandemen 7 untuk Protokol Evaluasi v1.0 (DRAF, 9 November 2026)

STATUS: DRAF, belum dibekukan. Harus dibekukan (commit bertanda "dibekukan") SEBELUM pengambilan foto dimulai.
Melengkapi v1.0 dan amandemen 1-6; isinya tidak diubah. Menindaklanjuti amandemen 6.

PENTING (transparansi): kriteria pemilihan model pada bagian 6 ditulis SETELAH hasil liveness lama terlihat. Angkanya dipilih
dari logika ukuran sampel dan penyaringan dasar, bukan untuk memenangkan model tertentu; satu syarat (BPCER per relawan) terinspirasi
kegagalan total anti-spoof-mn3 pada hasil lama. Kriteria dibekukan SEBELUM foto baru diambil, sehingga hasil baru dinilai dengan aturan
yang sudah tetap. Angka pada bagian 6 dapat disesuaikan HANYA selama STATUS masih DRAF.

## 1. Tujuan

Mengambil ulang foto serangan liveness dengan KAMERA DEPAN agar foto asli dan foto serangan berasal dari kamera yang
sama, lalu mengevaluasi ulang liveness. Hasil liveness lama (serangan kamera belakang) tidak dipakai memilih model
(amandemen 6) dan tetap disimpan sebagai catatan.

## 2. Lingkup

- Yang diulang: foto serangan saja. Per relawan: print 10 dan screen 10. Total 80 foto.
- Yang TIDAK diulang: foto asli liveness (80) dan enrollment; dipakai apa adanya untuk evaluasi utama.
- Tambahan KONTROL SESI: 5 foto asli baru per relawan (total 20), hanya untuk memeriksa apakah pergantian sesi saja menggeser skor foto asli (bagian 3 dan 5).
- Total pengambilan baru: 80 foto serangan + 20 foto asli kontrol = 100 foto.
- Replay video, topeng 3D, dan injeksi kamera virtual tetap tidak dikumpulkan dan tidak diuji (amandemen 1). Dicatat sebagai keterbatasan.
- Relawan dan ponsel sama dengan pengambilan foto asli (S01-S04, ponsel masing-masing).

## 3. Aturan pengambilan

- Kamera DEPAN ponsel relawan memotret hasil presentasi serangan (kertas cetak atau layar). Kamera belakang tidak dipakai untuk memotret presentasi serangan.
- Materi sumber serangan (foto potret relawan) boleh diambil dengan kamera berkualitas baik (protokol v1.0 bagian 3).
- Rasio foto 3:4, format JPEG (iPhone: Pengaturan > Kamera > Format > Paling Kompatibel).
- Print: A4 kertas biasa, ukuran wajah mendekati asli; 5 pencahayaan terang dan 5 redup (protokol v1.0 bagian 4).
- Screen: layar laptop; kecerahan layar dibuat tetap dan dicatat; pencahayaan dicatat per foto.
- Pencahayaan diatur fisik; foto tidak boleh diedit (protokol v1.0 bagian 11). Pengaturan cermin kamera depan dicatat apa adanya; pengaturan saat foto asli tidak tercatat di manifest, sehingga kesamaannya tidak dapat diverifikasi (dilaporkan sebagai keterbatasan).
- Jarak sekitar sepanjang lengan, frontal. Tanpa blitz, tanpa mode kecantikan atau HDR agresif bila dapat dimatikan.
- Matikan sinkronisasi cloud galeri dan penandaan lokasi; pindahkan foto lewat kabel; hapus dari ponsel termasuk tempat sampah galeri.
- Foto baru disimpan di folder terpisah dari foto serangan lama; foto lama tidak dihapus atau ditimpa.
- Kontrol sesi: 5 foto asli baru per relawan (kamera depan, wajah asli, bukan serangan) diambil pada sesi dan kondisi yang sama dengan foto serangan baru, campuran terang dan redup seperti foto asli lama; jumlah per pencahayaan dicatat. Foto ini TIDAK masuk evaluasi utama.
- Model ponsel dan OS dicatat di manifest (kolom device_model dan os; manifest berada di datasets/ yang tidak ikut Git).
- Persetujuan relawan dipastikan masih berlaku sebelum pengambilan.

## 4. Pemeriksaan sebelum evaluasi (syarat lolos)

Hanya header EXIF yang dibaca (orientasi, merek, model, software, lensa, bukaan, panjang fokus); GPS, tanggal, nomor seri,
dan piksel tidak dibaca. Per relawan:
1. foto serangan baru dan foto asli memakai lensa yang sama (bukaan dan panjang fokus sama);
2. himpunan ukuran asli foto serangan baru dan foto asli tumpang tindih;
3. foto asli kontrol baru dan foto asli lama memakai lensa yang sama (bukaan dan panjang fokus sama).
Bila salah satu syarat gagal pada seorang relawan, hal itu dilaporkan dan diputuskan sebelum evaluasi dilanjutkan; hasil liveness
tidak dipakai memilih model sampai syarat terpenuhi.

## 5. Evaluasi

- Pipeline, aturan keputusan bawaan, threshold EER lipatan latih, perlakuan gagal deteksi, dan tiga skenario resolusi (640, 1280, penuh) sama dengan amandemen 1-5. Tidak ada aturan yang diubah setelah melihat hasil.
- Foto asli lama (kamera depan) dipasangkan dengan foto serangan baru (kamera depan). Foto serangan lama tidak ikut.
- Hasil baru ditulis ke berkas terpisah dari hasil lama; hasil lama diberi label "v1 (serangan kamera belakang)" dan tidak digabung.
- Jumlah gagal deteksi dilaporkan per model, relawan, kelas, cahaya, dan skenario.
- Pemilihan model mengikuti kriteria bagian 6, yang dihitung hanya dari foto asli lama dan foto serangan baru.
- Hasil kontrol sesi dilaporkan terpisah: skor foto asli baru dibandingkan dengan foto asli lama pada relawan dan model yang sama (selisih median skor dan jumlah ditolak). Hasil ini tidak mengubah aturan pemilihan; bila ada pergeseran yang jelas, dicatat sebagai keterbatasan [T].

## 6. Kriteria pemilihan model liveness (tahap 1)

Tujuan: memilih SATU model liveness terbaik dari tiga kandidat (MiniFASNet, face-antispoof-onnx, anti-spoof-mn3) berdasarkan bukti.
Ini melengkapi PRD tujuan T2 ("memilih ... berdasarkan bukti, atau menyatakan belum ada yang layak"), yang belum punya aturan angka.
Ini BUKAN ambang kelayakan produksi (lihat bagian 8).

Dasar perhitungan: foto asli lama (80, kamera depan) + foto serangan baru (80: print 40, screen 40); skenario resolusi 1280
(skenario utama sementara, amandemen 1); threshold EER per lipatan latih leave-one-subject-out (analisis tambahan, amandemen 4 bagian 2);
ACER = (APCER terburuk dari print dan screen + BPCER) / 2; gagal deteksi dihitung ditolak (amandemen 4 bagian 3).

Aturan:
1. Syarat ikut peringkat (keduanya harus terpenuhi): ACER <= 25%, DAN BPCER pada tiap relawan <= 50%.
2. Pemenang: model yang memenuhi syarat dengan ACER terendah.
3. Bila selisih ACER antara dua model teratas <= 5 poin persentase, pemenang ditentukan berurutan: (a) lisensi lulus audit; (b) APCER terburuk lebih rendah; (c) latensi median lebih rendah.
4. Bila tidak ada model yang memenuhi syarat, dinyatakan "belum ada model liveness terpilih". Syarat tidak diturunkan setelah melihat hasil.
5. Hanya dilaporkan, tidak ikut menentukan: skenario 640 dan penuh, aturan keputusan bawaan (hasil utama amandemen 4), hasil per pencahayaan, jumlah gagal deteksi, dan hasil kontrol sesi.
6. Pemenang kinerja yang lisensinya tertahan atau riset saja tetap dicatat sebagai pemenang kinerja; kelayakan produksinya menunggu gerbang lisensi (PRD).

Alasan angka: ACER <= 25% hanya menyaring model yang jelas tidak berfungsi, bukan standar produksi. BPCER per relawan <= 50% menangkap
kegagalan total pada satu orang (pada hasil lama, anti-spoof-mn3 menolak seluruh foto asli dua relawan dengan aturan bawaan). Selisih 5 poin
kira-kira derau pada 40 foto per jenis serangan dan 80 foto asli; di bawah itu dua model tidak dapat dibedakan secara meyakinkan, sehingga
lisensi dan APCER yang memutuskan.

Peringkat memakai analisis tambahan EER, bukan hasil utama aturan bawaan (amandemen 4 bagian 2), karena aturan bawaan tidak dikalibrasi dan
mengukur perilaku bawaan model, bukan kemampuan memisahkan asli dari serangan. Hasil utama aturan bawaan tetap dilaporkan.

## 7. Keterbatasan yang wajib dilaporkan

- Foto serangan baru diambil pada sesi berbeda dari foto asli; perbedaan waktu, cahaya, atau pengaturan antar sesi dapat memengaruhi skor [T].
- 4 relawan dan 4 ponsel: perbandingan relatif, bukan akurasi populasi; selang kepercayaan optimistis.
- Hanya serangan cetak dan foto di layar; replay video dan serangan lain tidak diuji.
- Kamera bawaan ponsel belum tentu sama dengan kamera di dalam aplikasi HRMS.
- Kontrol sesi hanya 5 foto asli per relawan (20 total): cukup untuk melihat pergeseran besar, tidak untuk membuktikan tidak ada pergeseran [T].
- Pengaturan cermin kamera depan saat foto asli lama tidak tercatat; kesamaannya dengan foto baru tidak dapat diverifikasi.

## 8. Tahap 2: kelayakan model terpilih (bukan bagian amandemen ini)

Dirumuskan dan dibekukan di protokol pilot SEBELUM data pilot diambil. Titik awal usulan: batas atas selang kepercayaan 95% (Clopper-Pearson)
untuk APCER terburuk dan untuk BPCER masing-masing <= 10%, pada kamera depan dari aplikasi. Catatan statistik: dengan 40 foto per jenis serangan,
batas atas <= 10% hanya tercapai bila tidak ada serangan yang lolos (0/40: 8,8%; 1/40: 13,2%); untuk membuktikan <= 5% diperlukan minimal 72 foto
per jenis serangan tanpa satu pun lolos. Angka akhir ditetapkan peneliti bersama pembimbing. Kriteria pengenalan wajah juga masuk protokol pilot:
data pengenalan sudah terlihat, sehingga ambang yang ditulis sekarang bukan ambang yang dibekukan di muka.

## 9. Hubungan dengan dokumen lain

Melengkapi PRD tujuan T2 tanpa mengubahnya. Tidak mengubah protokol v1.0 maupun amandemen 1-6; hasil utama liveness menurut amandemen 4 (aturan bawaan) tetap berlaku sebagai hasil utama.
