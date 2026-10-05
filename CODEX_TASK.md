# ATA v2 OVERHAUL: BIG-AI UI REDESIGN & CORE MISSING FEATURES
Target Working Directory: `D:\code\ata-v2\`

## 1. MANDAT DESAIN: BIG-AI INTERFACE (CLAUDE / CHATGPT / PERPLEXITY VIBE)
Desain antarmuka `D:\code\ata-v2\web\index.html` harus dirombak total menjadi model aplikasi AI papan atas dunia (seperti Claude.ai / ChatGPT / Perplexity Workbench):
- **Layout Struktur**:
  1. **Left Navigation Sidebar (Colapsible)**:
     - Header brand: ATA v2 (Advanced Thesis Architect) + S2 LKPP Badge.
     - New Chat Button (+ Percakapan Baru).
     - Role Selector List: Ledger, Topic Framer, Research Brief, Drafting, Critic, Method Fit, Stats Reviewer, Mock Examiner.
     - Knowledge Links: 00-Ledger, 01-Profil, 02-Matriks Konsistensi, 03-Briefs, 04-Matriks Literatur.
  2. **Central Chat Studio**:
     - Modern Clean Thread: Avatar peran AI, bubble percakapan berdinding tipis, markdown formatting, copy message action, metadata badge (tokens/latency/model).
     - Bottom Floating Prompt Bar: Input textarea auto-resize, tombol pilih peran, tombol attachment, status model live (OpenRouter Free Tier), tombol Send `[Enter]`.
  3. **Right Inspector & Workbench Drawer (Canvas Mode)**:
     - Tab 1: **Supervisor Feedback Ledger (Bu Henni)**: List arahan MUST/SHOULD/NICE, live badge, status toggle (open / addressed / clarify), bukti locator.
     - Tab 2: **Quality Gates (G1 - G6)**: Dashboard visual 6 gerbang kualitas tesis dengan progress bar dan status lolos/belum.
     - Tab 3: **Claim-Evidence Checker**: Textarea draf untuk scan kalimat, tagging author origin `(M)`, `(M+AI)`, `(AI)`, dan deteksi `[PERLU SUMBER]`.
     - Tab 4: **Citation & Quote Lab**: Verifikasi deterministik Crossref, OpenAlex, dan string-match PDF.
     - Tab 5: **Anti-Slop Audit**: Deteksi 18 frasa klise terlarang LKPP.
- **Estetika & Styling**:
  - Warna: Dark theme kelas satu (`#0B0D11`, `#14171F`, `#1C202B`), border hairline halus (`rgba(255,255,255,0.08)`), aksen Emerald (`#10B981`) dan Amber (`#F59E0B`).
  - Tipografi: Plus Jakarta Sans / Inter + JetBrains Mono untuk kode/DOI.
  - Zero AI slop, zero template card ungu murahan.

## 2. BACKEND & FITUR ENGINE BARU:
1. `D:\code\ata-v2\core\gates.py`:
   - Evaluasi otomatis gerbang G1 sampai G6:
     * G1: FINER score >= 3, all MUST directives addressed.
     * G2: Source quota check (min 30 verified sources, >=60% recent 10 yrs, >=5 core books, >=10 intl journals, >=5 SINTA).
     * G3: Consistency matrix score >= 3.
     * G4: Survey statistical criteria (loading >= 0.70, AVE >= 0.50, HTMT < 0.90, CR >= 0.70).
     * G5: Final draft criteria (0 invalid citations, 0 unsupported claims, 0 open red critiques, similarity check).
     * G6: Defense simulation score (>=80% questions answered with score >= 3).
2. `D:\code\ata-v2\core\claims.py`:
   - Deteksi klaim per kalimat dari draf mahasiswa.
   - Ekstrak penanda `[Brief: ID, hal. X]` dan `[Ledger: ID]`.
   - Identifikasi kalimat tanpa rujukan `[PERLU SUMBER]`.
   - Klasifikasi persentase `author_origin` (`student`, `ai_expanded`, `ai_suggested`).
3. `D:\code\ata-v2\server.py`:
   - Tambah endpoint REST API:
     * `GET /api/gates`: Mengembalikan status evaluasi G1-G6 saat ini.
     * `POST /api/audit/claims`: Menerima teks draf dan mengembalikan analisis klaim ber-bukti.
     * `GET /api/knowledge/files`: Menampilkan daftar file knowledge yang aktif.

Semua perubahan harus langsung diterapkan ke file disk di `D:\code\ata-v2\` dan dipastikan bebas syntax error.
