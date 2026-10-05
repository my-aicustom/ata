# Domain Profile: Informatika / Ilmu Komputer (sistem terdistribusi, keamanan & forensik digital)

Lapis 2 — Domain Profile. **[TAMBAHAN 1-OKT]** Seluruh file ini baru, disusun dari bahan folder `1 oktober/` (diagram sistem terdistribusi, lab Velociraptor, Nota Dinas Pusdatin). Rujukan di bawah adalah kandidat dan wajib lolos verifikasi sebelum dipakai.

## Persona
Pegawai TI (mis. Pusat Data dan Informasi) di lembaga pemerintah yang kuliah S2 sambil bekerja penuh waktu. Kekuatan: paham infrastruktur nyata. Risiko: terikat SMKI dan NDA lembaga; server kantor belum tentu tersedia untuk riset; godaan memakai sistem produksi sebagai objek uji.

## Sumber utama
- IEEE Xplore, ACM Digital Library, SpringerLink, ScienceDirect, arXiv (preprint: tandai belum *peer-reviewed*), DBLP untuk cek metadata.
- Standar: NIST (csrc.nist.gov), ISO/IEC, RFC (rfc-editor.org).
- Dokumentasi resmi tool (mis. docs.velociraptor.app) dengan versi dan tanggal akses.
- Nasional: Garuda, SINTA.

## Kriteria G2
- ≥30 sumber berstatus `valid`
- ≥70% terbit 5 tahun terakhir (bidang cepat berubah); teori dasar boleh lebih lama
- Prosiding IEEE/ACM/Springer dihitung setara jurnal
- ≥2 standar acuan (untuk forensik, kandidat: NIST SP 800-86, ISO/IEC 27037) [BELUM DIVERIFIKASI]
- ≥3 sumber nasional SINTA (untuk konteks Indonesia)
- Dokumentasi tool dan preprint boleh dipakai, tetapi tidak dihitung dalam angka minimum
- Research gap tertulis eksplisit
- Angka final mengikuti pedoman prodi

## Gaya sitasi
IEEE, kecuali pedoman prodi menentukan lain.

## Kerangka teori umum
| Konsep | Kandidat rujukan (wajib lolos verifikasi) |
|---|---|
| Proses forensik digital | NIST SP 800-86 (integrasi forensik ke respons insiden); ISO/IEC 27037 (identifikasi, pengumpulan, akuisisi, preservasi bukti digital) |
| Integritas bukti | Fungsi hash kriptografis (SHA-256, FIPS 180-4); *chain of custody* |
| Forensik jarak jauh / *live response* | Literatur *remote forensic acquisition*, *endpoint detection and response* |
| Sistem terdistribusi | Konsistensi & replikasi (mis. CAP theorem), arsitektur *client–server*, API Gateway |
| Desain artefak | Design Science Research (Hevner dkk.; Peffers dkk.) |

## Aturan Bab I
Masalah nyata di lingkungan kerja (tanpa detail infrastruktur rahasia) → bukti awal (insiden publik, laporan, data uji awal) → keterbatasan solusi yang ada → pendekatan yang diusulkan → penelitian terdahulu → celah → tujuan dan batasan lingkup (lab, versi tool, jenis sistem berkas).

## Domain Expert (untuk Critic Board dan Mock Examiner)
- Persona: pakar keamanan sistem dan forensik digital, sekaligus paham sistem terdistribusi.
- Teori/standar acuan: NIST SP 800-86, ISO/IEC 27037, prinsip integritas bukti, praktik eksperimen sistem yang bisa diulang.
- Pertanyaan kunci yang selalu diuji:
  - Apakah eksperimen bisa diulang orang lain dari dokumentasi testbed (versi tool, spesifikasi VM, dataset)?
  - Apakah integritas bukti dibuktikan di setiap perpindahan data (hash sebelum/sesudah, *chain of custody*)?
  - Apakah ada baseline pembanding yang adil?
  - Apakah hasil lab bisa digeneralisasi ke lingkungan nyata, dan apa batasannya?
  - Apakah ada detail infrastruktur lembaga yang tidak boleh dipublikasikan di naskah?

## Bentuk kontribusi (untuk Contribution Builder)
Artefak dan panduan implementasi dengan kolom: Masalah | Artefak/prosedur yang diusulkan | Prasyarat (infrastruktur, izin, SDM) | Langkah implementasi | Risiko keamanan | Indikator keberhasilan (metrik terukur) | Dasar (hasil eksperimen/evaluasi Bab IV + standar).

## Daftar istilah baku
- *acquisition* → akuisisi
- *disk image* → citra disk
- *dead disk analysis* → analisis disk mati (sistem dalam keadaan mati)
- *live response* → respons langsung (sistem menyala)
- *chain of custody* → rantai penguasaan bukti
- *endpoint* → titik akhir (*endpoint*)

## Frasa terlarang tambahan
- "sistem yang aman dan handal" (tanpa metrik)
- "teknologi canggih"
- "solusi terbaik" (tanpa pembanding)

## Batasan wajib
- Eksperimen hanya di testbed lab dengan data sintetis. Tidak menyentuh sistem produksi lembaga.
- Diagram di naskah memakai nama generik. Tidak ada nama server, IP, akun, atau konfigurasi akses nyata.
- Naskah ditinjau unit TI lembaga sebelum diserahkan ke kampus.

## Method Pack yang lazim
Cocok: system-experiment, dsr, mixed (system-experiment + interview pakar untuk evaluasi). Jarang cocok: content-analysis.

## Tes penerimaan profil
Belum dijalankan. Jalankan Critic Board pada satu bab tesis forensik/sistem terdistribusi yang sudah dinilai dosen, lalu bandingkan catatannya.
