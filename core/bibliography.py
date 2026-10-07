"""Deterministic bibliography helpers from ATA source metadata.

This is intentionally metadata-preserving, not a claim that every campus citation style
is reproduced perfectly. BibTeX is provided so users can hand formatting to Zotero/CSL.
"""
from __future__ import annotations
import re
from typing import Any, Dict, Iterable, List

_DATA_TYPES={'dataset','data','analysis-output','statistical-output','experiment-output','transcript'}


def is_bibliographic_source(source: Dict[str,Any]) -> bool:
    return str(source.get('type') or '').strip().lower() not in _DATA_TYPES


def _key(source: Dict[str,Any], index: int=1) -> str:
    raw=str(source.get('id') or f'source{index}')
    key=re.sub(r'[^A-Za-z0-9_:-]+','_',raw).strip('_')
    return key or f'source{index}'


def _bib_value(value: Any) -> str:
    return str(value or '').replace('\\','\\\\').replace('{','\\{').replace('}','\\}')


def source_to_bibtex(source: Dict[str,Any], index: int=1) -> str:
    stype=str(source.get('type') or 'document').lower()
    entry='article' if stype=='journal' else ('book' if stype=='book' else 'misc')
    fields=[]
    title=str(source.get('title') or '').strip()
    authors=source.get('authors') or []
    if not isinstance(authors,list): authors=[str(authors)]
    if title: fields.append(('title',title))
    if authors: fields.append(('author',' and '.join(str(a) for a in authors if str(a).strip())))
    if source.get('year'): fields.append(('year',source.get('year')))
    if source.get('doi'): fields.append(('doi',source.get('doi')))
    if source.get('url'): fields.append(('url',source.get('url')))
    lines=[f'@{entry}{{{_key(source,index)},']
    for name,value in fields:
        lines.append(f'  {name} = {{{_bib_value(value)}}},')
    if len(lines)>1: lines[-1]=lines[-1].rstrip(',')
    lines.append('}')
    return '\n'.join(lines)


def build_bibtex(sources: Iterable[Dict[str,Any]]) -> str:
    usable=[s for s in sources if is_bibliographic_source(s)]
    return '\n\n'.join(source_to_bibtex(s,i+1) for i,s in enumerate(usable)) + ('\n' if usable else '')


def reference_text(source: Dict[str,Any]) -> str:
    authors=source.get('authors') or []
    if not isinstance(authors,list): authors=[str(authors)]
    author_text=', '.join(str(a).strip() for a in authors if str(a).strip()) or 'Tanpa nama'
    year=str(source.get('year') or 't.t.')
    title=str(source.get('title') or 'Tanpa judul').strip()
    tail=''
    if source.get('doi'): tail=f" https://doi.org/{str(source['doi']).replace('https://doi.org/','')}"
    elif source.get('url'): tail=' '+str(source['url'])
    return f'{author_text}. ({year}). {title}.{tail}'.strip()


def referenced_bibliography(artifacts: Iterable[Dict[str,Any]], sources: Iterable[Dict[str,Any]]) -> List[Dict[str,Any]]:
    refs=[]
    for artifact in artifacts:
        for rid in artifact.get('source_refs') or []:
            rid=str(rid)
            if rid not in refs: refs.append(rid)
    by_id={str(s.get('id')):s for s in sources}
    selected=[by_id[rid] for rid in refs if rid in by_id and is_bibliographic_source(by_id[rid])]
    return sorted(selected,key=lambda s:((s.get('authors') or [''])[0] if isinstance(s.get('authors'),list) and s.get('authors') else '',str(s.get('title') or '')))
