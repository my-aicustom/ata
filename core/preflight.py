"""Runtime readiness checks that do not perform paid/live provider calls."""
from __future__ import annotations
import importlib.util
import os
from pathlib import Path
from typing import Any, Dict
from . import db


def runtime_preflight() -> Dict[str,Any]:
    packages={
        'yaml':'pyyaml','requests':'requests','docx':'python-docx','pypdf':'pypdf','fitz':'PyMuPDF'
    }
    checks=[]
    for module,label in packages.items():
        ok=importlib.util.find_spec(module) is not None
        checks.append({'name':f'dependency:{label}','ok':ok,'detail':'installed' if ok else 'missing'})
    storage=db.storage_status()
    try:
        if storage.get('backend')=='sqlite':
            p=Path(storage['path']); p.parent.mkdir(parents=True,exist_ok=True); test=p.parent/'.ata-write-test'; test.write_text('ok'); test.unlink(); writable=True
        else: writable=True
    except Exception as e:
        writable=False; storage={**storage,'warning':str(e)}
    checks.append({'name':'storage:writable','ok':writable,'detail':storage.get('backend')})
    code_ready=all(x['ok'] for x in checks)
    provider_configured=bool(os.getenv('OPENROUTER_API_KEY'))
    live=[]
    if not provider_configured: live.append('Set OPENROUTER_API_KEY lalu jalankan smoke test text/vision/audio.')
    else: live.append('Jalankan smoke test OpenRouter text/vision/audio dengan credential environment Anda.')
    live.append('Hubungkan PostgreSQL/PostgREST VPS Anda dan jalankan persistence/isolation test di environment lokal.')
    live.append('Jalankan satu tesis asli end-to-end sebagai UAT sebelum release publik.')
    return {
        'code_ready':code_ready,
        'provider_configured':provider_configured,
        'storage':storage,
        'checks':checks,
        'live_tests_remaining':live,
    }
