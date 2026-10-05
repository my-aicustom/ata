"""Migrate the legacy ATA v2 SQLite workspace into one ATA v3 project.

Usage:
  python scripts/migrate_v2_to_v3.py core/ata_v2.db [session-id]

The migration is additive. It never deletes the v2 database.
"""
from __future__ import annotations
import json, sqlite3, sys
from pathlib import Path
from typing import Any, Dict

ROOT=Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path: sys.path.insert(0,str(ROOT))
from core import db


def _table_exists(conn,name):
    return conn.execute("SELECT 1 FROM sqlite_master WHERE type='table' AND name=?",(name,)).fetchone() is not None


def migrate(old_db: str, session_id: str='migration-local') -> Dict[str, Any]:
    path=Path(old_db)
    if not path.is_file(): raise FileNotFoundError(path)
    db.init_db()
    pid=db.create_project(session_id,{
        'name':'Migrasi ATA v2','student':'Mahasiswa lama','program':'Program Magister','topic':'Workspace hasil migrasi ATA v2','domain':'komunikasi','method':'survey','stage':'proposal'
    })
    src=sqlite3.connect(str(path)); src.row_factory=sqlite3.Row
    directives=sources=consistency=0
    if _table_exists(src,'supervisor_directive'):
        items=[]
        for r in src.execute('SELECT * FROM supervisor_directive').fetchall():
            d=dict(r); items.append({'id':d.get('id'),'session_label':d.get('session_id'),'quote':d.get('quote'),'directive':d.get('directive'),'priority':d.get('priority'),'target_chapter':d.get('target_chapter'),'status':d.get('status'),'evidence_ref':d.get('evidence_ref')})
        directives=db.upsert_directives(pid,items)
    if _table_exists(src,'source'):
        for r in src.execute('SELECT * FROM source').fetchall():
            d=dict(r); authors=d.get('authors') or ''
            try:
                parsed=json.loads(authors); authors=parsed if isinstance(parsed,list) else [str(parsed)]
            except Exception: authors=[x.strip() for x in str(authors).split(';') if x.strip()] or [str(authors)]
            db.save_source(pid,{'id':d.get('id'),'type':d.get('type') or 'journal','doi':d.get('doi'),'title':d.get('title') or 'Untitled','authors':authors,'year':d.get('year'),'verified':bool(d.get('verified')),'verification_status':'verified' if d.get('verified') else 'candidate','brief_json':json.loads(d.get('brief_json') or '{}') if isinstance(d.get('brief_json'),str) else d.get('brief_json')})
            sources+=1
    if _table_exists(src,'consistency_row'):
        rows=src.execute('SELECT * FROM consistency_row').fetchall()
        with db.get_connection() as conn:
            for r in rows:
                d=dict(r); conn.execute('INSERT INTO consistency_row(project_id,element,content,score,critique) VALUES(?,?,?,?,?) ON CONFLICT(project_id,element) DO UPDATE SET content=excluded.content,score=excluded.score,critique=excluded.critique',(pid,d.get('element'),d.get('content'),d.get('score'),d.get('critique'))); consistency+=1
    src.close()
    return {'project_id':pid,'directives':directives,'sources':sources,'consistency_rows':consistency,'old_db':str(path)}


def main(argv=None):
    argv=list(sys.argv[1:] if argv is None else argv)
    if not argv:
        print(__doc__); return 2
    report=migrate(argv[0],argv[1] if len(argv)>1 else 'migration-local')
    print(json.dumps(report,indent=2,ensure_ascii=False)); return 0

if __name__=='__main__': raise SystemExit(main())
