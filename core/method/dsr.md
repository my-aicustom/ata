# Method Pack: DSR / Prototype (Design Science Research)

Lapis 3 — Method Pack. **[TAMBAHAN 1-OKT]** Seluruh file ini baru, disusun dari bahan `Arsitektur System Terdistribusi THESIS.png` (artefak arsitektur kantor pusat–cabang). Model proses mengacu Peffers dkk. (2007) [BELUM DIVERIFIKASI].

## Kapan cocok / tidak cocok
- Cocok: tesis yang menghasilkan artefak (arsitektur, prosedur, prototipe, model) untuk masalah nyata, lalu mengevaluasinya.
- Tidak cocok: tesis yang hanya mengukur hubungan antarvariabel tanpa membuat artefak.
- Sering digabung: DSR untuk membuat artefak + System Experiment Pack untuk evaluasi kinerja + Interview Pack untuk evaluasi pakar.

## 8 langkah (dipetakan ke 6 aktivitas DSR)
| Langkah | Aktivitas DSR | Isi | Gate manusia |
|---|---|---|---|
| 1. Fit | — | Method Fit Advisor (core) | Mahasiswa + pembimbing |
| 2. Design | Identifikasi masalah + tujuan solusi | Masalah, kebutuhan (fungsional & non-fungsional), kriteria keberhasilan terukur | |
| 3. Instrument | Desain & pengembangan | Artefak: diagram arsitektur, komponen, alur data, keputusan desain + alasannya (artifact-designer) | Mahasiswa |
| 4. Plan | — | Rencana evaluasi dikunci: metrik, skenario uji, pakar penilai | Masuk Bab III |
| 5. Pilot | Demonstrasi | Artefak berjalan untuk satu kasus | |
| 6. Collect & QC | Evaluasi | Uji fungsional, kinerja, dan/atau penilaian pakar | |
| 7. Analyze | Evaluasi | Skrip/rekap; LLM tidak menghitung | |
| 8. Review & Interpret | Komunikasi | Critic Board; kontribusi | Mahasiswa |

## Peran: artifact-designer

```text
PERAN: ARTIFACT DESIGNER

Tugas: bantu mahasiswa menyusun dan memeriksa desain artefak (arsitektur atau prosedur) secara sistematis.

Langkah:
1. Nyatakan masalah dan kebutuhan: fungsional dan non-fungsional (mis. ketersediaan, konsistensi data, keamanan, latensi). Setiap kebutuhan non-fungsional harus punya metrik.
2. Uraikan komponen artefak dan tanggung jawab tiap komponen.
3. Gambarkan alur data utama dan alur kegagalan (apa yang terjadi jika satu komponen atau koneksi putus).
4. Catat setiap keputusan desain dalam format: Keputusan | Alternatif | Alasan | Konsekuensi.
5. Periksa konsistensi diagram: setiap komponen terhubung dengan jelas, batas keamanan seragam, mekanisme sinkronisasi/replikasi data tergambar jika ada beberapa database, komponen pemantauan tidak berada di jalur data kecuali memang disengaja.
6. Gunakan nama generik (Main Office, Branch Office, Server A). Jangan menulis nama server, IP, atau sistem produksi nyata.

Output: A. Tabel kebutuhan + metrik. B. Tabel komponen. C. Diagram Mermaid (alur normal + alur gagal). D. Catatan keputusan desain. E. Daftar inkonsistensi diagram yang ditemukan.
```

## Kriteria G4
- Artefak berjalan di lab untuk minimal satu kasus demonstrasi
- Evaluasi dijalankan sesuai rencana terkunci; kriteria keberhasilan ditulis sebelum evaluasi
- Jika evaluasi pakar: ≥3 pakar, instrumen penilaian tertulis, hasil dicatat apa adanya

## Alat
Mermaid / draw.io (file di repo), testbed VM (bersama System Experiment Pack), formulir penilaian pakar.

## Jadwal
Ikuti jadwal System Experiment Pack; minggu 7–8 dipakai untuk desain artefak dan rencana evaluasi.

## Tes penerimaan pack
Jalankan artifact-designer pada diagram `Arsitektur System Terdistribusi THESIS.png`. Peran ini harus menemukan minimal inkonsistensi yang sudah dicatat di `instances/forensik-informatika/catatan-bahan.md` bagian A.
