"""Normalize structured supervisor directions produced from notes/transcripts."""
from __future__ import annotations
import json
import re
from typing import Any, Dict, List


def _json_value(text: str) -> Any:
    raw=str(text or '').strip()
    raw=re.sub(r'^```(?:json)?\s*|\s*```$','',raw,flags=re.I|re.S).strip()
    for opener,closer in [('[',']'),('{','}')]:
        a=raw.find(opener); b=raw.rfind(closer)
        if a>=0 and b>a:
            try: return json.loads(raw[a:b+1])
            except json.JSONDecodeError: pass
    raise ValueError('Output ekstraksi arahan tidak memuat JSON valid')


def normalize_directives(text: str, prefix: str='SV') -> List[Dict[str,Any]]:
    data=_json_value(text)
    if isinstance(data,dict): data=data.get('directives') or data.get('items') or [data]
    if not isinstance(data,list): raise ValueError('Output arahan harus berupa list')
    out=[]
    for i,item in enumerate(data,1):
        if not isinstance(item,dict): continue
        directive=str(item.get('directive') or item.get('instruction') or '').strip()
        if not directive: continue
        priority=str(item.get('priority') or 'SHOULD').upper().strip()
        if priority not in {'MUST','SHOULD','NICE'}: priority='SHOULD'
        status=str(item.get('status') or 'open').lower().strip()
        if status not in {'open','addressed','clarify'}: status='open'
        did=str(item.get('id') or f'{prefix}-{i:02d}').strip()[:80]
        out.append({
            'id':did,
            'session_label':str(item.get('session_label') or item.get('session') or '').strip(),
            'quote':str(item.get('quote') or '').strip(),
            'directive':directive,
            'priority':priority,
            'target_chapter':str(item.get('target_chapter') or item.get('target') or '').strip(),
            'status':status,
            'evidence_ref':item.get('evidence_ref'),
        })
    if not out: raise ValueError('Tidak ada arahan valid yang berhasil diekstrak')
    return out
