# TASK REDESIGN AWWWARDS-TIER UNTUK CODEX
Target File: `D:\code\ata-v2\web\index.html`

## Mandat Desain:
Bos meminta UI ATA v2 di-redesign ulang total agar berkelas **Awwwards-Tier (Editorial Academic Architecture / No AI Slop)**.
Tinggalkan gaya card-and-shadow generik AI template. Ubah menjadi antarmuka riset akademik setara majalah kurasi ilmiah dunia (kombinasi Linear precision + Kinfolk/Stripe Press editorial typography).

## Arahan Estetika:
1. **Palet Warna**:
   - Deep Obsidian / Architectural Ink: `#090A0D`, `#111318`, `#181A20`
   - Borders: Subtle hairline divider `rgba(255, 255, 255, 0.07)` dan hover glow
   - Aksen: Warm Cream/Bone (`#F5EFE6`), Muted Amber (`#D97706` untuk MUST), Sage/Emerald (`#10B981` untuk valid sitasi), Crimson (`#EF4444` untuk fabrikasi/slop)
2. **Tipografi Kelas Dunia**:
   - Google Fonts: `Newsreader` (serif editorial untuk heading, kutipan dosen, dan aksen estetika)
   - `Plus Jakarta Sans` / `Inter` untuk body UI
   - `JetBrains Mono` untuk DOI, ID direktif (BH1-01), dan data teknis
3. **Layout & Micro-craft**:
   - Split-screen asimetris yang proporsional (Left: 38% Chat Studio, Right: 62% Research Ledger & Lab)
   - Header floating minimalis dengan status live OpenRouter dan MUST counter
   - Table Ledger Bu Henni dengan tipografi serif untuk kutipan lisan Bu Henni, badge prioritas berkarakter, dan status pill interaktif
   - Lab tabs: Navigation pill glassmorphism halus, visual alert dengan border tipis dan tipografi presisi
4. **Fungsi Wajib Dipertahankan 100%**:
   - Semua fungsi JavaScript dan elemen ID (`user-input`, `chat-box`, `role-select`, `ledger-table-body`, `consistency-table-body`, `citation-result`, `quote-result`, `slop-result`, `must-counter`, dll) HARUS TETAP ADA dan bekerja dengan endpoint REST API backend (`/api/directives`, `/api/agent/chat`, `/api/verify/citation`, `/api/verify/quote`, `/api/audit/slop`).

Instruksi: Tulis ulang file `D:\code\ata-v2\web\index.html` secara lengkap dan pastikan tidak ada syntax error.
