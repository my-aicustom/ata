"""Defense evaluation helpers with robust structured parsing."""
from __future__ import annotations
import json
import re
from collections import defaultdict
from typing import Any, Dict, Iterable


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
    prompt=f"KONTEKS TESIS:\n{context[:24000]}\n\nPERTANYAAN PENGUJI:\n{question}\n\nJAWABAN MAHASISWA:\n{answer}"
    res=client.chat([{'role':'system','content':system},{'role':'user','content':prompt}],tier='reasoning',temperature=.1,max_tokens=1200)
    if not res.get('success'): return res
    try: parsed=parse_defense_evaluation(res.get('content',''))
    except Exception as e: return {'success':False,'error':f'Output evaluator tidak valid: {e}','content':res.get('content','')}
    return {'success':True,**parsed,'model':res.get('model'),'raw':res.get('raw')}
