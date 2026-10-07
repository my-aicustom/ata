"""Data-intake policy for thesis files before any cloud processing."""
from __future__ import annotations
import re
from typing import Any, Dict

_ALLOWED={'public','internal-authorized','confidential'}
_ALIASES={
    'publik':'public','public':'public',
    'internal':'internal-authorized','internal-authorized':'internal-authorized','internal_authorized':'internal-authorized','internal authorized':'internal-authorized',
    'rahasia':'confidential','confidential':'confidential','private':'confidential',
}


def normalize_classification(value: str|None) -> str:
    key=str(value or 'internal-authorized').strip().lower()
    result=_ALIASES.get(key,key)
    if result not in _ALLOWED:
        raise ValueError('classification harus public, internal-authorized, atau confidential')
    return result


def decide_intake(classification: str|None, media_type: str|None='', filename: str|None='') -> Dict[str,Any]:
    cls=normalize_classification(classification)
    mtype=str(media_type or '').strip().lower()
    cloud=cls in {'public','internal-authorized'}
    return {
        'classification':cls,
        'local_allowed':True,
        'cloud_allowed':cloud,
        'requires_redaction':cls=='internal-authorized',
        'media_type':mtype,
        'filename':str(filename or ''),
        'reason':('Rahasia: file hanya boleh diproses lokal dan tidak boleh dikirim ke provider cloud.' if cls=='confidential'
                  else 'Internal-authorized: cloud diizinkan setelah pengguna berwenang dan data sensitif diminimalkan.' if cls=='internal-authorized'
                  else 'Publik: cloud processing diizinkan.'),
    }


def redact_personal_data(text: str) -> str:
    """Best-effort minimization for internal-authorized text before model calls.

    This is intentionally conservative and not presented as a full anonymizer.
    """
    value=str(text or '')
    value=re.sub(r'(?i)\b[A-Z0-9._%+-]+@[A-Z0-9.-]+\.[A-Z]{2,}\b','[EMAIL]',value)
    value=re.sub(r'(?<!\d)(?:\+62|62|0)8\d{7,12}(?!\d)','[TELEPON]',value)
    value=re.sub(r'(?i)\bNIP\s*[:.]?\s*\d{8,20}\b','NIP [DIHAPUS]',value)
    value=re.sub(r'(?i)\bNIK\s*[:.]?\s*\d{16}\b','NIK [DIHAPUS]',value)
    return value
