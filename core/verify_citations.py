from __future__ import annotations
import json, urllib.error, urllib.parse, urllib.request

def _clean(doi):
    d=(doi or '').strip()
    for p in ('https://doi.org/','http://doi.org/','doi:'):
        if d.lower().startswith(p): d=d[len(p):]
    return d

def verify_citation(doi):
    d=_clean(doi)
    if not d: return {'valid':False,'doi':d,'error':'DOI kosong'}
    url='https://api.crossref.org/works/'+urllib.parse.quote(d,safe='')
    req=urllib.request.Request(url,headers={'User-Agent':'ATA-v3/1.0'})
    try:
        with urllib.request.urlopen(req,timeout=12) as r: item=json.loads(r.read().decode()).get('message',{})
        title=(item.get('title') or [''])[0]; authors=[' '.join(filter(None,[a.get('given'),a.get('family')])) for a in item.get('author',[])]
        year=None
        for k in ('published-print','published-online','issued'):
            parts=((item.get(k) or {}).get('date-parts') or [])
            if parts and parts[0]: year=parts[0][0]; break
        return {'valid':True,'source':'crossref','doi':d,'title':title,'authors':authors,'year':year,'publisher':item.get('publisher','')}
    except urllib.error.HTTPError as e:
        return {'valid':False,'doi':d,'error':f'Crossref HTTP {e.code}'}
    except Exception as e:
        return {'valid':False,'doi':d,'error':str(e)}
