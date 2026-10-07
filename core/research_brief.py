"""Research-brief parsing and deterministic quote verification."""
from __future__ import annotations
import json
import re
from typing import Any, Dict, List
from .evidence import verify_quote_in_document


def parse_research_brief(text: str) -> Dict[str,Any]:
    raw=str(text or '').strip()
    raw=re.sub(r'^```(?:json)?\s*|\s*```$','',raw,flags=re.I|re.S).strip()
    a=raw.find('{'); b=raw.rfind('}')
    if a<0 or b<=a: raise ValueError('Research Brief tidak memuat JSON object')
    data=json.loads(raw[a:b+1])
    if not isinstance(data,dict): raise ValueError('Research Brief harus object')
    quotes=data.get('quotes') or []
    if not isinstance(quotes,list): quotes=[]
    clean=[]
    for q in quotes:
        if not isinstance(q,dict): continue
        locator=str(q.get('locator') or '').strip(); quote=str(q.get('text') or q.get('quote') or '').strip()
        if locator and quote: clean.append({'locator':locator,'text':quote})
    data['quotes']=clean
    for key in ('summary','method'):
        if key in data: data[key]=str(data.get(key) or '').strip()
    for key in ('findings','limitations','relevance','keywords'):
        if key in data and not isinstance(data[key],list): data[key]=[str(data[key])]
    return data


def verify_brief_quotes(brief: Dict[str,Any], source_text: str) -> Dict[str,Any]:
    verified=[]; rejected=[]
    for q in brief.get('quotes') or []:
        verification=verify_quote_in_document(q['text'],source_text,q['locator'])
        row={**q,'verification':verification}
        (verified if verification.get('verified') else rejected).append(row)
    return {'verified':verified,'rejected':rejected}
