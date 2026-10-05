# Katalog Method Pack

[BARU MULTI-USER] Daftar pack yang sudah ada dan kandidat pack berikutnya. Pack baru dibuat dengan peran `method-pack-builder` (`core/onboarding.md`), hanya saat ada tesis nyata yang membutuhkannya (YAGNI). [BARU SELF-SERVICE] Pengguna boleh membuat draf sendiri dan langsung memakainya; tim menguji sebelum masuk katalog untuk semua pengguna.

## Sudah ada

| Pack | Untuk | Analisis | Status |
|---|---|---|---|
| `survey` | Kuantitatif, kuesioner, PLS-SEM/regresi | SmartPLS, JASP, SPSS, R | Dari v2 |
| `interview` | Kualitatif, wawancara mendalam | Analisis tematik | Dari v2 |
| `content-analysis` | Analisis isi berita/dokumen | Deskriptif, Krippendorff α | Dari v2 |
| `system-experiment` | Eksperimen sistem komputer di testbed lab | Skrip Python/R | [TAMBAHAN 1-OKT] |
| `dsr` | Design Science Research (artefak + evaluasi) | Sesuai metode evaluasi | [TAMBAHAN 1-OKT] |

## Kandidat (belum dibuat)

Diurutkan dari yang paling sering dipakai di program magister di Indonesia (perkiraan, belum diukur).

| Pack | Untuk | Prodi yang biasa memakai | Catatan khusus |
|---|---|---|---|
| `secondary-data` | Data sekunder / panel / laporan keuangan / data BPS | Manajemen, Akuntansi, Ekonomi, Administrasi Publik | Sumber data resmi; uji asumsi klasik; Stata/EViews/R |
| `normative-legal` | Penelitian hukum normatif (perundang-undangan, putusan, doktrin) | Magister Hukum | Verifikasi non-DOI wajib (regulasi, putusan); tanpa data lapangan |
| `case-study` | Studi kasus multi-sumber (wawancara + dokumen + observasi) | Administrasi Publik, Manajemen, Komunikasi | Bisa dirakit dari `interview` + `content-analysis` |
| `behavioral-experiment` | Eksperimen / kuasi-eksperimen pada manusia | Pendidikan, Psikologi, Pemasaran | Ethical clearance; randomisasi; pre-test/post-test |
| `research-development` | R&D (Borg & Gall, ADDIE, 4D) — produk + validasi ahli + uji coba | Pendidikan | Validasi ahli; uji kelayakan produk |
| `classroom-action` | Penelitian tindakan kelas (siklus) | Pendidikan | Siklus perencanaan–tindakan–observasi–refleksi |
| `ml-experiment` | Eksperimen machine learning (dataset, train/test, metrik) | Informatika, Sistem Informasi | Beda dari `system-experiment`: kebocoran data, pembagian dataset, baseline model |
| `slr` | Systematic literature review / bibliometrik | Semua | PRISMA; protokol dikunci; verifikasi sitasi sangat berat |
| `focus-group` | Diskusi kelompok terarah | Komunikasi, Kesehatan Masyarakat, Pemasaran | Bisa jadi varian `interview` |

## Aturan pack baru

1. Ikuti `_template.md` dan 8 langkah yang sama.
2. Tidak boleh mengubah `core/`. Jika terasa perlu, catat di `PERUBAHAN.md` dan diskusikan dulu.
3. Lolos tes penerimaan sebelum dipakai untuk tesis sungguhan.
4. Gabungan metode (mixed methods) dibuat dengan memasang beberapa pack di `method_packs`, bukan pack baru, kecuali titik integrasinya khas.
