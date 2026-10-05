# Catatan bahan 1 Oktober

[TAMBAHAN 1-OKT] Catatan untuk Consistency Auditor, artifact-designer, dan testbed-designer. Semua butir perlu dicek pemilik tesis.

## A. `Arsitektur System Terdistribusi THESIS.png`

1. API Gateway hanya berada di depan Application System. Branch Office 1 dan 2 terhubung langsung ke Main Office Cloud tanpa gateway. Batas keamanan jadi tidak seragam; jelaskan alasannya atau samakan jalurnya.
2. Tiap cabang punya database sendiri, tetapi mekanisme sinkronisasi/replikasi ke Database Main Office tidak digambar. Untuk tesis sistem terdistribusi, mekanisme ini dan model konsistensinya adalah inti yang akan ditanya penguji.
3. Monitoring tergambar di jalur data antara Main Office System dan Database Main Office. Biasanya monitoring berada di samping jalur (menerima metrik/log), bukan di tengah jalur data.
4. Di tiap cabang, hanya satu USER yang punya panah ke server; dua USER lain hanya terhubung garis horizontal.
5. Velociraptor tidak muncul di diagram ini. Jika topiknya forensik jarak jauh, tunjukkan posisi Velociraptor Server (pusat) dan client (cabang), agar diagram ini dan lab VM terhubung.

## B. `gemini-code-1790822558295.txt` (lab 3 VM)

1. Jalur bukti dari VM 2 (endpoint) ke VM 3 (analisis dead disk) tidak jelas: garis dari VM 2 tidak masuk ke kotak VM 3. Tulis jalur eksplisit (mis. citra disk → File Store VM 1 → VM 3) dan titik pengecekan SHA-256 di tiap perpindahan (rantai penguasaan bukti).
2. Port "Web GUI 8001/443" perlu dicek ke dokumentasi Velociraptor versi yang dipakai. Port bawaan GUI, frontend client, dan API berbeda. [BELUM DIVERIFIKASI]
3. Target storage LUKS terenkripsi. Analisis dead disk butuh kunci, atau akuisisi dilakukan saat volume terbuka (live). Skenario eksperimen perlu membedakan dua kondisi ini.
4. CentOS sebagai target: CentOS Linux sudah end-of-life. Pertimbangkan Rocky Linux atau AlmaLinux agar hasil relevan.
5. Tulis versi setiap tool (Velociraptor, dc3dd, kernel) di Bab III agar eksperimen bisa diulang.

## C. Nota Dinas 26438/Pusdatin/09/2026

1. Bukan data untuk tesis komunikasi. Nilainya: bukti kendala infrastruktur (server development "belum dapat diberikan"), alasan memakai testbed lab, dan contoh penerapan *least privilege* serta SMKI (Kep. Kepala LKPP 171/2025).
2. Nota memuat nama personel penyedia, nama dan nomor HP narahubung, serta rincian akses. Jangan unggah dokumen asli ke Claude Project. Pakai ringkasan anonim (contoh di `core/data-intake.md`).
3. Jika LMS PBJ (Moodle) ternyata objek studi tesis ini, profil tesis, Method Pack, dan risiko perlu ditinjau ulang.
