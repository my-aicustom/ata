"""Evidence-backed, method-aware quality gates for ATA v3."""
from __future__ import annotations
import json
import math
from datetime import date
from typing import Any, Dict, List
from . import db


def _number(v: Any) -> bool:
    return isinstance(v, (int, float)) and not isinstance(v, bool) and math.isfinite(v)


def _result(gate: str, name: str, checks: Dict[str, bool], metrics: Dict[str, Any]) -> Dict[str, Any]:
    checks = checks or {"Data tersedia": False}
    passed = all(bool(v) for v in checks.values())
    return {"gate": gate, "name": name, "passed": passed, "progress": round(sum(bool(v) for v in checks.values()) / len(checks) * 100), "checks": checks, "metrics": metrics, "status": "passed" if passed else "pending"}


def _all_range(values: Any, predicate) -> bool:
    vals = values if isinstance(values, list) else [values]
    return bool(vals) and all(_number(v) and predicate(float(v)) for v in vals)


def evaluate_g4_payload(method: str, data: Dict[str, Any]) -> Dict[str, Any]:
    method = (method or 'survey').replace('_', '-')
    if method == 'survey':
        checks = {
            'Loading >= 0.70': _all_range(data.get('loading'), lambda v: .70 <= v <= 1),
            'AVE >= 0.50': _all_range(data.get('ave'), lambda v: .50 <= v <= 1),
            'HTMT < 0.90': _all_range(data.get('htmt'), lambda v: 0 <= v < .90),
            'CR >= 0.70': _all_range(data.get('cr'), lambda v: .70 <= v <= 1),
        }
    elif method == 'interview':
        checks = {
            'Saturasi tercapai': data.get('saturation') is True,
            'Triangulasi >= 2 sumber': _number(data.get('triangulation_sources')) and data['triangulation_sources'] >= 2,
            'Codebook diverifikasi': data.get('codebook_verified') is True,
            'Member check': data.get('member_check') is True,
        }
    elif method == 'content-analysis':
        alpha = data.get('krippendorff_alpha')
        checks = {
            'Krippendorff alpha >= 0.80': _number(alpha) and .80 <= alpha <= 1,
            'Periode sesuai rencana': data.get('period_locked') is True,
            'Codebook terkunci': data.get('codebook_locked') is True,
        }
    elif method == 'system-experiment':
        checks = {
            'Pengulangan >= 5/skenario': _number(data.get('runs_per_scenario')) and data['runs_per_scenario'] >= 5,
            'Testbed reproducible': data.get('reproducible') is True,
            'Raw logs tersimpan': data.get('raw_logs_saved') is True,
            'Sesuai analysis plan': data.get('analysis_plan_followed') is True,
        }
    elif method == 'dsr':
        checks = {
            'Artefak terdefinisi': data.get('artifact_defined') is True,
            'Kriteria evaluasi terkunci': data.get('evaluation_criteria_locked') is True,
            'Evaluasi artefak selesai': data.get('artifact_evaluated') is True,
            'Traceability masalah-solusi': data.get('traceability_complete') is True,
        }
    else:
        checks = {
            'QC selesai': data.get('qc_complete') is True,
            'Rencana analisis diikuti': data.get('analysis_plan_followed') is True,
            'Data/hasil dapat diaudit': data.get('auditable') is True,
        }
    return _result('G4', f'Data · {method}', checks, data)


def evaluate_g1(project_id: str) -> Dict[str, Any]:
    assessment = db.get_gate_assessment(project_id, 'G1')
    scores = assessment.get('finer_scores') or {}
    keys = ['Feasible','Interesting','Novel','Ethical','Relevant']
    finer = isinstance(scores, dict) and all(_number(scores.get(k)) and 3 <= scores[k] <= 4 for k in keys)
    directives = db.get_directives(project_id)
    must = [d for d in directives if d['priority'] == 'MUST']
    addressed = sum(d['status'] == 'addressed' for d in must)
    supervisor_approved = assessment.get('supervisor_approved') is True
    return _result('G1','Topik & scoping',{
        'FINER >= 3': finer,
        'Semua MUST addressed': bool(must) and addressed == len(must),
        'Disetujui pembimbing': supervisor_approved,
    }, {'finer_scores': scores, 'must_directives': f'{addressed}/{len(must)}'})


def evaluate_g2(project_id: str) -> Dict[str, Any]:
    assessment = db.get_gate_assessment(project_id, 'G2')
    sources = db.list_sources(project_id, verified_only=True)
    min_sources = int(assessment.get('min_sources') or 20)
    recent_ratio_target = float(assessment.get('recent_ratio_target') or .60)
    recent = 0
    year = date.today().year
    for s in sources:
        y = s.get('year')
        recent += bool(y and year - 10 <= int(y) <= year)
    ratio = recent / len(sources) if sources else 0
    checks = {
        f'>= {min_sources} sumber terverifikasi': len(sources) >= min_sources,
        f'>= {round(recent_ratio_target*100)}% 10 tahun terakhir': ratio >= recent_ratio_target,
        'Research gap tertulis': assessment.get('research_gap_ready') is True,
        'Kerangka/model tergambar': assessment.get('framework_ready') is True,
    }
    return _result('G2','Literatur terverifikasi',checks,{'verified_sources':len(sources),'recent_ratio':round(ratio*100,1)})


def evaluate_g3(project_id: str) -> Dict[str, Any]:
    assessment = db.get_gate_assessment(project_id, 'G3')
    with db.get_connection() as conn:
        rows = conn.execute('SELECT element,score FROM consistency_row WHERE project_id=?',(project_id,)).fetchall()
    matrix_ok = bool(rows) and all(_number(r['score']) and r['score'] >= 3 for r in rows)
    checks = {
        'Matriks konsistensi >= 3': matrix_ok,
        'Instrumen/izin siap': assessment.get('instrument_ready') is True,
        'Analysis plan dikunci': assessment.get('analysis_plan_locked') is True,
        'Proposal disetujui/lolos': assessment.get('proposal_approved') is True,
    }
    return _result('G3','Proposal & metode',checks,{'consistency_rows':len(rows)})


def evaluate_g4(project_id: str, method: str) -> Dict[str, Any]:
    return evaluate_g4_payload(method, db.get_gate_assessment(project_id, 'G4'))


def evaluate_g5(project_id: str) -> Dict[str, Any]:
    data = db.get_gate_assessment(project_id, 'G5')
    zero_keys = ['invalid_citations','manual_refs_pending','unsupported_claims','open_red_critiques']
    checks = {k.replace('_',' '): _number(data.get(k)) and data[k] == 0 for k in zero_keys}
    checks['Similarity di bawah ambang'] = (_number(data.get('similarity')) and _number(data.get('similarity_threshold')) and 0 <= data['similarity'] < data['similarity_threshold'] <= 100)
    must = [d for d in db.get_directives(project_id) if d['priority'] == 'MUST']
    checks['Semua MUST addressed'] = bool(must) and all(d['status'] == 'addressed' for d in must)
    return _result('G5','Integritas draf final',checks,data)


def evaluate_g6(project_id: str) -> Dict[str, Any]:
    data = db.get_gate_assessment(project_id, 'G6')
    scores = data.get('question_scores') or []
    scores = scores if isinstance(scores,list) else []
    strong = sum(_number(v) and 3 <= v <= 4 for v in scores)
    ratio = strong / len(scores) if scores else 0
    return _result('G6','Kesiapan sidang',{'80% jawaban skor >= 3': ratio >= .8},{'answered_strong':strong,'total':len(scores),'mock_score':round(ratio*100,1)})


def get_all_gates(project_id: str, method: str) -> List[Dict[str, Any]]:
    return [evaluate_g1(project_id),evaluate_g2(project_id),evaluate_g3(project_id),evaluate_g4(project_id,method),evaluate_g5(project_id),evaluate_g6(project_id)]
