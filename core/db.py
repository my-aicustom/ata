"""ATA v3 persistence layer with project isolation.

Backends:
- DATABASE_URL=postgresql://... -> managed PostgreSQL (recommended for Vercel/SaaS)
- otherwise SQLite in ATA_DATA_DIR (recommended for local/self-hosted single server)

Every thesis row is project-scoped and every project belongs to an opaque browser
session. There is no process-global "active thesis" state.
"""
from __future__ import annotations

import json
import os
import secrets
import sqlite3
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional

_SCHEMA_VERSION = 3


def _backend() -> str:
    return 'postgres' if os.getenv('DATABASE_URL', '').startswith(('postgres://','postgresql://')) else 'sqlite'


def _data_dir() -> Path:
    base = os.getenv('ATA_DATA_DIR')
    if base:
        p = Path(base)
    elif os.getenv('VERCEL'):
        p = Path('/tmp/ata-v3')
    else:
        p = Path(__file__).resolve().parent / 'data'
    p.mkdir(parents=True, exist_ok=True)
    return p


def _db_path() -> Path:
    return _data_dir() / 'ata_v3.db'


def _translate_qmark(sql: str) -> str:
    """Convert qmark placeholders to psycopg placeholders.
    SQL in this module contains no literal question marks.
    """
    return sql.replace('?', '%s')


class _PGResult:
    def __init__(self, cursor): self._cursor = cursor
    @property
    def rowcount(self): return self._cursor.rowcount
    def fetchone(self): return self._cursor.fetchone()
    def fetchall(self): return self._cursor.fetchall()


class _PGConnection:
    def __init__(self):
        try:
            import psycopg
            from psycopg.rows import dict_row
        except ImportError as e:
            raise RuntimeError('DATABASE_URL diset tetapi psycopg belum terpasang. Jalankan pip install -r requirements.txt') from e
        self._conn = psycopg.connect(os.environ['DATABASE_URL'], row_factory=dict_row)
    def execute(self, sql, params=()):
        return _PGResult(self._conn.execute(_translate_qmark(sql), params))
    def executescript(self, script):
        for statement in [x.strip() for x in script.split(';') if x.strip()]:
            self._conn.execute(statement)
    def __enter__(self): return self
    def __exit__(self, exc_type, exc, tb):
        try:
            if exc_type is None: self._conn.commit()
            else: self._conn.rollback()
        finally: self._conn.close()
        return False
    def close(self): self._conn.close()


class _SQLiteConnection:
    def __init__(self, path: str):
        self._conn = sqlite3.connect(path, timeout=20)
        self._conn.row_factory = sqlite3.Row
        self._conn.execute('PRAGMA foreign_keys = ON')
        self._conn.execute('PRAGMA journal_mode = WAL')
    def execute(self, sql, params=()): return self._conn.execute(sql, params)
    def executescript(self, script): return self._conn.executescript(script)
    def __enter__(self): return self
    def __exit__(self, exc_type, exc, tb):
        try:
            if exc_type is None: self._conn.commit()
            else: self._conn.rollback()
        finally: self._conn.close()
        return False
    def close(self): self._conn.close()


def get_connection(db_path: Optional[str] = None):
    if _backend() == 'postgres' and db_path is None:
        return _PGConnection()
    return _SQLiteConnection(db_path or str(_db_path()))


def reset_for_tests() -> None:
    if _backend() != 'sqlite':
        return
    path = _db_path()
    for suffix in ('', '-wal', '-shm'):
        try: Path(str(path) + suffix).unlink()
        except FileNotFoundError: pass


_SCHEMA = """
CREATE TABLE IF NOT EXISTS meta (key TEXT PRIMARY KEY, value TEXT NOT NULL);
CREATE TABLE IF NOT EXISTS project (
    id TEXT PRIMARY KEY, session_id TEXT NOT NULL, name TEXT NOT NULL, student TEXT NOT NULL,
    program TEXT NOT NULL, advisor TEXT, topic TEXT NOT NULL, domain TEXT NOT NULL DEFAULT 'umum',
    method TEXT NOT NULL DEFAULT 'survey', stage TEXT NOT NULL DEFAULT 'start', deadline TEXT,
    institution TEXT, insider INTEGER NOT NULL DEFAULT 0, language TEXT NOT NULL DEFAULT 'Indonesia',
    campus TEXT, created_at TEXT NOT NULL, updated_at TEXT NOT NULL
);
CREATE INDEX IF NOT EXISTS idx_project_session ON project(session_id, updated_at DESC);
CREATE TABLE IF NOT EXISTS project_state (
    session_id TEXT PRIMARY KEY, active_project_id TEXT,
    FOREIGN KEY(active_project_id) REFERENCES project(id) ON DELETE SET NULL
);
CREATE TABLE IF NOT EXISTS supervisor_directive (
    project_id TEXT NOT NULL, id TEXT NOT NULL, session_label TEXT, quote TEXT NOT NULL DEFAULT '',
    directive TEXT NOT NULL, priority TEXT NOT NULL CHECK(priority IN ('MUST','SHOULD','NICE')),
    target_chapter TEXT, status TEXT NOT NULL DEFAULT 'open' CHECK(status IN ('open','addressed','clarify')),
    evidence_ref TEXT, created_at TEXT NOT NULL, PRIMARY KEY(project_id,id),
    FOREIGN KEY(project_id) REFERENCES project(id) ON DELETE CASCADE
);
CREATE TABLE IF NOT EXISTS source (
    project_id TEXT NOT NULL, id TEXT NOT NULL, type TEXT NOT NULL DEFAULT 'journal', doi TEXT, url TEXT,
    title TEXT NOT NULL, authors TEXT NOT NULL DEFAULT '[]', year INTEGER, verified INTEGER NOT NULL DEFAULT 0,
    verification_status TEXT NOT NULL DEFAULT 'candidate', brief_json TEXT, created_at TEXT NOT NULL,
    PRIMARY KEY(project_id,id), FOREIGN KEY(project_id) REFERENCES project(id) ON DELETE CASCADE
);
CREATE INDEX IF NOT EXISTS idx_source_project_verified ON source(project_id, verified, year);
CREATE TABLE IF NOT EXISTS evidence (
    project_id TEXT NOT NULL, id TEXT NOT NULL, source_id TEXT NOT NULL, locator TEXT NOT NULL, text TEXT NOT NULL,
    PRIMARY KEY(project_id,id), FOREIGN KEY(project_id,source_id) REFERENCES source(project_id,id) ON DELETE CASCADE
);
CREATE TABLE IF NOT EXISTS claim (
    project_id TEXT NOT NULL, id TEXT NOT NULL, chapter TEXT, sentence TEXT NOT NULL,
    evidence_ids TEXT NOT NULL DEFAULT '[]', support TEXT NOT NULL DEFAULT 'unsupported',
    author_origin TEXT NOT NULL DEFAULT 'student', PRIMARY KEY(project_id,id),
    FOREIGN KEY(project_id) REFERENCES project(id) ON DELETE CASCADE
);
CREATE TABLE IF NOT EXISTS consistency_row (
    project_id TEXT NOT NULL, element TEXT NOT NULL, content TEXT, score INTEGER CHECK(score BETWEEN 1 AND 4),
    critique TEXT, PRIMARY KEY(project_id,element), FOREIGN KEY(project_id) REFERENCES project(id) ON DELETE CASCADE
);
CREATE TABLE IF NOT EXISTS gate_assessment (
    project_id TEXT NOT NULL, gate TEXT NOT NULL, data_json TEXT NOT NULL, updated_at TEXT NOT NULL,
    PRIMARY KEY(project_id,gate), FOREIGN KEY(project_id) REFERENCES project(id) ON DELETE CASCADE
);
CREATE TABLE IF NOT EXISTS artifact (
    id TEXT PRIMARY KEY, project_id TEXT NOT NULL, kind TEXT NOT NULL, title TEXT NOT NULL, version INTEGER NOT NULL,
    content TEXT NOT NULL, source_refs TEXT NOT NULL DEFAULT '[]', created_at TEXT NOT NULL,
    UNIQUE(project_id,kind,title,version), FOREIGN KEY(project_id) REFERENCES project(id) ON DELETE CASCADE
);
CREATE INDEX IF NOT EXISTS idx_artifact_lookup ON artifact(project_id,kind,title,version DESC);
CREATE TABLE IF NOT EXISTS revision_task (
    id TEXT PRIMARY KEY, project_id TEXT NOT NULL, directive_id TEXT, target_kind TEXT, target_title TEXT,
    status TEXT NOT NULL DEFAULT 'open' CHECK(status IN ('open','proposed','accepted','rejected','done')),
    before_text TEXT, proposed_text TEXT, rationale TEXT, created_at TEXT NOT NULL, updated_at TEXT NOT NULL,
    FOREIGN KEY(project_id) REFERENCES project(id) ON DELETE CASCADE
);
CREATE TABLE IF NOT EXISTS defense_score (
    id TEXT PRIMARY KEY, project_id TEXT NOT NULL, question TEXT NOT NULL, answer TEXT,
    score INTEGER CHECK(score BETWEEN 1 AND 4), feedback TEXT, created_at TEXT NOT NULL,
    FOREIGN KEY(project_id) REFERENCES project(id) ON DELETE CASCADE
);
CREATE TABLE IF NOT EXISTS ai_usage_log (
    id TEXT PRIMARY KEY, project_id TEXT, ts TEXT NOT NULL, agent TEXT NOT NULL, action TEXT NOT NULL, artifact TEXT
);
"""


def init_db(db_path: Optional[str] = None) -> None:
    with get_connection(db_path) as conn:
        conn.executescript(_SCHEMA)
        conn.execute("INSERT INTO meta(key,value) VALUES('schema_version',?) ON CONFLICT(key) DO UPDATE SET value=excluded.value", (str(_SCHEMA_VERSION),))


def _now() -> str: return datetime.now(timezone.utc).isoformat()
def _id(prefix: str) -> str: return prefix + '_' + secrets.token_urlsafe(9).replace('-','').replace('_','')[:12]


def create_project(session_id: str, data: Dict[str, Any]) -> str:
    init_db(); pid = _id('th'); now = _now()
    topic=(data.get('topic') or 'Tesis baru').strip(); program=(data.get('program') or 'Program Magister').strip(); student=(data.get('student') or 'Mahasiswa').strip(); name=(data.get('name') or topic or program)[:120]
    with get_connection() as conn:
        conn.execute("""INSERT INTO project
        (id,session_id,name,student,program,advisor,topic,domain,method,stage,deadline,institution,insider,language,campus,created_at,updated_at)
        VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)""",
        (pid,session_id,name,student,program,data.get('advisor'),topic,data.get('domain') or 'umum',data.get('method') or 'survey',data.get('stage') or 'start',data.get('deadline'),data.get('institution'),1 if data.get('insider') else 0,data.get('language') or 'Indonesia',data.get('campus'),now,now))
        conn.execute("INSERT INTO project_state(session_id,active_project_id) VALUES(?,?) ON CONFLICT(session_id) DO UPDATE SET active_project_id=excluded.active_project_id",(session_id,pid))
    return pid


def list_projects(session_id: str) -> List[Dict[str, Any]]:
    init_db()
    with get_connection() as conn: rows=conn.execute('SELECT * FROM project WHERE session_id=? ORDER BY updated_at DESC',(session_id,)).fetchall()
    return [dict(r) for r in rows]


def get_project_for_session(session_id: str, project_id: str) -> Optional[Dict[str, Any]]:
    init_db()
    with get_connection() as conn: row=conn.execute('SELECT * FROM project WHERE id=? AND session_id=?',(project_id,session_id)).fetchone()
    return dict(row) if row else None


def get_active_project(session_id: str) -> Optional[Dict[str, Any]]:
    init_db()
    with get_connection() as conn:
        row=conn.execute('SELECT p.* FROM project_state s JOIN project p ON p.id=s.active_project_id WHERE s.session_id=? AND p.session_id=?',(session_id,session_id)).fetchone()
        if not row: row=conn.execute('SELECT * FROM project WHERE session_id=? ORDER BY updated_at DESC LIMIT 1',(session_id,)).fetchone()
    return dict(row) if row else None


def set_active_project(session_id: str, project_id: str) -> bool:
    if not get_project_for_session(session_id,project_id): return False
    with get_connection() as conn: conn.execute("INSERT INTO project_state(session_id,active_project_id) VALUES(?,?) ON CONFLICT(session_id) DO UPDATE SET active_project_id=excluded.active_project_id",(session_id,project_id))
    return True


def update_project(session_id: str, project_id: str, changes: Dict[str, Any]) -> bool:
    allowed={'name','student','program','advisor','topic','domain','method','stage','deadline','institution','language','campus'}; vals={k:v for k,v in changes.items() if k in allowed}
    if 'insider' in changes: vals['insider']=1 if changes['insider'] else 0
    if not vals or not get_project_for_session(session_id,project_id): return False
    vals['updated_at']=_now(); sql=', '.join(f'{k}=?' for k in vals); params=list(vals.values())+[project_id,session_id]
    with get_connection() as conn: conn.execute(f'UPDATE project SET {sql} WHERE id=? AND session_id=?',params)
    return True


def get_directives(project_id: str, status_filter: Optional[str]=None) -> List[Dict[str, Any]]:
    init_db(); q='SELECT * FROM supervisor_directive WHERE project_id=?'; params=[project_id]
    if status_filter: q+=' AND status=?'; params.append(status_filter)
    q+=' ORDER BY id'
    with get_connection() as conn: rows=conn.execute(q,params).fetchall()
    return [dict(r) for r in rows]


def upsert_directives(project_id: str, directives: Iterable[Dict[str, Any]]) -> int:
    init_db(); count=0; now=_now()
    with get_connection() as conn:
        for d in directives:
            did=str(d.get('id') or '').strip(); directive=str(d.get('directive') or '').strip()
            if not did or not directive: continue
            priority=str(d.get('priority') or 'SHOULD').upper(); priority=priority if priority in {'MUST','SHOULD','NICE'} else 'SHOULD'
            status=str(d.get('status') or 'open'); status=status if status in {'open','addressed','clarify'} else 'open'
            conn.execute("""INSERT INTO supervisor_directive(project_id,id,session_label,quote,directive,priority,target_chapter,status,evidence_ref,created_at)
            VALUES(?,?,?,?,?,?,?,?,?,?) ON CONFLICT(project_id,id) DO UPDATE SET session_label=excluded.session_label,quote=excluded.quote,directive=excluded.directive,priority=excluded.priority,target_chapter=excluded.target_chapter,status=excluded.status,evidence_ref=excluded.evidence_ref""",
            (project_id,did,d.get('session_label'),d.get('quote') or '',directive,priority,d.get('target_chapter'),status,d.get('evidence_ref'),now)); count+=1
    return count


def update_directive_status(project_id: str, directive_id: str, new_status: str, evidence_ref: Optional[str]=None) -> bool:
    if new_status not in {'open','addressed','clarify'}: return False
    with get_connection() as conn: cur=conn.execute('UPDATE supervisor_directive SET status=?,evidence_ref=? WHERE project_id=? AND id=?',(new_status,evidence_ref,project_id,directive_id))
    return cur.rowcount>0


def save_gate_assessment(project_id: str, gate: str, data: Dict[str, Any]) -> None:
    with get_connection() as conn: conn.execute("INSERT INTO gate_assessment(project_id,gate,data_json,updated_at) VALUES(?,?,?,?) ON CONFLICT(project_id,gate) DO UPDATE SET data_json=excluded.data_json,updated_at=excluded.updated_at",(project_id,gate,json.dumps(data,ensure_ascii=False),_now()))


def get_gate_assessment(project_id: str, gate: str) -> Dict[str, Any]:
    with get_connection() as conn: row=conn.execute('SELECT data_json FROM gate_assessment WHERE project_id=? AND gate=?',(project_id,gate)).fetchone()
    if not row: return {}
    raw=row['data_json'] if isinstance(row,dict) or hasattr(row,'keys') else row[0]
    try: value=json.loads(raw); return value if isinstance(value,dict) else {}
    except (ValueError,TypeError): return {}


def save_source(project_id: str, source: Dict[str, Any]) -> str:
    sid=str(source.get('id') or _id('src')); authors=source.get('authors') or []; authors=authors if isinstance(authors,list) else [str(authors)]
    with get_connection() as conn: conn.execute("""INSERT INTO source(project_id,id,type,doi,url,title,authors,year,verified,verification_status,brief_json,created_at)
    VALUES(?,?,?,?,?,?,?,?,?,?,?,?) ON CONFLICT(project_id,id) DO UPDATE SET type=excluded.type,doi=excluded.doi,url=excluded.url,title=excluded.title,authors=excluded.authors,year=excluded.year,verified=excluded.verified,verification_status=excluded.verification_status,brief_json=COALESCE(excluded.brief_json,source.brief_json)""",
    (project_id,sid,source.get('type') or 'journal',source.get('doi'),source.get('url'),source.get('title') or 'Untitled',json.dumps(authors,ensure_ascii=False),source.get('year'),1 if source.get('verified') else 0,source.get('verification_status') or 'candidate',json.dumps(source.get('brief_json'),ensure_ascii=False) if source.get('brief_json') is not None else None,_now()))
    return sid


def list_sources(project_id: str, verified_only: bool=False) -> List[Dict[str, Any]]:
    q='SELECT * FROM source WHERE project_id=?'+(' AND verified=1' if verified_only else '')+' ORDER BY year DESC,title'
    with get_connection() as conn: rows=conn.execute(q,(project_id,)).fetchall()
    out=[]
    for r in rows:
        d=dict(r)
        try:d['authors']=json.loads(d.get('authors') or '[]')
        except ValueError:d['authors']=[]
        raw_brief=d.get('brief_json')
        if isinstance(raw_brief,str) and raw_brief.strip():
            try:d['brief_json']=json.loads(raw_brief)
            except ValueError: pass
        d['verified']=bool(d.get('verified')); out.append(d)
    return out


def _artifact_dict(row) -> Dict[str, Any]:
    d=dict(row)
    raw=d.get('source_refs')
    if isinstance(raw,list): refs=raw
    else:
        try: refs=json.loads(raw or '[]')
        except (ValueError,TypeError): refs=[]
    d['source_refs']=[str(x) for x in refs] if isinstance(refs,list) else []
    return d


def save_artifact(project_id: str, kind: str, title: str, content: str, source_refs: Optional[List[str]]=None) -> Dict[str, Any]:
    now=_now(); aid=_id('art'); refs=[str(x) for x in (source_refs or []) if str(x).strip()]
    try:
        from .claims import parse_draft_claims
        parsed=parse_draft_claims(content or '')
        for sentence in parsed.get('sentences',[]):
            for ref in sentence.get('references',[]):
                if ref.get('type') in {'brief','data'}:
                    rid=str(ref.get('id') or '').strip()
                    if rid and rid not in refs: refs.append(rid)
    except Exception:
        pass
    with get_connection() as conn:
        row=conn.execute('SELECT COALESCE(MAX(version),0) AS max_version FROM artifact WHERE project_id=? AND kind=? AND title=?',(project_id,kind,title)).fetchone(); version=int(row['max_version'])+1
        conn.execute('INSERT INTO artifact(id,project_id,kind,title,version,content,source_refs,created_at) VALUES(?,?,?,?,?,?,?,?)',(aid,project_id,kind,title,version,content,json.dumps(refs),now))
    return {'id':aid,'project_id':project_id,'kind':kind,'title':title,'version':version,'content':content,'source_refs':refs,'created_at':now}


def list_artifacts(project_id: str) -> List[Dict[str, Any]]:
    with get_connection() as conn: rows=conn.execute("""SELECT a.* FROM artifact a JOIN (SELECT kind,title,MAX(version) v FROM artifact WHERE project_id=? GROUP BY kind,title) latest ON a.kind=latest.kind AND a.title=latest.title AND a.version=latest.v WHERE a.project_id=? ORDER BY a.created_at DESC""",(project_id,project_id)).fetchall()
    return [_artifact_dict(r) for r in rows]


def list_artifact_versions(project_id: str, kind: str, title: str) -> List[Dict[str, Any]]:
    with get_connection() as conn: rows=conn.execute('SELECT * FROM artifact WHERE project_id=? AND kind=? AND title=? ORDER BY version DESC',(project_id,kind,title)).fetchall()
    return [_artifact_dict(r) for r in rows]


def log_ai_usage(agent: str, action: str, artifact: str='', project_id: Optional[str]=None) -> None:
    init_db()
    with get_connection() as conn: conn.execute('INSERT INTO ai_usage_log(id,project_id,ts,agent,action,artifact) VALUES(?,?,?,?,?,?)',(_id('log'),project_id,_now(),agent,action,artifact))


def storage_status() -> Dict[str, Any]:
    if _backend()=='postgres': return {'backend':'postgres','path':None,'ephemeral':False,'production_ready':True,'warning':None}
    path=_db_path(); ephemeral=str(path).startswith('/tmp/')
    return {'backend':'sqlite','path':str(path),'ephemeral':ephemeral,'production_ready':not ephemeral,'warning':'Vercel /tmp bersifat ephemeral. Set DATABASE_URL ke managed PostgreSQL untuk produksi.' if ephemeral else None}

# --- v3 complete feature helpers (no schema topology change) ---
def get_artifact(project_id: str, artifact_id: str) -> Optional[Dict[str, Any]]:
    with get_connection() as conn:
        row=conn.execute('SELECT * FROM artifact WHERE project_id=? AND id=?',(project_id,artifact_id)).fetchone()
    return _artifact_dict(row) if row else None


def save_evidence(project_id: str, source_id: str, locator: str, text: str, evidence_id: Optional[str]=None, verification: Optional[Dict[str,Any]]=None) -> str:
    """Persist evidence without changing schema.

    New rows encode verification metadata inside the existing text column. Legacy plain-text
    rows remain readable and are treated as manual/unverified.
    """
    eid=evidence_id or _id('ev')
    meta=dict(verification or {})
    status='verified' if meta.get('verified') is True else 'manual_unverified'
    payload=json.dumps({'__ata_evidence_v1__':True,'quote':str(text),'verification_status':status,'verification':meta},ensure_ascii=False)
    with get_connection() as conn:
        conn.execute('INSERT INTO evidence(project_id,id,source_id,locator,text) VALUES(?,?,?,?,?) ON CONFLICT(project_id,id) DO UPDATE SET source_id=excluded.source_id,locator=excluded.locator,text=excluded.text',(project_id,eid,source_id,locator,payload))
    return eid


def _decode_evidence_row(row) -> Dict[str,Any]:
    d=dict(row); raw=d.get('text') or ''
    try: payload=json.loads(raw)
    except (ValueError,TypeError): payload=None
    if isinstance(payload,dict) and payload.get('__ata_evidence_v1__'):
        d['text']=str(payload.get('quote') or '')
        d['verification_status']=str(payload.get('verification_status') or 'manual_unverified')
        d['verification']=payload.get('verification') if isinstance(payload.get('verification'),dict) else {}
    else:
        d['verification_status']='manual_unverified'; d['verification']={}
    return d


def list_evidence(project_id: str, source_id: Optional[str]=None) -> List[Dict[str, Any]]:
    sql='SELECT * FROM evidence WHERE project_id=?'; params=[project_id]
    if source_id is not None: sql+=' AND source_id=?'; params.append(source_id)
    sql+=' ORDER BY source_id,locator,id'
    with get_connection() as conn: rows=conn.execute(sql,params).fetchall()
    return [_decode_evidence_row(r) for r in rows]


def create_revision_task(project_id: str, directive_id: Optional[str], target_kind: str, target_title: str, before_text: str, proposed_text: str, rationale: str='') -> Dict[str, Any]:
    rid=_id('rev'); now=_now()
    with get_connection() as conn:
        conn.execute('INSERT INTO revision_task(id,project_id,directive_id,target_kind,target_title,status,before_text,proposed_text,rationale,created_at,updated_at) VALUES(?,?,?,?,?,?,?,?,?,?,?)',(rid,project_id,directive_id,target_kind,target_title,'proposed',before_text,proposed_text,rationale,now,now))
    return get_revision_task(project_id,rid) or {}


def get_revision_task(project_id: str, revision_id: str) -> Optional[Dict[str, Any]]:
    with get_connection() as conn: row=conn.execute('SELECT * FROM revision_task WHERE project_id=? AND id=?',(project_id,revision_id)).fetchone()
    return dict(row) if row else None


def list_revision_tasks(project_id: str) -> List[Dict[str, Any]]:
    with get_connection() as conn: rows=conn.execute('SELECT * FROM revision_task WHERE project_id=? ORDER BY created_at DESC',(project_id,)).fetchall()
    return [dict(r) for r in rows]


def update_revision_task_status(project_id: str, revision_id: str, status: str) -> bool:
    if status not in {'open','proposed','accepted','rejected','done'}: return False
    with get_connection() as conn: cur=conn.execute('UPDATE revision_task SET status=?,updated_at=? WHERE project_id=? AND id=?',(status,_now(),project_id,revision_id))
    return cur.rowcount>0


def save_defense_score(project_id: str, question: str, answer: str, score: int, feedback: str, weakness: str='') -> str:
    if not isinstance(score,int) or isinstance(score,bool) or score < 1 or score > 4: raise ValueError('score harus 1-4')
    did=_id('def'); payload=json.dumps({'feedback':feedback,'weakness':weakness},ensure_ascii=False)
    with get_connection() as conn: conn.execute('INSERT INTO defense_score(id,project_id,question,answer,score,feedback,created_at) VALUES(?,?,?,?,?,?,?)',(did,project_id,question,answer,score,payload,_now()))
    return did


def list_defense_scores(project_id: str, limit: int=100) -> List[Dict[str, Any]]:
    with get_connection() as conn: rows=conn.execute('SELECT * FROM defense_score WHERE project_id=? ORDER BY created_at DESC LIMIT ?',(project_id,max(1,min(int(limit),500)))).fetchall()
    out=[]
    for row in rows:
        d=dict(row); raw=d.get('feedback') or ''
        try:
            parsed=json.loads(raw)
            if isinstance(parsed,dict): d['feedback']=str(parsed.get('feedback') or ''); d['weakness']=str(parsed.get('weakness') or '')
            else: d['weakness']=''
        except (ValueError,TypeError): d['weakness']=''
        out.append(d)
    return out

# --- pre-UAT helpers using existing schema ---
def upsert_consistency_rows(project_id: str, rows: Iterable[Dict[str,Any]]) -> int:
    count=0
    with get_connection() as conn:
        for item in rows:
            if not isinstance(item,dict): continue
            element=str(item.get('element') or '').strip()
            if not element: continue
            score=item.get('score')
            if score is not None:
                try: score=int(score)
                except (TypeError,ValueError): score=None
                if score is not None and not 1 <= score <= 4: score=None
            conn.execute('''INSERT INTO consistency_row(project_id,element,content,score,critique) VALUES(?,?,?,?,?)
            ON CONFLICT(project_id,element) DO UPDATE SET content=excluded.content,score=excluded.score,critique=excluded.critique''',
            (project_id,element,str(item.get('content') or ''),score,str(item.get('critique') or '')))
            count+=1
    return count


def list_consistency_rows(project_id: str) -> List[Dict[str,Any]]:
    with get_connection() as conn:
        rows=conn.execute('SELECT * FROM consistency_row WHERE project_id=? ORDER BY element',(project_id,)).fetchall()
    return [dict(r) for r in rows]


def replace_consistency_rows(project_id: str, rows: Iterable[Dict[str,Any]]) -> int:
    """Replace the project's consistency matrix atomically so deleted UI rows cannot linger."""
    clean=[]
    for item in rows:
        if not isinstance(item,dict):
            continue
        element=str(item.get('element') or '').strip()
        if not element:
            continue
        score=item.get('score')
        if score is not None:
            try: score=int(score)
            except (TypeError,ValueError): score=None
            if score is not None and not 1 <= score <= 4: score=None
        clean.append((project_id,element,str(item.get('content') or ''),score,str(item.get('critique') or '')))
    with get_connection() as conn:
        conn.execute('DELETE FROM consistency_row WHERE project_id=?',(project_id,))
        for row in clean:
            conn.execute('INSERT INTO consistency_row(project_id,element,content,score,critique) VALUES(?,?,?,?,?)',row)
    return len(clean)
