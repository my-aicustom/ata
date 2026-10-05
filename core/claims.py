"""Conservative sentence audit. Reference presence is not evidence verification."""
import re

def parse_draft_claims(text):
    records = []
    counts = dict(student=0, ai_expanded=0, ai_suggested=0)
    for pidx, paragraph in enumerate(re.split(r'\n\s*\n', text.strip()), 1):
        if not paragraph.strip(): continue
        tags = re.findall(r'\((M\+AI|AI|M)\)', paragraph, re.I)
        inherited = tags[0].upper() if tags else 'M'
        # Shield periods inside locators, decimals, and common abbreviations.
        protected = re.sub(r'\[[^\]]*\]', lambda m: m[0].replace('.', '\uE000'), paragraph)
        protected = re.sub(r'(?<=\d)\.(?=\d)', '\uE000', protected)
        protected = re.sub(r'\b(?:Dr|Prof|No|et al)\.', lambda m: m[0].replace('.', '\uE000'), protected)
        chunks = re.findall(r'.*?[.!?](?:\s*\[(?:Brief|Ledger):[^\]]+\]|\s*\[(?:PERLU SUMBER|BELUM DIVERIFIKASI)\])*(?=\s+|$)|.+$', protected.strip(), re.I | re.S)
        for sidx, sentence in enumerate(chunks, 1):
            sentence = sentence.replace('\uE000', '.').strip()
            if not sentence: continue
            tag = re.search(r'\((M\+AI|AI|M)\)', sentence, re.I)
            if tag:
                inherited = tag[1].upper()
            origin = {'M': 'student', 'M+AI': 'ai_expanded', 'AI': 'ai_suggested'}[(tag[1].upper() if tag else inherited)]
            counts[origin] += 1
            references = []
            for m in re.finditer(r'\[(Brief|Ledger):\s*([^\]]+)\]', sentence, re.I):
                parts = re.split(r',\s*hal\.\s*', m[2], maxsplit=1, flags=re.I)
                references.append(dict(type=m[1].lower(), id=parts[0].strip(), page=parts[1].strip() if len(parts) > 1 else None))
            missing = bool(re.search(r'\[(PERLU SUMBER|BELUM DIVERIFIKASI)\]', sentence, re.I)) or not references
            records.append(dict(paragraph_idx=pidx, sentence_idx=sidx, text=sentence, origin=origin,
                author_origin=origin, references=references, evidences=re.findall(r'\[([^\]]+)\]', sentence),
                status='unsupported' if missing else 'supported', evidence_verified=False,
                annotated_text=sentence + (' [PERLU SUMBER]' if missing and '[PERLU SUMBER]' not in sentence.upper() else '')))
    total = len(records)
    supported = sum(r['status'] == 'supported' for r in records)
    distribution = {k + '_ratio': round(v / total * 100, 1) if total else 0 for k, v in counts.items()}
    return dict(author_origin=distribution, compliance=dict(total_sentences=total, supported_claims=supported,
        unsupported_claims=total-supported, compliance_score=round(supported / total * 100, 1) if total else 0),
        sentences=records, note='Supported berarti penanda rujukan tersedia; isi sumber belum diverifikasi.')
