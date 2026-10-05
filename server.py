from __future__ import annotations
import base64, json, mimetypes, os, secrets, urllib.parse
from http import cookies
from http.server import ThreadingHTTPServer, SimpleHTTPRequestHandler
from pathlib import Path
from typing import Any

ROOT=Path(__file__).resolve().parent; WEB=ROOT/'web'
from core import db
from core.gates import get_all_gates
from core.planner import next_best_action
from core.literature import search_openalex, search_crossref, dedupe_sources
from core.roles import ThesisAgent
from core.claims import parse_draft_claims
from core.verify_citations import verify_citation
from core.quote_check import verify_quote
from core.file_parser import parse_bytes
from core.openrouter_client import OpenRouterClient
from core.revisions import propose_revision, accept_revision, reject_revision, list_revisions
from core.evidence import resolve_draft_evidence
from core.export_docx import build_manuscript_docx
from core.defense import evaluate_answer, summarize_defense_history

FORBIDDEN=['di era digital yang dinamis','di era globalisasi','tidak dapat dipungkiri','memegang peranan yang sangat penting','seiring dengan perkembangan zaman','secara komprehensif dan holistik','sangat krusial','menjadi sebuah keniscayaan']
agent=ThesisAgent()
init_db = db.init_db  # compatibility with api/index.py

def _session_from_header(handler):
    raw=handler.headers.get('Cookie',''); jar=cookies.SimpleCookie();
    try: jar.load(raw)
    except cookies.CookieError: pass
    if jar.get('ata_session'): return jar['ata_session'].value, False
    return secrets.token_urlsafe(24), True

class ATAHandler(SimpleHTTPRequestHandler):
    def __init__(self,*args,directory=None,**kwargs): super().__init__(*args,directory=str(WEB),**kwargs)
    def log_message(self,fmt,*args):
        if os.getenv('ATA_HTTP_LOG','0')=='1': super().log_message(fmt,*args)
    def _session(self):
        if not hasattr(self,'_ata_session'): self._ata_session,self._new_session=_session_from_header(self)
        return self._ata_session
    def _set_common(self):
        self.send_header('X-Content-Type-Options','nosniff'); self.send_header('Referrer-Policy','same-origin'); self.send_header('Cache-Control','no-store')
        if getattr(self,'_new_session',False):
            secure='; Secure' if os.getenv('VERCEL') else ''
            self.send_header('Set-Cookie',f'ata_session={self._ata_session}; Path=/; HttpOnly; SameSite=Lax; Max-Age=31536000{secure}')
            self._new_session=False
    def end_headers(self): self._set_common(); super().end_headers()
    def send_json(self,obj:Any,status=200):
        body=json.dumps(obj,ensure_ascii=False,default=str).encode(); self.send_response(status); self.send_header('Content-Type','application/json; charset=utf-8'); self.send_header('Content-Length',str(len(body))); self.end_headers(); self.wfile.write(body)
    def _path(self):
        p=urllib.parse.urlparse(self.headers.get('x-forwarded-uri') or self.path); q=urllib.parse.parse_qs(p.query)
        path=q.get('__path',[p.path])[0]
        if path.startswith('/api/index.py/'): path=path.replace('/api/index.py','/api',1)
        return path,q
    def _json(self):
        n=int(self.headers.get('Content-Length','0') or 0)
        if n>35_000_000: raise ValueError('Body terlalu besar')
        raw=self.rfile.read(n) if n else b'{}'; obj=json.loads(raw.decode())
        if not isinstance(obj,dict): raise ValueError('JSON object required')
        return obj
    def _active(self): return db.get_active_project(self._session())
    def _need_project(self):
        p=self._active()
        if not p: self.send_json({'error':'Belum ada proyek tesis aktif. Buat proyek terlebih dulu.'},409); return None
        return p
    def do_GET(self):
        db.init_db(); path,q=self._path(); self._session()
        if path=='/api/status': return self.send_json({'ok':True,'storage':db.storage_status(),'project':self._active()})
        if path=='/api/projects': return self.send_json(db.list_projects(self._session()))
        if path=='/api/projects/active': return self.send_json(self._active() or {})
        if path=='/api/gates':
            p=self._need_project();
            if not p:return
            return self.send_json(get_all_gates(p['id'],p['method']))
        if path=='/api/next-action':
            p=self._need_project();
            if not p:return
            gates={g['gate']:g for g in get_all_gates(p['id'],p['method'])}; open_must=sum(d['priority']=='MUST' and d['status']!='addressed' for d in db.get_directives(p['id']))
            return self.send_json(next_best_action({'stage':p['stage'],'gates':gates,'open_must':open_must}))
        if path=='/api/directives':
            p=self._need_project();
            if not p:return
            return self.send_json(db.get_directives(p['id']))
        if path=='/api/sources':
            p=self._need_project();
            if not p:return
            return self.send_json(db.list_sources(p['id']))
        if path=='/api/artifacts':
            p=self._need_project();
            if not p:return
            return self.send_json(db.list_artifacts(p['id']))
        if path=='/api/revisions':
            p=self._need_project();
            if not p:return
            return self.send_json(list_revisions(p['id']))
        if path=='/api/defense/history':
            p=self._need_project();
            if not p:return
            rows=db.list_defense_scores(p['id']); return self.send_json({'records':rows,'summary':summarize_defense_history(rows)})
        if path=='/api/model/status': return self.send_json({'provider':'OpenRouter','configured':bool(agent.client.get_key())})
        if path.startswith('/api/'): return self.send_json({'error':'Endpoint not found','path':path},404)
        return self._serve_static(path)
    def _serve_static(self,path):
        if path.startswith('/web/'): path=path[4:]
        elif path.startswith('web/'): path=path[3:]
        rel='index.html' if path in ('','/') else path.lstrip('/'); target=(WEB/rel).resolve()
        try: target.relative_to(WEB.resolve())
        except ValueError: return self.send_error(404)
        if not target.is_file(): return self.send_error(404)
        data=target.read_bytes(); self.send_response(200); self.send_header('Content-Type',mimetypes.guess_type(str(target))[0] or 'application/octet-stream'); self.send_header('Content-Length',str(len(data))); self.end_headers(); self.wfile.write(data)
    def do_POST(self):
        db.init_db(); path,q=self._path(); self._session()
        try: data=self._json()
        except Exception as e: return self.send_json({'error':str(e)},400)
        if path=='/api/projects/create':
            pid=db.create_project(self._session(),data); return self.send_json({'success':True,'id':pid,'project':db.get_project_for_session(self._session(),pid)})
        if path=='/api/projects/switch':
            ok=db.set_active_project(self._session(),str(data.get('id') or '')); return self.send_json({'success':ok,'project':self._active()} if ok else {'error':'Project tidak ditemukan'},200 if ok else 404)
        p=self._need_project()
        if not p:return
        pid=p['id']
        if path=='/api/projects/update':
            ok=db.update_project(self._session(),pid,data); return self.send_json({'success':ok,'project':self._active()})
        if path=='/api/gates/assessment':
            gate=str(data.get('gate') or ''); payload=data.get('data')
            if gate not in {'G1','G2','G3','G4','G5','G6'} or not isinstance(payload,dict): return self.send_json({'error':'Gate/data invalid'},400)
            db.save_gate_assessment(pid,gate,payload); return self.send_json({'success':True})
        if path=='/api/directives/import':
            items=data.get('directives');
            if not isinstance(items,list): return self.send_json({'error':'directives harus list'},400)
            return self.send_json({'success':True,'count':db.upsert_directives(pid,items)})
        if path=='/api/directives/update':
            ok=db.update_directive_status(pid,str(data.get('id') or ''),str(data.get('status') or ''),data.get('evidence_ref')); return self.send_json({'success':ok},200 if ok else 404)
        if path=='/api/literature/search':
            query=str(data.get('query') or '').strip(); limit=int(data.get('limit') or 10)
            if len(query)<3:return self.send_json({'error':'Query terlalu pendek'},400)
            items=[]; errors=[]
            for fn in (search_openalex,search_crossref):
                try: items.extend(fn(query,limit))
                except Exception as e: errors.append(str(e))
            items=dedupe_sources(items)[:max(1,min(limit*2,40))]
            return self.send_json({'results':items,'errors':errors})
        if path=='/api/literature/save':
            src=data.get('source')
            if not isinstance(src,dict):return self.send_json({'error':'source invalid'},400)
            candidate={**src,'verified':False,'verification_status':'candidate'}
            sid=db.save_source(pid,candidate); return self.send_json({'success':True,'id':sid})
        if path=='/api/literature/verify':
            sid=str(data.get('source_id') or ''); src=next((x for x in db.list_sources(pid) if x['id']==sid),None)
            if not src:return self.send_json({'error':'Source tidak ditemukan'},404)
            if not src.get('doi'):return self.send_json({'error':'Source tidak memiliki DOI untuk verifikasi deterministik'},400)
            verified=verify_citation(src['doi'])
            if not verified.get('valid'):return self.send_json({'success':False,**verified},200)
            updated={**src,'verified':True,'verification_status':'verified','title':verified.get('title') or src['title'],'authors':verified.get('authors') or src.get('authors') or [],'year':verified.get('year') or src.get('year')}
            db.save_source(pid,updated); return self.send_json({'success':True,'source':next(x for x in db.list_sources(pid) if x['id']==sid),'verification':verified})
        if path=='/api/evidence/save':
            sid=str(data.get('source_id') or '').strip(); locator=str(data.get('locator') or '').strip(); text=str(data.get('text') or '').strip()
            if not sid or not locator or not text:return self.send_json({'error':'source_id, locator, dan text wajib'},400)
            try:eid=db.save_evidence(pid,sid,locator,text)
            except Exception as e:return self.send_json({'error':f'Gagal menyimpan evidence: {e}'},400)
            return self.send_json({'success':True,'id':eid})
        if path=='/api/evidence/resolve':
            return self.send_json(resolve_draft_evidence(pid,str(data.get('text') or '')))
        if path=='/api/verify/citation': return self.send_json(verify_citation(str(data.get('doi') or '')))
        if path=='/api/verify/quote': return self.send_json(verify_quote(str(data.get('quote') or ''),str(data.get('source') or '')))
        if path=='/api/audit/claims': return self.send_json(parse_draft_claims(str(data.get('text') or '')))
        if path=='/api/audit/slop':
            text=str(data.get('text') or '').lower(); found=[x for x in FORBIDDEN if x in text]; return self.send_json({'clean':not found,'found':found})
        if path=='/api/artifacts/save':
            kind=str(data.get('kind') or 'note'); title=str(data.get('title') or '').strip(); content=str(data.get('content') or '')
            if not title:return self.send_json({'error':'Judul artefak wajib'},400)
            return self.send_json(db.save_artifact(pid,kind,title,content,data.get('source_refs') if isinstance(data.get('source_refs'),list) else []))
        if path=='/api/revisions/propose':
            artifact_id=str(data.get('artifact_id') or ''); directive_id=str(data.get('directive_id') or '') or None; proposed=str(data.get('proposed_text') or '').strip(); rationale=str(data.get('rationale') or '').strip()
            artifact=db.get_artifact(pid,artifact_id)
            if not artifact:return self.send_json({'error':'Artefak target tidak ditemukan'},404)
            if not proposed:
                directive=next((d for d in db.get_directives(pid) if d['id']==directive_id),None) if directive_id else None
                instruction=directive['directive'] if directive else str(data.get('instruction') or '').strip()
                if not instruction:return self.send_json({'error':'Pilih arahan pembimbing atau isi instruction'},400)
                prompt=f"ARAHAN REVISI: {instruction}\n\nNASKAH SAAT INI ({artifact['title']}):\n{artifact['content']}"
                generated=agent.run_role('revision_editor',prompt,[],data.get('api_key'),p,pid)
                if not generated.get('success'):return self.send_json(generated,502)
                proposed=generated.get('content','').strip(); rationale=rationale or instruction
            try:return self.send_json(propose_revision(pid,directive_id,artifact_id,proposed,rationale))
            except ValueError as e:return self.send_json({'error':str(e)},400)
        if path=='/api/revisions/decision':
            rid=str(data.get('id') or ''); decision=str(data.get('decision') or '')
            try:
                if decision=='accept': return self.send_json(accept_revision(pid,rid))
                if decision=='reject': return self.send_json(reject_revision(pid,rid))
                return self.send_json({'error':'decision harus accept/reject'},400)
            except ValueError as e:return self.send_json({'error':str(e)},400)
        if path=='/api/artifacts/export-docx':
            template=None; t64=str(data.get('template_base64') or '')
            if t64:
                try:template=base64.b64decode(t64,validate=True)
                except Exception:return self.send_json({'error':'Template DOCX base64 invalid'},400)
            try:raw=build_manuscript_docx(p,db.list_artifacts(pid),template)
            except Exception as e:return self.send_json({'error':f'Export DOCX gagal: {e}'},400)
            safe=''.join(ch if ch.isalnum() or ch in '-_' else '-' for ch in (p.get('topic') or 'tesis'))[:80].strip('-') or 'tesis'
            return self.send_json({'success':True,'filename':safe+'.docx','mime':'application/vnd.openxmlformats-officedocument.wordprocessingml.document','base64':base64.b64encode(raw).decode('ascii')})
        if path=='/api/defense/evaluate':
            question=str(data.get('question') or '').strip(); answer=str(data.get('answer') or '').strip()
            if not question or not answer:return self.send_json({'error':'Pertanyaan dan jawaban wajib'},400)
            artifacts=db.list_artifacts(pid); context='\n\n'.join(f"## {a['title']}\n{a['content']}" for a in artifacts)
            if not context.strip():return self.send_json({'error':'Simpan naskah tesis terlebih dulu agar evaluator punya konteks'},409)
            result=evaluate_answer(OpenRouterClient(data.get('api_key')),context,question,answer)
            if not result.get('success'):return self.send_json(result,502)
            db.save_defense_score(pid,question,answer,int(result['score']),result.get('feedback',''),result.get('weakness',''))
            rows=db.list_defense_scores(pid); result['summary']=summarize_defense_history(rows); return self.send_json(result)
        if path=='/api/defense/weakness-map':
            artifacts=db.list_artifacts(pid); context='\n\n'.join(f"## {a['title']}\n{a['content']}" for a in artifacts)
            if not context.strip():return self.send_json({'error':'Simpan naskah tesis terlebih dulu'},409)
            prompt='Petakan 5-10 titik lemah tesis berikut yang paling mungkin diserang penguji. Prioritaskan inkonsistensi RQ-metode-temuan, bukti lemah, overclaim, dan kontribusi. Untuk tiap titik: risiko, pertanyaan penguji, dan apa yang harus dikuasai mahasiswa. Jangan mengarang fakta di luar naskah.\n\n'+context[:30000]
            result=OpenRouterClient(data.get('api_key')).chat([{'role':'user','content':prompt}],tier='reasoning',temperature=.15,max_tokens=2500)
            return self.send_json(result,200 if result.get('success') else 502)
        if path=='/api/parse/file':
            b64=str(data.get('base64') or ''); filename=str(data.get('filename') or 'file.bin')
            if not b64:return self.send_json({'error':'File kosong'},400)
            try: raw=base64.b64decode(b64,validate=True)
            except Exception:return self.send_json({'error':'Base64 invalid'},400)
            if len(raw)>20_000_000:return self.send_json({'error':'File maksimal 20 MB pada mode lokal. Untuk produksi gunakan object storage.'},413)
            parsed=parse_bytes(filename,raw)
            response={'success':parsed.get('type')!='error','filename':filename,'size':len(raw),**parsed}
            client=OpenRouterClient(data.get('api_key'))
            if parsed.get('type')=='audio':
                media=client.transcribe(raw,filename,language=str(data.get('language') or 'id'))
                if media.get('success'):
                    response.update({'text':media['text'],'media_pending':False,'media_model':media.get('model'),'media_usage':media.get('usage')})
                else:
                    response.update({'media_pending':True,'media_error':media.get('error','Transkripsi belum tersedia')})
            elif parsed.get('type')=='image':
                mime=mimetypes.guess_type(filename)[0] or 'image/png'
                prompt=str(data.get('media_prompt') or 'Baca gambar ini sebagai bahan tesis. Jika berupa catatan/revisi dosen, transkripsikan isi yang terbaca dan jelaskan arahan secara faktual. Jika ada bagian tidak terbaca, tandai [TIDAK TERBACA]. Jangan mengarang teks.')
                media=client.vision(raw,mime,prompt)
                if media.get('success'):
                    response.update({'text':media['content'],'media_pending':False,'media_model':media.get('model')})
                else:
                    response.update({'media_pending':True,'media_error':media.get('error','Vision belum tersedia')})
            return self.send_json(response)
        if path=='/api/agent/chat':
            role=str(data.get('role') or 'onboarding'); msg=str(data.get('message') or ''); history=data.get('history') or []
            if not msg.strip():return self.send_json({'error':'Pesan kosong'},400)
            return self.send_json(agent.run_role(role,msg,history if isinstance(history,list) else [],data.get('api_key'),p,pid))
        return self.send_json({'error':'Endpoint not found','path':path},404)

def make_server(host='127.0.0.1',port=4321): db.init_db(); return ThreadingHTTPServer((host,port),ATAHandler)
def run_server(port=4321):
    s=make_server('127.0.0.1',port); print(f'ATA v3 running http://127.0.0.1:{port}');
    try:s.serve_forever()
    except KeyboardInterrupt: pass
    finally:s.server_close()
if __name__=='__main__':
    import sys; run_server(int(sys.argv[1]) if len(sys.argv)>1 else 4321)
