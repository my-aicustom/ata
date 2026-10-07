"""Conservative sentence audit with evidence-need heuristics.

A sentence is not automatically an unsupported claim just because it has no citation.
ATA distinguishes self/structural statements from factual claims that need evidence.
"""
from __future__ import annotations
import re

_SELF_PATTERNS=(
    r'^penelitian ini (?:bertujuan|menggunakan|menganalisis|menguji|membahas|dibatasi|difokuskan|disusun)',
    r'^tujuan penelitian (?:ini )?(?:adalah|yaitu|untuk)',
    r'^rumusan masalah (?:penelitian )?(?:ini )?',
    r'^bab (?:ini|[ivx]+) (?:membahas|menjelaskan|menguraikan|menyajikan)',
    r'^pada penelitian ini[, ]',
    r'^peneliti (?:menggunakan|memilih|membatasi|menetapkan|menganalisis)',
    r'^hipotesis penelitian (?:ini )?',
)
_FACTUAL_MARKERS=(
    r'\b\d+(?:[.,]\d+)?\s*%', r'\b(?:19|20)\d{2}\b', r'\b(?:sebesar|sebanyak|meningkat|menurun|kenaikan|penurunan)\b',
    r'\b(?:data|hasil penelitian|studi|survei|laporan|statistik)\b.*\b(?:menunjukkan|menemukan|mencatat|mengindikasikan|menyatakan)\b',
    r'\b(?:menurut|berdasarkan)\b', r'\b(?:signifikan|koefisien|p-value|r-square|r²|loading|ave|htmt|cronbach|reliabilitas|validitas)\b',
)


def _requires_evidence(sentence: str, refs, explicit_missing: bool) -> bool:
    if explicit_missing or refs: return True
    clean=re.sub(r'\((?:M\+AI|AI|M)\)','',sentence,flags=re.I).strip().lower()
    if any(re.search(p,clean,re.I) for p in _SELF_PATTERNS): return False
    if any(re.search(p,clean,re.I) for p in _FACTUAL_MARKERS): return True
    # Interpretive/argumentative prose without an explicit external-data marker is not
    # auto-failed; Critic/Advisor gates can still challenge it substantively.
    return False


def parse_draft_claims(text):
    records=[]; counts={'student':0,'ai_expanded':0,'ai_suggested':0}
    for pidx,paragraph in enumerate(re.split(r'\n\s*\n',str(text or '').strip()),1):
        if not paragraph.strip(): continue
        tags=re.findall(r'\((M\+AI|AI|M)\)',paragraph,re.I); inherited=tags[0].upper() if tags else 'M'
        protected=re.sub(r'\[[^\]]*\]',lambda m:m[0].replace('.','\uE000'),paragraph)
        protected=re.sub(r'(?<=\d)\.(?=\d)','\uE000',protected)
        protected=re.sub(r'\b(?:Dr|Prof|No|et al)\.',lambda m:m[0].replace('.','\uE000'),protected)
        chunks=re.findall(r'.*?[.!?](?:\s*\[(?:Brief|Ledger|Data):[^\]]+\]|\s*\[(?:PERLU SUMBER|BELUM DIVERIFIKASI)\])*(?=\s+|$)|.+$',protected.strip(),re.I|re.S)
        for sidx,sentence in enumerate(chunks,1):
            sentence=sentence.replace('\uE000','.').strip()
            if not sentence: continue
            tag=re.search(r'\((M\+AI|AI|M)\)',sentence,re.I)
            if tag: inherited=tag.group(1).upper()
            origin={'M':'student','M+AI':'ai_expanded','AI':'ai_suggested'}[tag.group(1).upper() if tag else inherited]; counts[origin]+=1
            refs=[]
            for m in re.finditer(r'\[(Brief|Ledger|Data):\s*([^\]]+)\]',sentence,re.I):
                raw=m.group(2).strip(); parts=re.split(r',\s*(?=hal(?:aman)?\.?|p\.?|page\s|bab\s|bagian\s|section\s|dokumen\b|tabel\s|table\s|lampiran\s)',raw,maxsplit=1,flags=re.I)
                refs.append({'type':m.group(1).lower(),'id':parts[0].strip(),'locator':parts[1].strip() if len(parts)>1 else ''})
            explicit_missing=bool(re.search(r'\[(PERLU SUMBER|BELUM DIVERIFIKASI)\]',sentence,re.I))
            needs=_requires_evidence(sentence,refs,explicit_missing)
            if refs: status='referenced'
            elif needs: status='unsupported'
            else: status='not_required'
            annotated=sentence
            if status=='unsupported' and '[PERLU SUMBER]' not in sentence.upper(): annotated=sentence+' [PERLU SUMBER]'
            records.append({'paragraph_idx':pidx,'sentence_idx':sidx,'text':sentence,'origin':origin,'author_origin':origin,'references':refs,'requires_evidence':needs,'status':status,'evidence_verified':False,'annotated_text':annotated})
    total=len(records); referenced=sum(r['status']=='referenced' for r in records); unsupported=sum(r['status']=='unsupported' for r in records); required=sum(r['requires_evidence'] for r in records)
    ratio=lambda k: round(counts[k]/total*100,1) if total else 0
    covered=referenced
    return {
        'author_origin':{'student_ratio':ratio('student'),'ai_expanded_ratio':ratio('ai_expanded'),'ai_suggested_ratio':ratio('ai_suggested')},
        'compliance':{
            'total_sentences':total,'required_claims':required,'referenced_claims':referenced,'unsupported_claims':unsupported,
            'compliance_score':round(covered/max(1,required)*100,1) if required else 100.0,
        },
        'sentences':records,
        'note':'Kalimat struktural/self-statement tidak otomatis membutuhkan sitasi. Klaim faktual terdeteksi atau yang ditandai [PERLU SUMBER] wajib punya reference chain; referenced belum berarti evidence terverifikasi.'
    }
