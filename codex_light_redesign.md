# TASK SPECIFICATION: ULTRA-MODERN LIGHT-MODE REDESIGN FOR ATA v2
Target File: `D:\code\ata-v2\web\index.html` and `D:\code\ata-v2\web\studio.css`

## 1. IDENTITY & HIGH-STAKES MANDATE
Kamu adalah Principal Frontend Architect & Senior Product Designer kelas Awwwards.
Kamu ditugaskan untuk merombak total antarmuka web `D:\code\ata-v2\web\index.html` dari dark-mode kaku menjadi **Ultra-Modern Editorial Light Mode** yang intuitif, hidup, dan memanjakan mata mahasiswa S2 muda (usia 24–32 tahun, terbiasa dengan standar Notion, Linear, Perplexity, dan Apple macOS).
Kegagalan estetika (kembali ke AI slop/card-shadow ungu) atau rusaknya fungsionalitas JavaScript API adalah fatal error.

## 2. NON-NEGOTIABLE CONSTRAINTS (SANDWICH TOP)
- TEMA WAJIB 100% LIGHT-MODE PERTAMA (PUTIH / SOFT-OFFWHITE / WARM CREAM). DILARANG MENGGUNAKAN LATAR BELAKANG HITAM/OBSIDIAN.
- SIDEBAR KIRI WAJIB BISA DITUTUP/COLLAPSIBLE (Toggle button dengan animasi CSS transisi halus `transition-all duration-300`).
- WORKBENCH KANAN WAJIB MEMILIKI TOGGLE COLLAPSE/EXPAND (agar pengguna bisa fokus menulis full-screen bila diinginkan).
- WAJIB MEMILIKI ANIMASI INTERAKTIF (Hover micro-lift, fade-in tabs, pulse badges, accordion smooth slide).
- SEMUA ID ELEMEN DAN FUNGSI JAVASCRIPT HARUS TETAP 100% UTUH:
  `user-input`, `chat-box`, `role-select`, `ledger-table-body`, `consistency-table-body`, `citation-result`, `quote-result`, `slop-result`, `must-counter`, `active-model-badge`, fungsi `sendMessage`, `loadDirectives`, `toggleStatus`, `loadConsistency`, `switchTab`, `runCitationVerify`, `runCitationTestPreset`, `runQuoteVerify`, `runSlopScan`.

## 3. TARGET AUDIENCE & PSYCHOLOGICAL PROFILE
- **Pengguna:** Mahasiswa Pascasarjana (S2) usia muda (24–32 tahun), karyawan Humas LKPP.
- **Mentalitas:** Waktu sempit, anti-ribet, menyukai antarmuka bersih bergaya Notion/Apple/Perplexity. Tidak suka istilah kodingan hacker atau layar gelap matrix yang melelahkan mata saat membaca ratusan teks tesis di siang hari.
- **Tone:** Segar, resmi tapi modern, elegan, kredibel, menyenangkan untuk dipakai berjam-jam.

## 4. DESIGN TOKENS & ATRIBUT VISUAL
- **Backgrounds:**
  - Page Canvas: `#F8FAFC` (Slate 50) atau `#FBFBFC` dengan sentuhan warm white.
  - Surface Cards: `#FFFFFF` (Putih Murni) dengan border halus `border-slate-200/80` dan ambient shadow `shadow-[0_2px_8px_rgba(0,0,0,0.04)]`.
  - Inset Panels: `#F1F5F9` (Slate 100) / `#F8FAFC`.
- **Accents:**
  - Primary / LKPP Emerald: `#0D9488` (Teal 600) & `#059669` (Emerald 600).
  - High Priority / MUST Badge: `#F59E0B` (Warm Amber) / `#EA580C` (Coral Orange).
  - Text Primary: `#0F172A` (Slate 900, tajam, high readability).
  - Text Secondary: `#475569` (Slate 600).
- **Tipografi:**
  - Heading: Google Fonts `Newsreader` (Serif editorial berkelas dengan style italic artistik).
  - UI Chrome & Body: `Plus Jakarta Sans` / `Inter` (Sangat terbaca, modern).
  - Metadata, DOI & Kode: `JetBrains Mono`.

## 5. INTERAKSI & FITUR WAJIB
1. **Collapsible Sidebar (Kiri):**
   - Tambahkan tombol toggle collapse di pojok sidebar (icon chevron atau hamburger modern).
   - Saat di-collapse, sidebar mengecil mulus menjadi icon-rail (w-16) atau bergeser keluar layar dengan toggle mengambang.
2. **Right Workbench (Kanan):**
   - Tambahkan tombol toggle expand/collapse di header kanan (tombol `[Sembunyikan/Buka Workbench]`).
   - Menyediakan mode "Fokus Menulis" (Distraction-free writing mode).
3. **Animasi & Micro-interactions:**
   - Tambahkan kelas transition dan keyframe sederhana di `studio.css` (misal hover cards naik 2px `hover:-translate-y-0.5 transition-transform duration-200`).
   - Animasi transisi tab yang lembut (fade & slight slide).
   - Status badge beranimasi halus saat di-klik toggle.
4. **Friendly Onboarding Chips untuk Mahasiswa S2:**
   - 🎙️ *"Catat Arahan Bu Henni (Transkrip Bimbingan)"*
   - 🎯 *"Uji Rumusan Masalah (Biar Disetujui Dosen)"*
   - 📚 *"Ringkas Paper van Riel & Fombrun Jadi 1 Halaman"*
   - 🚫 *"Scan Kata Klise Sebelum Dosen Baca"*

## 6. NON-NEGOTIABLE CONSTRAINTS (SANDWICH BOTTOM)
Ingat: Lakukan perubahan secara menyeluruh pada `D:\code\ata-v2\web\index.html` dan `D:\code\ata-v2\web\studio.css`.
Pastikan palet 100% LIGHT-MODE yang cantik dan bersih. Zero error di console JavaScript browser. Seluruh endpoint REST API backend (`/api/directives`, `/api/agent/chat`, `/api/verify/citation`, `/api/verify/quote`, `/api/audit/slop`) harus tetap terhubung normal.
