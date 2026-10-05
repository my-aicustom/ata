"""Deterministic literature discovery helpers using OpenAlex/Crossref HTTP APIs.
The LLM never invents search results: it only synthesizes records returned here.
"""
from __future__ import annotations
import json
import urllib.parse
import urllib.request
from typing import Any, Dict, List

UA = 'ATA-v3/1.0 (academic research assistant)'


def _doi(value: Any) -> str | None:
    if not value:
        return None
    s = str(value).strip()
    for prefix in ('https://doi.org/','http://doi.org/','doi:'):
        if s.lower().startswith(prefix):
            s = s[len(prefix):]
            break
    return s or None


def normalize_openalex_work(item: Dict[str, Any]) -> Dict[str, Any]:
    authors = [a.get('author',{}).get('display_name','') for a in item.get('authorships',[]) if a.get('author',{}).get('display_name')]
    primary = item.get('primary_location') or {}
    return {
        'id': str(item.get('id') or '').rsplit('/',1)[-1] or None,
        'type': 'journal',
        'doi': _doi(item.get('doi')),
        'url': primary.get('landing_page_url') or item.get('id'),
        'title': item.get('display_name') or item.get('title') or 'Untitled',
        'authors': authors,
        'year': item.get('publication_year'),
        'verified': False,
        'verification_status': 'candidate',
        'cited_by_count': item.get('cited_by_count',0),
        'is_oa': bool((item.get('open_access') or {}).get('is_oa')),
    }


def search_openalex(query: str, per_page: int = 10) -> List[Dict[str, Any]]:
    q = urllib.parse.urlencode({'search': query, 'per-page': max(1,min(int(per_page),25))})
    req = urllib.request.Request('https://api.openalex.org/works?' + q, headers={'User-Agent': UA})
    with urllib.request.urlopen(req, timeout=15) as resp:
        data = json.loads(resp.read().decode('utf-8'))
    return [normalize_openalex_work(x) for x in data.get('results',[])]


def normalize_crossref_item(item: Dict[str, Any]) -> Dict[str, Any]:
    title = (item.get('title') or ['Untitled'])[0]
    authors = []
    for a in item.get('author') or []:
        name = ' '.join(p for p in [a.get('given',''),a.get('family','')] if p).strip()
        if name: authors.append(name)
    year = None
    for key in ('published-print','published-online','issued'):
        parts = ((item.get(key) or {}).get('date-parts') or [])
        if parts and parts[0]:
            year = parts[0][0]
            break
    return {'id': 'cr_' + str(item.get('DOI') or item.get('URL') or abs(hash(title))), 'type':'journal','doi':_doi(item.get('DOI')),'url':item.get('URL'),'title':title,'authors':authors,'year':year,'verified':False,'verification_status':'candidate'}


def search_crossref(query: str, rows: int = 10) -> List[Dict[str, Any]]:
    q = urllib.parse.urlencode({'query.bibliographic':query,'rows':max(1,min(int(rows),25))})
    req = urllib.request.Request('https://api.crossref.org/works?' + q, headers={'User-Agent': UA})
    with urllib.request.urlopen(req, timeout=15) as resp:
        data = json.loads(resp.read().decode('utf-8'))
    return [normalize_crossref_item(x) for x in data.get('message',{}).get('items',[])]


def dedupe_sources(items: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    seen=set(); out=[]
    for x in items:
        key=(x.get('doi') or '', (x.get('title') or '').strip().lower())
        if key in seen: continue
        seen.add(key); out.append(x)
    return out
