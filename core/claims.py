"""Conservative sentence audit. Reference presence is not evidence verification."""
import re


def parse_draft_claims(text):
    records=[]; counts={'student':0,'ai_expanded':0,'ai_suggested':0}
    for pidx,paragraph in enumerate(re.split(r'\n\s*\n',text.strip()),1):
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
                raw=m.group(2).strip(); parts=re.split(r',\s*(?=hal\.|p\.|page\s)',raw,maxsplit=1,flags=re.I)
                refs.append({'type':m.group(1).lower(),'id':parts[0].strip(),'locator':parts[1].strip() if len(parts)>1 else ''})
            missing=bool(re.search(r'\[(PERLU SUMBER|BELUM DIVERIFIKASI)\]',sentence,re.I)) or not refs
            records.append({'paragraph_idx':pidx,'sentence_idx':sidx,'text':sentence,'origin':origin,'author_origin':origin,'references':refs,'status':'unsupported' if missing else 'referenced','evidence_verified':False,'annotated_text':sentence+(' [PERLU SUMBER]' if missing and '[PERLU SUMBER]' not in sentence.upper() else '')})
    total=len(records); referenced=sum(r['status']=='referenced' for r in records)
    ratio=lambda k: round(counts[k]/total*100,1) if total else 0
    return {'author_origin':{'student_ratio':ratio('student'),'ai_expanded_ratio':ratio('ai_expanded'),'ai_suggested_ratio':ratio('ai_suggested')},'compliance':{'total_sentences':total,'referenced_claims':referenced,'unsupported_claims':total-referenced,'compliance_score':round(referenced/total*100,1) if total else 0},'sentences':records,'note':'Referenced hanya berarti penanda sumber tercantum; evidence belum otomatis terverifikasi.'}
