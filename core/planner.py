"""Outcome-driven thesis planner: user sees the next action, not internal agents."""
from __future__ import annotations
from typing import Any, Dict


def next_best_action(state: Dict[str, Any]) -> Dict[str, Any]:
    gates = state.get('gates') or {}
    open_must = int(state.get('open_must') or 0)
    if not (gates.get('G1') or {}).get('passed'):
        reason = 'Selesaikan arahan pembimbing yang wajib dan kunci judul/rumusan masalah sebelum menambah literatur.' if open_must else 'Judul dan rumusan masalah belum melewati G1.'
        return {"phase": 1, "role": "topic_framer", "label": "Kunci judul & rumusan masalah", "reason": reason, "eta_minutes": 60}
    if not (gates.get('G2') or {}).get('passed'):
        return {"phase": 2, "role": "source_finder", "label": "Lengkapi bukti & research gap", "reason": "Literatur belum memenuhi komposisi dan verifikasi yang dibutuhkan.", "eta_minutes": 75}
    if not (gates.get('G3') or {}).get('passed'):
        return {"phase": 3, "role": "method_fit", "label": "Kunci metode & proposal", "reason": "Matriks konsistensi, instrumen, atau rencana analisis belum siap.", "eta_minutes": 75}
    if not (gates.get('G4') or {}).get('passed'):
        return {"phase": 4, "role": "method_fit", "label": "Selesaikan data & quality control", "reason": "Data belum memenuhi kriteria Method Pack aktif.", "eta_minutes": 90}
    if not (gates.get('G5') or {}).get('passed'):
        return {"phase": 5, "role": "drafting_assistant", "label": "Tutup gap draf & bukti", "reason": "Masih ada sitasi, klaim, kritik, atau similarity yang belum lolos G5.", "eta_minutes": 90}
    if not (gates.get('G6') or {}).get('passed'):
        return {"phase": 7, "role": "mock_examiner", "label": "Latihan sidang dari titik terlemah", "reason": "Naskah siap; prioritas sekarang kemampuan mempertahankan keputusan penelitian.", "eta_minutes": 45}
    return {"phase": 7, "role": "defense_pack", "label": "Siap sidang", "reason": "Semua gate utama sudah lolos. Fokus pada konsistensi dan kesiapan hari-H.", "eta_minutes": 30}
