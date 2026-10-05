"""Deterministic claim-to-evidence resolution."""
from __future__ import annotations
import re
from typing import Any, Dict
from . import db
from .claims import parse_draft_claims


def _norm(value: str|None) -> str:
    return re.sub(r'\s+',' ',str(value or '').strip().lower().replace('https://doi.org/',''))


def resolve_draft_evidence(project_id: str, text: str) -> Dict[str,Any]:
    result=parse_draft_claims(text)
    sources=db.list_sources(project_id)
    source_map={_norm(s['id']):s for s in sources}
    for s in sources:
        if s.get('doi'): source_map[_norm(s['doi'])]=s
    evidences=db.list_evidence(project_id)
    by_source={}
    for ev in evidences: by_source.setdefault(ev['source_id'],[]).append(ev)
    directives={d['id']:d for d in db.get_directives(project_id)}
    supported=partial=unsupported=0
    for sentence in result['sentences']:
        resolved=[]; verified_flags=[]
        for ref in sentence.get('references',[]):
            rtype=ref.get('type'); rid=str(ref.get('id') or '')
            locator=str(ref.get('locator') or '')
            if rtype=='brief':
                source=source_map.get(_norm(rid))
                if not source:
                    resolved.append({'type':'brief','source_id':rid,'locator':locator,'verified':False,'reason':'source_not_found'}); verified_flags.append(False); continue
                matches=by_source.get(source['id'],[])
                if locator: matches=[e for e in matches if _norm(e.get('locator'))==_norm(locator)]
                elif len(matches)==1: matches=matches[:1]
                ok=bool(source.get('verified')) and bool(matches)
                resolved.append({'type':'brief','source_id':source['id'],'title':source.get('title'),'locator':matches[0]['locator'] if matches else locator,'evidence_id':matches[0]['id'] if matches else None,'evidence_text':matches[0]['text'] if matches else None,'verified':ok,'source_verified':bool(source.get('verified'))})
                verified_flags.append(ok)
            elif rtype=='ledger':
                d=directives.get(rid); ok=bool(d and d.get('status')=='addressed' and d.get('evidence_ref'))
                resolved.append({'type':'ledger','directive_id':rid,'locator':d.get('evidence_ref') if d else None,'verified':ok}); verified_flags.append(ok)
            else:
                resolved.append({'type':rtype,'id':rid,'locator':locator,'verified':False,'reason':'manual_data_verification_required'}); verified_flags.append(False)
        if not sentence.get('references'):
            status='unsupported'; unsupported+=1
        elif verified_flags and all(verified_flags):
            status='supported'; supported+=1
        else:
            status='partial'; partial+=1
        sentence['status']=status; sentence['evidence_verified']=status=='supported'; sentence['resolved']=resolved
    result['compliance']['supported_claims']=supported
    result['compliance']['partial_claims']=partial
    result['compliance']['unsupported_claims']=unsupported
    result['compliance']['verified_score']=round(supported/max(1,len(result['sentences']))*100,1)
    result['note']='Supported berarti seluruh referensi pada klaim terhubung ke bukti yang terverifikasi; partial berarti referensi ada tetapi rantai bukti belum lengkap.'
    return result
