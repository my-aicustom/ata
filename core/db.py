"""
db.py - SQLite Database Engine for ATA v2
Implements the 10-Tier Data Model according to ATA-v2-spesifikasi.md.
"""
import sqlite3
import json
import os
from typing import Dict, Any, List, Optional
from datetime import datetime

if os.environ.get("VERCEL"):
    DB_PATH = "/tmp/ata_v2.db"
    src_db = os.path.join(os.path.dirname(__file__), "ata_v2.db")
    if os.path.exists(src_db) and not os.path.exists(DB_PATH):
        import shutil
        try:
            shutil.copy2(src_db, DB_PATH)
        except Exception:
            pass
else:
    DB_PATH = os.path.join(os.path.dirname(__file__), "ata_v2.db")

def get_connection(db_path: str = DB_PATH) -> sqlite3.Connection:
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    return conn

def init_db(db_path: str = DB_PATH):
    """Initialize database tables according to ATA v2 Specification"""
    conn = get_connection(db_path)
    cur = conn.cursor()

    cur.executescript("""
    CREATE TABLE IF NOT EXISTS supervisor_directive (
        id TEXT PRIMARY KEY,
        session_id TEXT NOT NULL,
        quote TEXT NOT NULL,
        directive TEXT NOT NULL,
        priority TEXT CHECK (priority IN ('MUST','SHOULD','NICE')),
        target_chapter TEXT,
        status TEXT CHECK (status IN ('open','addressed','clarify')) DEFAULT 'open',
        evidence_ref TEXT
    );

    CREATE TABLE IF NOT EXISTS source (
        id TEXT PRIMARY KEY,
        type TEXT CHECK (type IN ('journal','book','regulation','news','interview','report')),
        doi TEXT,
        title TEXT NOT NULL,
        authors TEXT NOT NULL,
        year INTEGER,
        verified INTEGER DEFAULT 0,
        brief_json TEXT
    );

    CREATE TABLE IF NOT EXISTS evidence (
        id TEXT PRIMARY KEY,
        source_id TEXT REFERENCES source(id),
        locator TEXT NOT NULL,
        text TEXT NOT NULL
    );

    CREATE TABLE IF NOT EXISTS claim (
        id TEXT PRIMARY KEY,
        chapter TEXT NOT NULL,
        sentence TEXT NOT NULL,
        evidence_ids TEXT NOT NULL, -- JSON array of evidence ids
        support TEXT CHECK (support IN ('supported','partial','unsupported')),
        author_origin TEXT CHECK (author_origin IN ('student','ai_expanded','ai_suggested'))
    );

    CREATE TABLE IF NOT EXISTS consistency_row (
        element TEXT PRIMARY KEY,
        content TEXT,
        score INTEGER CHECK (score BETWEEN 1 AND 4),
        critique TEXT
    );

    CREATE TABLE IF NOT EXISTS ai_usage_log (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        ts TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        agent TEXT NOT NULL,
        action TEXT NOT NULL,
        artifact TEXT
    );

    CREATE TABLE IF NOT EXISTS survey_construct (
        id TEXT PRIMARY KEY,
        name TEXT NOT NULL,
        definition TEXT NOT NULL,
        source_id TEXT REFERENCES source(id)
    );

    CREATE TABLE IF NOT EXISTS survey_item (
        id TEXT PRIMARY KEY,
        construct_id TEXT REFERENCES survey_construct(id),
        text_id TEXT NOT NULL,
        text_origin TEXT,
        reversed INTEGER DEFAULT 0,
        source_id TEXT REFERENCES source(id)
    );

    CREATE TABLE IF NOT EXISTS analysis_plan (
        id TEXT PRIMARY KEY,
        hypothesis TEXT NOT NULL,
        test TEXT NOT NULL,
        locked_at TIMESTAMP,
        plan_hash TEXT
    );
    """)

    # Seed supervisor directives if empty
    cur.execute("SELECT COUNT(*) FROM supervisor_directive")
    if cur.fetchone()[0] == 0:
        directives = [
            ("BH1-01", "Bu Henni 1", "kepercayaan masyarakat itu sebenarnya menipis ke pemerintah", "Jadikan kepercayaan publik terhadap lembaga sebagai masalah inti", "MUST", "I", "open", None),
            ("BH1-02", "Bu Henni 1", "Tete harus baca buku dari ... Wombrun dan Funreal", "Pakai van Riel & Fombrun sebagai landasan teori utama", "MUST", "II", "clarify", None),
            ("BH1-03", "Bu Henni 1", "lembaga-lembaga pemerintah kita crisis ... karena perilaku pemerintah", "Bingkai konteks sebagai situasi krisis kepercayaan", "MUST", "I", "open", None),
            ("BH1-04", "Bu Henni 1", "ada manajemen isu di lembaga pemerintahan", "Masukkan kerangka issues management", "MUST", "II", "open", None),
            ("BH1-05", "Bu Henni 1", "medianya masih media kecil ... bukan media mainstream", "Analisis lanskap relasi media LKPP", "MUST", "IV", "open", None),
            ("BH1-06", "Bu Henni 1", "pake konsultan ... harusnya jangan", "Evaluasi media relations via pihak ketiga; rekomendasi relasi langsung", "SHOULD", "IV", "open", None),
            ("BH1-07", "Bu Henni 1", "memprioritaskan konten ke arah program-program kebijakan prioritas", "Kaitkan strategi konten dengan program prioritas nasional", "SHOULD", "IV", "open", None),
            ("BH1-08", "Bu Henni 1", "LKPP dibawa presiden langsung", "Jelaskan perubahan kedudukan kelembagaan dan implikasi risikonya", "SHOULD", "I", "open", None),
            ("BH1-09", "Bu Henni 1", "masukannya untuk strategi komunikasi ... harusnya gini lho", "Output = rekomendasi strategi/perencanaan komunikasi", "MUST", "V", "open", None),
            ("BH1-10", "Bu Henni 1", "pendekatan komunikasi ... untuk mendapatkan kepercayaan publik", "Arah judul: pendekatan komunikasi kelembagaan untuk kepercayaan publik", "MUST", "Judul", "open", None),
            ("BH1-11", "Bu Henni 1", "draft yang saya bikin ... kirimkan dulu ke ibu? Boleh", "Kirim draf awal ke pembimbing sebelum lanjut", "MUST", "Proses", "open", None)
        ]
        cur.executemany("""
            INSERT INTO supervisor_directive (id, session_id, quote, directive, priority, target_chapter, status, evidence_ref)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """, directives)

    # Seed consistency rows if empty
    cur.execute("SELECT COUNT(*) FROM consistency_row")
    if cur.fetchone()[0] == 0:
        rows = [
            ("Judul", "Strategi Komunikasi Korporat LKPP dalam Membangun Kepercayaan Publik", 3, "Sesuai arahan BH1-10"),
            ("Masalah", "Krisis kepercayaan publik dan ketergantungan media humas pada konsultan pihak ketiga", 3, "Sesuai arahan BH1-01, BH1-03, BH1-05"),
            ("Rumusan Masalah", "RQ1: Kondisi eksisting komunikasi; RQ2: Manajemen isu & relasi media; RQ3: Rekomendasi strategi", 3, "FINER score memenuhi kriteria"),
            ("Tujuan", "Menganalisis strategi, evaluasi isu/media, menyusun strategi komunikasi", 3, "Selaras dengan RQ"),
            ("Teori", "Corporate Communication (van Riel & Fombrun); Issues Management; OECD Trust", 2, "Perlu konfirmasi edisi buku van Riel & Fombrun ke Bu Henni"),
            ("Metode", "Mixed Methods Sekuensial Eksplanatori (Survei pemangku kepentingan + Wawancara Humas)", 3, "Efektif dan menjawab arahan BH1-09"),
            ("Temuan", "Menunggu pengumpulan data", 1, "Belum ada data lapangan"),
            ("Kesimpulan", "Menunggu analisis Bab IV", 1, "Belum selesai"),
            ("Rekomendasi", "Menunggu analisis Bab IV", 1, "Wajib punya jejak ke data Bab IV")
        ]
        cur.executemany("INSERT INTO consistency_row VALUES (?, ?, ?, ?)", rows)

    conn.commit()
    conn.close()
    print("Database initialized successfully at:", db_path)

def log_ai_usage(agent: str, action: str, artifact: str = ""):
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("INSERT INTO ai_usage_log (agent, action, artifact) VALUES (?, ?, ?)", (agent, action, artifact))
    conn.commit()
    conn.close()

def get_directives(status_filter: Optional[str] = None) -> List[Dict[str, Any]]:
    conn = get_connection()
    cur = conn.cursor()
    if status_filter:
        cur.execute("SELECT * FROM supervisor_directive WHERE status = ? ORDER BY id", (status_filter,))
    else:
        cur.execute("SELECT * FROM supervisor_directive ORDER BY id")
    rows = [dict(r) for r in cur.fetchall()]
    conn.close()
    return rows

def update_directive_status(directive_id: str, new_status: str, evidence_ref: Optional[str] = None):
    conn = get_connection()
    cur = conn.cursor()
    if evidence_ref is not None:
        cur.execute("UPDATE supervisor_directive SET status = ?, evidence_ref = ? WHERE id = ?", (new_status, evidence_ref, directive_id))
    else:
        cur.execute("UPDATE supervisor_directive SET status = ? WHERE id = ?", (new_status, directive_id))
    conn.commit()
    conn.close()

if __name__ == "__main__":
    init_db()
    directives = get_directives()
    print(f"Loaded {len(directives)} directives from Bu Henni.")
