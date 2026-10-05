# Profil Tesis (hanya isi yang sudah disetujui pembimbing)

Status: **draf. Tesis masih tahap rancangan (pra-proposal); topik belum final.** [TAMBAHAN 1-OKT]

Dugaan topik (dari bahan 1 Oktober): akuisisi dan analisis forensik digital jarak jauh pada endpoint Linux (Ext4/LVM/LUKS) dengan Velociraptor, dalam arsitektur terdistribusi kantor pusat–cabang, dibandingkan dengan akuisisi lokal (dd/dc3dd) + analisis dead disk.

Kandidat rumusan masalah (untuk didiskusikan, bukan keputusan):
1. Bagaimana rancangan arsitektur akuisisi forensik jarak jauh untuk organisasi dengan kantor pusat dan cabang? (DSR)
2. Bagaimana kinerja dan integritas bukti akuisisi jarak jauh dengan Velociraptor dibandingkan akuisisi lokal dd/dc3dd pada volume Ext4, LVM, dan LUKS? (Experiment)
3. Apa batasan akuisisi jarak jauh pada volume terenkripsi LUKS? (Experiment)

Metode / Method Pack: dsr (artefak arsitektur) + system-experiment (evaluasi di testbed 3 VM)
Testbed (dari bahan): VM1 Velociraptor Server + File Store; VM2 endpoint Linux + Velociraptor Client + dd/dc3dd; VM3 workstation analisis dead disk + parser raw_ext4 + verifikasi SHA-256
Teori/standar utama (kandidat): NIST SP 800-86, ISO/IEC 27037, Design Science Research [BELUM DIVERIFIKASI]
Dokumen lembaga yang boleh dipakai: Nota Dinas 26438/Pusdatin/09/2026 hanya dalam bentuk ringkasan anonim (lihat core/data-intake.md); permission_ref: [isi]

## Keputusan terbuka
- [ ] Konfirmasi: bahan 1 Oktober memang untuk tesis ini?
- [ ] Topik: forensik, sistem terdistribusi, atau gabungan?
- [ ] Apakah LMS PBJ (Moodle) objek studi? Jika ya, profil ini ditulis ulang
- [ ] Izin atasan untuk topik yang menyentuh infrastruktur lembaga
- [ ] Host untuk testbed (pribadi atau lab kampus) dan spesifikasinya

## Status Gate
- [ ] G1 Topik
- [ ] G2 Literatur
- [ ] G3 Proposal
- [ ] G4 Data
- [ ] G5 Draf
- [ ] G6 Sidang
