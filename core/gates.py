"""Evidence-backed gates. Store manual measurements in gate_assessment JSON.
G1: finer_scores; G4: loading/ave/htmt/cr (scalar or arrays);
G5: invalid_citations/unsupported_claims/open_red_critiques/similarity/similarity_threshold;
G6: question_scores, including null for unanswered questions.
Source brief_json uses explicit core_book/international/sinta boolean metadata.
"""
import json
import math
import sqlite3
from datetime import date
from pathlib import Path
DB_PATH = str(Path(__file__).with_name('ata_v2.db'))

class _Connection(sqlite3.Connection):
    def __exit__(self, *args):
        try:
            return super().__exit__(*args)
        finally:
            self.close()

def get_db():
    conn = sqlite3.connect(DB_PATH, factory=_Connection)
    conn.row_factory = sqlite3.Row
    return conn

def _assessment(gate):
    with get_db() as conn:
        conn.execute('CREATE TABLE IF NOT EXISTS gate_assessment (gate TEXT PRIMARY KEY, data_json TEXT NOT NULL)')
        row = conn.execute('SELECT data_json FROM gate_assessment WHERE gate=?', (gate,)).fetchone()
    try:
        data = json.loads(row[0]) if row else {}
        return data if isinstance(data, dict) else {}
    except (ValueError, TypeError):
        return {}

def _number(v):
    return isinstance(v, (int, float)) and not isinstance(v, bool) and math.isfinite(v)

def _result(gate, name, checks, metrics):
    passed = all(checks.values())
    return dict(gate=gate, name=name, description=name, passed=passed,
                progress=round(sum(checks.values()) / len(checks) * 100), checks=checks,
                metrics=metrics, status='passed' if passed else 'pending')

def evaluate_g1():
    scores = _assessment('G1').get('finer_scores', {})
    keys = ['Feasible', 'Interesting', 'Novel', 'Ethical', 'Relevant']
    finer = isinstance(scores, dict) and all(_number(scores.get(k)) and 3 <= scores[k] <= 4 for k in keys)
    with get_db() as conn:
        rows = conn.execute("SELECT status FROM supervisor_directive WHERE priority='MUST'").fetchall()
    addressed = sum(r['status'] == 'addressed' for r in rows)
    return _result('G1', 'Topik & scoping', {'FINER >= 3': finer, 'Semua MUST addressed': bool(rows) and addressed == len(rows)},
                   {'finer_scores': scores, 'must_directives': f'{addressed}/{len(rows)}'})

def evaluate_g2():
    with get_db() as conn:
        rows = conn.execute('SELECT * FROM source WHERE verified=1').fetchall()
    recent = books = international = sinta = 0
    year = date.today().year
    for row in rows:
        recent += bool(row['year'] and year - 10 <= row['year'] <= year)
        try:
            meta = json.loads(row['brief_json'] or '{}')
            if not isinstance(meta, dict): meta = {}
        except ValueError: meta = {}
        books += row['type'] == 'book' and meta.get('core_book') is True
        international += row['type'] == 'journal' and meta.get('international') is True
        sinta += row['type'] == 'journal' and meta.get('sinta') is True
    ratio = recent / len(rows) if rows else 0
    return _result('G2', 'Literatur terverifikasi', {'30 sumber': len(rows) >= 30, '60% dalam 10 tahun': ratio >= .6,
                   '5 buku inti': books >= 5, '10 jurnal internasional': international >= 10, '5 SINTA': sinta >= 5},
                   dict(verified_sources=len(rows), recent_ratio=round(ratio * 100, 1), core_books=books, international_journals=international, sinta_journals=sinta))

def evaluate_g3():
    with get_db() as conn:
        rows = conn.execute('SELECT element, score FROM consistency_row').fetchall()
    checks = {r['element']: _number(r['score']) and r['score'] >= 3 for r in rows} or {'Matriks tersedia': False}
    return _result('G3', 'Matriks konsistensi', checks, {'consistency_rows': f'{sum(checks.values())}/{len(rows)}'})

def evaluate_g4():
    data = _assessment('G4')
    checks = {}
    for key, threshold in [('loading', .7), ('ave', .5), ('htmt', .9), ('cr', .7)]:
        values = data.get(key)
        values = values if isinstance(values, list) else [values]
        checks[key] = bool(values) and all(_number(v) and 0 <= v <= 1 and (v < threshold if key == 'htmt' else v >= threshold) for v in values)
    return _result('G4', 'Validitas & reliabilitas', checks, data)

def evaluate_g5():
    data = _assessment('G5')
    checks = {k: _number(data.get(k)) and data[k] == 0 for k in ['invalid_citations', 'unsupported_claims', 'open_red_critiques']}
    checks['Similarity di bawah ambang'] = (_number(data.get('similarity')) and _number(data.get('similarity_threshold'))
        and 0 <= data['similarity'] < data['similarity_threshold'] <= 100)
    return _result('G5', 'Integritas draf final', checks, data)

def evaluate_g6():
    scores = _assessment('G6').get('question_scores', [])
    scores = scores if isinstance(scores, list) else []
    answered = sum(_number(v) and 3 <= v <= 4 for v in scores)
    ratio = answered / len(scores) if scores else 0
    return _result('G6', 'Kesiapan sidang', {'80% jawaban skor >= 3': ratio >= .8},
                   dict(answered=answered, total_questions=len(scores), mock_score=round(ratio * 100, 1)))

def get_all_gates():
    return [evaluate_g1(), evaluate_g2(), evaluate_g3(), evaluate_g4(), evaluate_g5(), evaluate_g6()]
