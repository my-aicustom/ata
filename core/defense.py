"""Defense evaluation helpers with thesis-aware retrieval and robust structured parsing."""
from __future__ import annotations
import json
import re
from collections import defaultdict
from typing import Any, Dict, Iterable, List, Sequence

_STOP={
    'yang','dan','atau','di','ke','dari','dengan','untuk','pada','ini','itu','saya','anda','bagaimana','mengapa',
    'apa','apakah','dalam','sebagai','oleh','karena','terhadap','adalah','tesis','penelitian','hasil'
}


def _tokens(text: str) -> set[str]:
    return {t for t in re.findall(r'[a-z0-9][a-z0-9_-]{2,}',str(text or '').lower()) if t not in _STOP}


def _chunks(title: str, content: str, size: int=2600, overlap: int=260) -> List[Dict[str,Any]]:
    text=str(content or '').strip()
    if not text: return []
    out=[]; start=0; idx=0
    while start < len(text):
        end=min(len(text),start+size)
        if end < len(text):
            cut=max(text.rfind('\n',start+size//2,end),text.rfind('. ',start+size//2,end))
            if cut>start: end=cut+1
        chunk=text[start:end].strip()
        if chunk: out.append({'title':title,'index':idx,'text':chunk,'tokens':_tokens(title+' '+chunk)})
        if end>=len(text): break
        start=max(start+1,end-overlap); idx+=1
    return out


def build_defense_context(artifacts: Sequence[Dict[str,Any]], query: str, max_chars: int=24000) -> str:
    """Retrieve the most relevant thesis chunks for one examiner question.

    This avoids the old first-N-character truncation, so a question about a late
    chapter can retrieve Bab IV/V even when earlier chapters are very long.
    """
    max_chars=max(1000,int(max_chars)); q=_tokens(query)
    candidates=[]
    for a in artifacts:
        title=str(a.get('title') or 'Bagian')
        for c in _chunks(title,str(a.get('content') or '')):
            overlap=len(q & c['tokens'])
            title_overlap=len(q & _tokens(title))
            density=overlap/max(1,len(q))
            c['score']=overlap*12+title_overlap*8+density
            candidates.append(c)
    candidates.sort(key=lambda c:(-c['score'],c['title'].lower(),c['index']))
    selected=[]; used=0
    # Prefer directly relevant chunks; if none match, fall back to balanced context.
    for c in candidates:
        if q and c['score']<=0 and selected: continue
        block=f"## {c['title']} [bagian {c['index']+1}]\n{c['text']}\n"
        if used+len(block)>max_chars:
            remaining=max_chars-used
            if remaining>180 and not selected:
                selected.append(block[:remaining])
            continue
        selected.append(block); used+=len(block)
        if used>=max_chars: break
    if not selected:
        return build_balanced_thesis_context(artifacts,max_chars=max_chars)
    return '\n'.join(selected)[:max_chars]


def _head_middle_tail(text: str, budget: int) -> str:
    text=str(text or '').strip()
    if len(text)<=budget: return text
    if budget<240: return text[:budget]
    mark1='\n…[potongan tengah]…\n'; mark2='\n…[potongan akhir]…\n'
    usable=max(90,budget-len(mark1)-len(mark2))
    base=usable//3; remainder=usable-base*3
    head_n=base; mid_n=base; tail_n=base+remainder
    middle_start=max(0,(len(text)-mid_n)//2)
    return text[:head_n]+mark1+text[middle_start:middle_start+mid_n]+mark2+text[-tail_n:]


def build_balanced_thesis_context(artifacts: Sequence[Dict[str,Any]], max_chars: int=30000) -> str:
    """Create a bounded, stratified view across every latest artifact."""
    items=[a for a in artifacts if str(a.get('content') or '').strip()]
    if not items: return ''
    max_chars=max(1000,int(max_chars))
    label_budget=sum(len(str(a.get('title') or 'Bagian'))+4 for a in items)
    separator_budget=max(0,(len(items)-1)*2)
    available=max(len(items)*160,max_chars-label_budget-separator_budget)
    per=max(160,available//len(items))
    blocks=[]
    for a in items:
        title=str(a.get('title') or 'Bagian')
        excerpt=_head_middle_tail(str(a.get('content') or ''),per)
        blocks.append(f"## {title}\n{excerpt}")
    return '\n\n'.join(blocks)[:max_chars]


def parse_defense_evaluation(text: str) -> Dict[str,Any]:
    cleaned=re.sub(r'^```(?:json)?\s*|\s*```$','',text.strip(),flags=re.I|re.S)
    match=re.search(r'\{.*\}',cleaned,flags=re.S)
    if not match: raise ValueError('Respons evaluator tidak memuat JSON')
    data=json.loads(match.group(0)); score=data.get('score')
    if not isinstance(score,int) or isinstance(score,bool) or not 1<=score<=4: raise ValueError('Skor evaluator harus 1-4')
    return {'score':score,'feedback':str(data.get('feedback') or '').strip(),'ideal_answer':str(data.get('ideal_answer') or '').strip(),'weakness':str(data.get('weakness') or 'umum').strip() or 'umum'}


def summarize_defense_history(rows: Iterable[Dict[str,Any]]) -> Dict[str,Any]:
    rows=list(rows); scored=[r for r in rows if isinstance(r.get('score'),int)]
    avg=round(sum(r['score'] for r in scored)/len(scored),2) if scored else 0.0
    buckets=defaultdict(lambda:{'count':0,'penalty':0,'scores':[]})
    for r in scored:
        name=str(r.get('weakness') or 'umum').strip() or 'umum'; b=buckets[name]; b['count']+=1; b['penalty']+=5-r['score']; b['scores'].append(r['score'])
    priority=[{'name':name,'count':v['count'],'average_score':round(sum(v['scores'])/len(v['scores']),2),'priority':v['penalty']} for name,v in buckets.items()]
    priority.sort(key=lambda x:(-x['priority'],x['average_score'],-x['count'],x['name']))
    return {'attempts':len(scored),'average_score':avg,'ready_ratio':round(sum(r['score']>=3 for r in scored)/len(scored)*100,1) if scored else 0.0,'priority_weaknesses':priority}


def evaluate_answer(client, context: str, question: str, answer: str) -> Dict[str,Any]:
    system='''Anda penguji tesis yang skeptis tetapi adil. Nilai jawaban mahasiswa hanya berdasarkan konteks tesis yang diberikan. Keluarkan JSON murni: {"score":1-4,"feedback":"...","ideal_answer":"...","weakness":"metode|teori|data|kontribusi|keterbatasan|lainnya"}. Skor 3 berarti memadai dan defensible; 4 kuat, spesifik, konsisten dengan bukti. Jangan mengarang fakta yang tidak ada di konteks.'''
    prompt=f"KONTEKS TESIS YANG DIRETRIEVE:\n{context}\n\nPERTANYAAN PENGUJI:\n{question}\n\nJAWABAN MAHASISWA:\n{answer}"
    res=client.chat([{'role':'system','content':system},{'role':'user','content':prompt}],tier='reasoning',temperature=.1,max_tokens=1200)
    if not res.get('success'): return res
    try: parsed=parse_defense_evaluation(res.get('content',''))
    except Exception as e: return {'success':False,'error':f'Output evaluator tidak valid: {e}','content':res.get('content','')}
    return {'success':True,**parsed,'model':res.get('model'),'raw':res.get('raw')}
