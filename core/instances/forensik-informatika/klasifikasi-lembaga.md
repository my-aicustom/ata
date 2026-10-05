# Klasifikasi informasi organisasi: LKPP

[TAMBAHAN 1-OKT] Dipindah dari `core/data-intake.md` (v3 awal) ke instance agar core tidak menyebut lembaga tertentu. [BARU MULTI-USER]

Acuan: Sistem Manajemen Keamanan Informasi (SMKI) menurut **Keputusan Kepala LKPP Nomor 171 Tahun 2025**, dirujuk dalam Nota Dinas 26438/Pusdatin/09/2026. Isi pemetaan masih kosong sampai dokumen keputusan itu diperoleh dan dibaca.

| Klasifikasi resmi organisasi | Label sistem | Dasar aturan |
|---|---|---|
| [PERLU SUMBER] | Publik | Kep. Kepala LKPP 171/2025 |
| [PERLU SUMBER] | Internal-diizinkan | Kep. Kepala LKPP 171/2025 |
| [PERLU SUMBER] | Rahasia | Kep. Kepala LKPP 171/2025 |

## [TAMBAHAN 1-OKT] Contoh kasus: Nota Dinas 26438/Pusdatin/09/2026

| Aspek | Penilaian |
|---|---|
| Jenis | Nota dinas internal, ditandatangani elektronik |
| Isi sensitif | Nama 4 personel penyedia, nama dan nomor HP narahubung, rincian pemberian akses VPN, GitLab, dan repositori; penolakan akses source code SSO dan portal |
| Label | Internal. Tidak boleh diunggah apa adanya |
| Jika dibutuhkan | Ringkasan anonim: "Akses server development untuk pengembang belum dapat diberikan karena keterbatasan infrastruktur (Nota Dinas Pusdatin, September 2026)". Label ringkasan: Internal-diizinkan, setelah ada izin |
| Nilai untuk tesis | Bukti kendala infrastruktur (alasan memakai testbed lab) dan contoh penerapan prinsip *least privilege* |
