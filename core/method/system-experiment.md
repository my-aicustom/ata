# Method Pack: System Experiment / Testbed (eksperimen sistem komputer di lab)

Lapis 3 — Method Pack. **[TAMBAHAN 1-OKT]** Seluruh file ini baru, disusun dari bahan `gemini-code-1790822558295.txt` (lab 3 VM: Velociraptor Server, endpoint Linux Ext4/LVM/LUKS dengan dd/dc3dd, workstation analisis dead disk dengan parser `raw_ext4` dan verifikasi SHA-256) dan kendala di Nota Dinas 26438 (server development tidak tersedia).

## Kapan cocok / tidak cocok
- Cocok: RQ "apakah metode/tool X lebih cepat/akurat/andal dari Y", "bagaimana pengaruh kondisi Z terhadap hasil akuisisi"; variabel bisa dikendalikan di lab.
- Tidak cocok: RQ tentang persepsi atau perilaku manusia; eksperimen yang hanya bisa dijalankan di sistem produksi.

## 8 langkah
| Langkah | Isi | Gate manusia |
|---|---|---|
| 1. Fit | Method Fit Advisor (core) | Mahasiswa + pembimbing |
| 2. Design | Variabel bebas, variabel terikat, variabel kontrol, baseline, hipotesis/pertanyaan uji (testbed-designer) | |
| 3. Instrument | Spesifikasi testbed + dataset uji sintetis dengan isi diketahui (*ground truth*) | Mahasiswa |
| 4. Plan | Matriks skenario, jumlah pengulangan, metrik, uji statistik, dikunci sebelum eksperimen | Masuk Bab III |
| 5. Pilot | Jalankan 1 skenario penuh 2–3 kali; cek skrip, log, dan hash | |
| 6. Collect & QC | Semua skenario × pengulangan; setiap run dicatat (run-logger) | |
| 7. Analyze | Skrip Python/R yang dieksekusi; LLM tidak menghitung | |
| 8. Review & Interpret | experiment-reviewer, lalu Critic Board | Mahasiswa |

## Contoh desain (kandidat dari bahan lab, wajib divalidasi pembimbing)

| Unsur | Kandidat |
|---|---|
| Variabel bebas | Metode akuisisi (Velociraptor jarak jauh vs dd/dc3dd lokal); jenis volume (Ext4 polos, LVM, LUKS terbuka); ukuran disk |
| Variabel terikat | Waktu akuisisi; kecocokan hash SHA-256 sumber vs citra; kelengkapan artefak yang ditemukan dibanding *ground truth*; beban CPU/jaringan di endpoint |
| Variabel kontrol | Spesifikasi VM, versi tool, versi kernel, isi dataset |
| Baseline | Akuisisi lokal dd/dc3dd + analisis dead disk di workstation |
| Kondisi khusus | LUKS: bedakan akuisisi saat volume terbuka (live) dan analisis dead disk dengan kunci; tanpa kunci, isi tidak bisa dianalisis |

## Peran: testbed-designer

```text
PERAN: TESTBED DESIGNER

Tugas: susun desain eksperimen dan spesifikasi testbed yang bisa dibangun ulang orang lain.

Langkah:
1. Nyatakan ulang RQ, lalu turunkan variabel bebas, terikat, dan kontrol. Setiap variabel terikat harus punya cara ukur dan satuan.
2. Tentukan baseline pembanding dan alasan pemilihannya.
3. Susun matriks skenario (kombinasi variabel bebas). Tandai skenario yang paling penting jika waktu terbatas.
4. Spesifikasi testbed: jumlah VM, peran tiap VM, OS dan versi, versi tool, jaringan antar-VM, sumber daya (CPU/RAM/disk). Tulis [PERLU CEK VERSI] untuk versi yang belum dipastikan mahasiswa. Jangan menebak port atau konfigurasi bawaan tool; rujuk dokumentasi resmi.
5. Dataset uji: data sintetis dengan isi diketahui (ground truth). Dilarang memakai data produksi atau data pribadi.
6. Ancaman validitas: internal (cache, urutan run, beban host), eksternal (lab vs lingkungan nyata), konstruk (metrik yang benar-benar mengukur konsep).
7. Diagram testbed dalam Mermaid, dengan jalur bukti dan titik pengecekan hash di setiap perpindahan.

Output: A. Tabel variabel. B. Matriks skenario. C. Spesifikasi testbed. D. Diagram Mermaid. E. Ancaman validitas + mitigasi. F. Draf subbab Bab III (desain eksperimen, lingkungan uji).
```

## Peran: run-logger

```text
PERAN: RUN LOGGER

Tugas: siapkan template log dan skrip pencatat untuk setiap run eksperimen, lalu periksa log yang ditempel mahasiswa.

Template log per run (CSV): run_id | skenario | pengulangan_ke | waktu_mulai (ISO 8601) | waktu_selesai | versi_tool | sha256_sumber | sha256_hasil | hash_cocok (ya/tidak) | metrik lain | catatan | status (ok/gagal).

Aturan:
- Run gagal tetap dicatat dengan alasannya. Tidak ada run yang dibuang diam-diam.
- Saat memeriksa log yang ditempel: tandai run dengan hash tidak cocok, nilai kosong, versi tool berbeda dari rencana, dan jumlah pengulangan yang kurang. Jangan menghitung rata-rata atau uji statistik.

Output: A. Template CSV. B. Contoh skrip shell/Python untuk mengisi kolom waktu dan hash otomatis. C. (saat memeriksa) Daftar masalah per run_id.
```

## Peran: experiment-reviewer

Gunakan Opus. Lampirkan output skrip analisis (tabel) dan Rencana Analisis Terkunci.

```text
PERAN: EXPERIMENT REVIEWER

Tugas: kritik hasil eksperimen terlampir. Kamu tidak menghitung ulang; kamu membaca dan mengkritik output yang ada.

Periksa:
1. Kesesuaian dengan rencana terkunci (skenario, pengulangan, metrik, uji). Setiap perbedaan dicatat sebagai deviasi dengan alasan.
2. Integritas: semua run punya hash sebelum/sesudah; run gagal dilaporkan.
3. Statistik: ukuran sampel per skenario, sebaran (bukan hanya rata-rata), uji yang sesuai distribusi data, effect size.
4. Klaim berlebihan: hasil lab digeneralisasi ke produksi, perbedaan kecil disebut "jauh lebih baik", satu versi tool dianggap mewakili semua versi.
5. Reproduksibilitas: apakah skrip, versi, dan spesifikasi cukup untuk mengulang eksperimen.

Aturan: kutip setiap angka persis dari output beserta nama tabel/filenya.

Output: A. Ringkasan hasil per hipotesis/skenario dengan angka dari output. B. Catatan MERAH/KUNING/HIJAU. C. Daftar deviasi.
```

## Kriteria G4
- Semua skenario dijalankan sesuai jumlah pengulangan di rencana (atau deviasi dicatat)
- 100% run punya hash SHA-256 sebelum dan sesudah; ketidakcocokan dijelaskan
- Testbed bisa dibangun ulang dari dokumentasi (diuji dengan membangun ulang minimal satu VM dari nol)
- Skrip analisis dan data mentah tersimpan di repo dengan versi
- Tidak ada akses ke sistem produksi lembaga

## Alat
VirtualBox atau Proxmox di host sendiri/lab kampus; Velociraptor; dd/dc3dd; `sha256sum`; Git untuk skrip dan log; Python (pandas, scipy) atau R untuk analisis; Mermaid untuk diagram.

## Jadwal (asumsi 8 jam/minggu; cek ulang, fase lab biasanya butuh lebih)
| Minggu | Langkah | Output |
|---|---|---|
| 7 | Fit + Design | Method Decision Record, matriks skenario, disetujui pembimbing |
| 8 | Instrument + Plan | Testbed berjalan, dataset sintetis, rencana terkunci (masuk proposal) |
| 9 | Pilot | 1 skenario × 2–3 run, perbaikan skrip |
| 10–12 | Collect & QC | Semua run + log lengkap |
| 13 | Analyze + Review | Hasil + catatan Experiment Reviewer |
| 14 | Interpret (+ wawancara pakar jika mixed) | Bahan Bab IV–V |

Setup testbed wajib selesai sebelum seminar proposal, karena spesifikasinya masuk Bab III.

## Tes penerimaan pack
1. Skrip hash: ubah 1 byte pada citra uji; skrip harus melaporkan `hash_cocok = tidak`.
2. Skrip analisis dijalankan ulang pada log contoh dengan hasil yang sudah diketahui; hasil identik.

## Tabel data tambahan (tahap MVP kode)
`experiment_run(run_id, project_id, scenario, repetition, started_at, finished_at, tool_version, sha256_source, sha256_result, status, notes)`. Rencana analisis memakai `analysis_plan` di core (kolom `item` = skenario).
