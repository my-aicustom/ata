"""Deterministic claim-to-evidence resolution and document-backed quote verification."""
from __future__ import annotations
import hashlib
import re
import unicodedata
from typing import Any, Dict
from . import db
from .claims import parse_draft_claims


def _norm(value: str|None) -> str:
    return re.sub(r'\s+',' ',str(value or '').strip().lower().replace('https://doi.org/',''))


def _norm_quote(value: str|None) -> str:
    text=unicodedata.normalize('NFKC',str(value or '')).replace('\u00ad','')
    text=re.sub(r'-\s*\n\s*','',text)
    text=text.replace('“','"').replace('”','"').replace('’',"'").replace('‘',"'")
    return re.sub(r'\s+',' ',text).strip().lower()


def _page_number(locator: str) -> int|None:
    m=re.search(r'(?i)(?:hal(?:aman)?|page|p\.?)[\s.:#-]*(\d+)',str(locator or ''))
    return int(m.group(1)) if m else None


def _pdf_pages(source_text: str) -> Dict[int,str]:
    matches=list(re.finditer(r'(?im)^\[PAGE\s+(\d+)\]\s*$',str(source_text or '')))
    if not matches: return {}
    out={}
    for i,m in enumerate(matches):
        start=m.end(); end=matches[i+1].start() if i+1<len(matches) else len(source_text)
        out[int(m.group(1))]=source_text[start:end].strip()
    return out


def verify_quote_in_document(quote: str, source_text: str, locator: str='') -> Dict[str,Any]:
    """Verify that a quote exists in the supplied source, constrained to a PDF page when possible."""
    nq=_norm_quote(quote); doc=str(source_text or '')
    base={'verified':False,'status':'unverified','locator':str(locator or ''),'source_sha256':hashlib.sha256(doc.encode('utf-8')).hexdigest() if doc else ''}
    if len(nq)<12: return {**base,'reason':'quote_too_short'}
    if not doc.strip(): return {**base,'reason':'source_document_empty'}
    page=_page_number(locator); pages=_pdf_pages(doc)
    if page is not None:
        if not pages: return {**base,'reason':'page_locator_unverifiable_without_pdf_page_markers','page':page}
        if page not in pages: return {**base,'reason':'page_not_found','page':page}
        haystack=pages[page]; method='exact_normalized_page_match'
    else:
        haystack=doc; method='exact_normalized_document_match'
    ok=nq in _norm_quote(haystack)
    if not ok: return {**base,'reason':'quote_not_found','page':page}
    return {**base,'verified':True,'status':'verified','method':method,'page':page,'matched_text':str(quote).strip()}


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
                matches=sorted(matches,key=lambda e:e.get('verification_status')!='verified')
                chosen=matches[0] if matches else None
                ev_verified=bool(chosen and chosen.get('verification_status')=='verified')
                ver=(chosen or {}).get('verification') or {}
                source_verified=bool(source.get('verified'))
                has_doi=bool(str(source.get('doi') or '').strip())
                document_backed=bool(ev_verified and ver.get('source_sha256'))
                if has_doi:
                    ok=source_verified and ev_verified
                    support_basis='doi_verified' if ok else 'incomplete_doi_chain'
                else:
                    ok=document_backed
                    support_basis='document_backed' if ok else 'manual_unverified'
                resolved.append({
                    'type':'brief','source_id':source['id'],'title':source.get('title'),
                    'locator':chosen['locator'] if chosen else locator,
                    'evidence_id':chosen['id'] if chosen else None,
                    'evidence_text':chosen['text'] if chosen else None,
                    'verified':ok,'source_verified':source_verified,
                    'source_traceable':document_backed,
                    'bibliographic_status':source.get('verification_status') or 'candidate',
                    'support_basis':support_basis,
                    'verification_status':(chosen or {}).get('verification_status','missing'),
                    'verification_method':ver.get('method'),'source_sha256':ver.get('source_sha256'),
                })
                verified_flags.append(ok)
            elif rtype=='ledger':
                d=directives.get(rid); ok=bool(d and d.get('status')=='addressed' and d.get('evidence_ref'))
                resolved.append({'type':'ledger','directive_id':rid,'locator':d.get('evidence_ref') if d else None,'verified':ok}); verified_flags.append(ok)
            elif rtype=='data':
                source=source_map.get(_norm(rid))
                if not source:
                    resolved.append({'type':'data','source_id':rid,'locator':locator,'verified':False,'reason':'data_source_not_found'}); verified_flags.append(False); continue
                matches=by_source.get(source['id'],[])
                if locator: matches=[e for e in matches if _norm(e.get('locator'))==_norm(locator)]
                elif len(matches)==1: matches=matches[:1]
                matches=sorted(matches,key=lambda e:e.get('verification_status')!='verified')
                chosen=matches[0] if matches else None
                ver=(chosen or {}).get('verification') or {}
                document_backed=bool(chosen and chosen.get('verification_status')=='verified' and ver.get('source_sha256'))
                ok=document_backed
                resolved.append({
                    'type':'data','source_id':source['id'],'title':source.get('title'),'locator':chosen['locator'] if chosen else locator,
                    'evidence_id':chosen['id'] if chosen else None,'evidence_text':chosen['text'] if chosen else None,
                    'verified':ok,'support_basis':'data_document_backed' if ok else 'manual_unverified',
                    'verification_status':(chosen or {}).get('verification_status','missing'),'verification_method':ver.get('method'),
                    'source_sha256':ver.get('source_sha256'),
                }); verified_flags.append(ok)
            else:
                resolved.append({'type':rtype,'id':rid,'locator':locator,'verified':False,'reason':'unsupported_reference_type'}); verified_flags.append(False)
        if not sentence.get('references'):
            if sentence.get('requires_evidence',True):
                status='unsupported'; unsupported+=1
            else:
                status='not_required'
        elif verified_flags and all(verified_flags):
            status='supported'; supported+=1
        else:
            status='partial'; partial+=1
        sentence['status']=status; sentence['evidence_verified']=status=='supported'; sentence['resolved']=resolved
    required=sum(1 for x in result['sentences'] if x.get('requires_evidence',True) or x.get('references'))
    result['compliance']['supported_claims']=supported
    result['compliance']['partial_claims']=partial
    result['compliance']['unsupported_claims']=unsupported
    result['compliance']['required_claims']=required
    result['compliance']['verified_score']=round(supported/max(1,required)*100,1) if required else 100.0
    result['note']='Supported berarti rantai bukti konten lengkap: sumber DOI memerlukan metadata DOI terverifikasi + quote dokumen terverifikasi; sumber non-DOI dapat didukung oleh exact quote + hash dokumen (document-backed). Metadata bibliografi non-DOI tetap dilaporkan terpisah; input manual tanpa dokumen tetap partial.'
    return result
