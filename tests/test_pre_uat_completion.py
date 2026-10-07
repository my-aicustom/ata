import base64
import http.cookiejar
import json
import os
import socket
import tempfile
import threading
import unittest
import urllib.error
import urllib.request
from unittest.mock import patch


class PreUATCoreTests(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory()
        os.environ['ATA_DATA_DIR']=self.tmp.name
        os.environ.pop('OPENROUTER_API_KEY',None)
        from core import db
        db.reset_for_tests(); db.init_db()
        self.db=db
        self.pid=db.create_project('s',{'student':'A','program':'S2','topic':'T','method':'survey'})

    def tearDown(self):
        self.tmp.cleanup(); os.environ.pop('ATA_DATA_DIR',None)

    def test_confidential_media_is_blocked_from_cloud(self):
        from core.intake import decide_intake
        decision=decide_intake('confidential','image','catatan.png')
        self.assertFalse(decision['cloud_allowed'])
        self.assertTrue(decision['local_allowed'])
        self.assertEqual(decision['classification'],'confidential')

    def test_g1_does_not_require_nonexistent_must_directive(self):
        from core import gates
        self.db.save_gate_assessment(self.pid,'G1',{
            'finer_scores':{k:3 for k in ['Feasible','Interesting','Novel','Ethical','Relevant']},
            'supervisor_approved':True,
        })
        result=gates.evaluate_g1(self.pid)
        self.assertTrue(result['passed'])
        self.assertEqual(result['metrics']['must_directives'],'0/0')

    def test_claim_audit_does_not_flag_structural_self_statement_as_unsupported(self):
        from core.claims import parse_draft_claims
        out=parse_draft_claims('Penelitian ini bertujuan untuk menjelaskan hubungan variabel X dan Y.')
        self.assertEqual(out['compliance']['unsupported_claims'],0)
        self.assertFalse(out['sentences'][0]['requires_evidence'])
        factual=parse_draft_claims('Data nasional menunjukkan peningkatan sebesar 12 persen pada 2025.')
        self.assertEqual(factual['compliance']['unsupported_claims'],1)
        self.assertTrue(factual['sentences'][0]['requires_evidence'])

    def test_artifact_provenance_collects_data_refs_too(self):
        art=self.db.save_artifact(self.pid,'chapter','Bab IV','Hasil utama [Data: DATA-99, tabel 4.1].')
        self.assertIn('DATA-99',art['source_refs'])

    def test_data_reference_can_resolve_against_document_backed_evidence(self):
        from core.evidence import resolve_draft_evidence
        self.db.save_source(self.pid,{'id':'DATA-01','type':'dataset','title':'Output analisis final','authors':[],'verification_status':'candidate'})
        self.db.save_evidence(self.pid,'DATA-01','tabel 4.2','Koefisien jalur X ke Y adalah 0,42.',verification={
            'verified':True,'method':'exact_normalized_document_match','source_sha256':'abc123'
        })
        out=resolve_draft_evidence(self.pid,'Koefisien jalur X ke Y adalah 0,42 [Data: DATA-01, tabel 4.2].')
        self.assertEqual(out['sentences'][0]['status'],'supported')
        self.assertEqual(out['sentences'][0]['resolved'][0]['support_basis'],'data_document_backed')

    def test_g2_counts_non_doi_document_backed_source_as_traceable(self):
        from core import gates
        self.db.save_source(self.pid,{'id':'REG-01','type':'regulation','title':'Peraturan Resmi','authors':[],'year':2026,'verification_status':'candidate'})
        self.db.save_evidence(self.pid,'REG-01','pasal 1','Ketentuan ini berlaku.',verification={'verified':True,'method':'exact_normalized_document_match','source_sha256':'hash-reg'})
        self.db.save_gate_assessment(self.pid,'G2',{'min_sources':1,'recent_ratio_target':0,'research_gap_ready':True,'framework_ready':True})
        result=gates.evaluate_g2(self.pid)
        self.assertTrue(result['passed'],result)
        self.assertEqual(result['metrics']['traceable_sources'],1)

    def test_g5_derives_claim_integrity_from_latest_artifacts(self):
        from core import gates
        self.db.save_source(self.pid,{'id':'DOC-01','type':'regulation','title':'Dokumen resmi','authors':[],'verification_status':'candidate'})
        self.db.save_evidence(self.pid,'DOC-01','hal. 1','Kebijakan ini berlaku untuk seluruh unit kerja.',verification={
            'verified':True,'method':'exact_normalized_page_match','source_sha256':'hash1'
        })
        self.db.save_artifact(self.pid,'chapter','Bab I','Kebijakan ini berlaku untuk seluruh unit kerja [Brief: DOC-01, hal. 1].')
        self.db.save_gate_assessment(self.pid,'G5',{'similarity':8,'similarity_threshold':20,'open_red_critiques':0})
        result=gates.evaluate_g5(self.pid)
        self.assertTrue(result['passed'],result)
        self.assertEqual(result['metrics']['unsupported_claims'],0)

    def test_g6_uses_saved_defense_history_without_manual_copy(self):
        from core import gates
        for i,score in enumerate([3,4,3,3,2]):
            self.db.save_defense_score(self.pid,f'Q{i}',f'A{i}',score,'feedback','metode')
        result=gates.evaluate_g6(self.pid)
        self.assertTrue(result['passed'])
        self.assertEqual(result['metrics']['total'],5)

    def test_g3_requires_at_least_three_consistency_rows(self):
        from core import gates
        self.db.upsert_consistency_rows(self.pid,[{'element':'RQ1 ↔ Tujuan','content':'ok','score':4,'critique':''}])
        self.db.save_gate_assessment(self.pid,'G3',{'instrument_ready':True,'analysis_plan_locked':True,'proposal_approved':True})
        self.assertFalse(gates.evaluate_g3(self.pid)['passed'])
        self.db.upsert_consistency_rows(self.pid,[
            {'element':'RQ1 ↔ Metode','content':'ok','score':3,'critique':''},
            {'element':'RQ1 ↔ Analisis','content':'ok','score':3,'critique':''},
        ])
        self.assertTrue(gates.evaluate_g3(self.pid)['passed'])

    def test_g5_cannot_pass_without_a_manuscript_artifact(self):
        from core import gates
        self.db.save_gate_assessment(self.pid,'G5',{'similarity':5,'similarity_threshold':20,'open_red_critiques':0})
        result=gates.evaluate_g5(self.pid)
        self.assertFalse(result['passed'])
        self.assertFalse(result['checks']['Naskah final tersedia'])

    def test_synthetic_journey_can_reach_all_six_gates(self):
        from core import gates
        self.db.save_gate_assessment(self.pid,'G1',{'finer_scores':{k:3 for k in ['Feasible','Interesting','Novel','Ethical','Relevant']},'supervisor_approved':True})
        self.db.save_source(self.pid,{'id':'REG-J','type':'regulation','title':'Dokumen Acuan','authors':[],'year':2026,'verification_status':'candidate'})
        self.db.save_evidence(self.pid,'REG-J','hal. 1','Ketentuan acuan berlaku.',verification={'verified':True,'method':'exact_normalized_document_match','source_sha256':'h1'})
        self.db.save_gate_assessment(self.pid,'G2',{'min_sources':1,'recent_ratio_target':0,'research_gap_ready':True,'framework_ready':True})
        self.db.upsert_consistency_rows(self.pid,[
            {'element':'RQ1 ↔ Tujuan','content':'selaras','score':3,'critique':''},
            {'element':'RQ1 ↔ Metode','content':'selaras','score':3,'critique':''},
            {'element':'RQ1 ↔ Analisis','content':'selaras','score':3,'critique':''},
        ])
        self.db.save_gate_assessment(self.pid,'G3',{'instrument_ready':True,'analysis_plan_locked':True,'proposal_approved':True})
        self.db.save_gate_assessment(self.pid,'G4',{'loading':[.71],'ave':.55,'htmt':.80,'cr':.75})
        self.db.save_source(self.pid,{'id':'DATA-J','type':'dataset','title':'Output analisis','authors':[],'verification_status':'candidate'})
        self.db.save_evidence(self.pid,'DATA-J','tabel 4.2','Koefisien jalur X ke Y adalah 0,42.',verification={'verified':True,'method':'exact_normalized_document_match','source_sha256':'h2'})
        self.db.save_artifact(self.pid,'chapter','Bab IV','Penelitian ini bertujuan menjelaskan hubungan X dan Y. Koefisien jalur X ke Y adalah 0,42 [Data: DATA-J, tabel 4.2].')
        self.db.save_gate_assessment(self.pid,'G5',{'similarity':9,'similarity_threshold':20,'open_red_critiques':0})
        for i,score in enumerate([3,4,3,3,2]): self.db.save_defense_score(self.pid,f'Q{i}',f'A{i}',score,'ok','metode')
        results=gates.get_all_gates(self.pid,'survey')
        self.assertTrue(all(x['passed'] for x in results),results)

    def test_planner_source_finder_role_is_registered(self):
        from core.roles import ROLE_PROMPTS
        self.assertIn('source_finder',ROLE_PROMPTS)

    def test_consistency_matrix_has_crud_helpers(self):
        self.db.upsert_consistency_rows(self.pid,[
            {'element':'RQ1 ↔ Tujuan 1','content':'selaras','score':3,'critique':''},
            {'element':'RQ1 ↔ Analisis','content':'selaras','score':4,'critique':''},
        ])
        rows=self.db.list_consistency_rows(self.pid)
        self.assertEqual(len(rows),2)
        self.assertEqual(rows[0]['project_id'],self.pid)


class PreUATApiTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.tmp=tempfile.TemporaryDirectory(); os.environ['ATA_DATA_DIR']=cls.tmp.name
        os.environ.pop('OPENROUTER_API_KEY',None)
        from core import db
        db.reset_for_tests(); db.init_db()
        from server import make_server
        sock=socket.socket(); sock.bind(('127.0.0.1',0)); cls.port=sock.getsockname()[1]; sock.close()
        cls.httpd=make_server('127.0.0.1',cls.port); cls.thread=threading.Thread(target=cls.httpd.serve_forever,daemon=True); cls.thread.start()

    @classmethod
    def tearDownClass(cls):
        cls.httpd.shutdown(); cls.httpd.server_close(); cls.tmp.cleanup(); os.environ.pop('ATA_DATA_DIR',None)

    def opener(self):
        return urllib.request.build_opener(urllib.request.HTTPCookieProcessor(http.cookiejar.CookieJar()))

    def call(self,o,path,data=None):
        body=json.dumps(data).encode() if data is not None else None
        req=urllib.request.Request(f'http://127.0.0.1:{self.port}{path}',data=body,headers={'Content-Type':'application/json'} if body else {})
        try:
            with o.open(req,timeout=8) as r: return r.status,json.loads(r.read().decode())
        except urllib.error.HTTPError as e:
            return e.code,json.loads(e.read().decode())

    def project(self,o):
        return self.call(o,'/api/projects/create',{'student':'A','program':'S2','topic':'Journey','method':'survey'})[1]

    def test_confidential_image_never_calls_vision_provider(self):
        o=self.opener(); self.project(o)
        with patch('server.OpenRouterClient.vision') as vision:
            status,out=self.call(o,'/api/parse/file',{
                'filename':'rahasia.png','base64':base64.b64encode(b'png').decode(),
                'classification':'confidential'
            })
        self.assertEqual(status,200)
        self.assertFalse(out['cloud_allowed'])
        self.assertTrue(out['media_pending'])
        self.assertIn('Rahasia',out['media_error'])
        vision.assert_not_called()

    def test_supervisor_text_can_be_extracted_and_saved_to_ledger(self):
        o=self.opener(); self.project(o)
        fake={'success':True,'content':json.dumps([
            {'id':'SV-01','quote':'Perjelas gap','directive':'Perjelas research gap di akhir Bab II','priority':'MUST','target_chapter':'Bab II','status':'open'}
        ])}
        with patch('server.agent.run_role',return_value=fake):
            status,out=self.call(o,'/api/directives/extract',{'text':'Perjelas gap','save':True})
        self.assertEqual(status,200)
        self.assertEqual(out['saved'],1)
        _,rows=self.call(o,'/api/directives')
        self.assertEqual(rows[0]['directive'],'Perjelas research gap di akhir Bab II')

    def test_research_brief_saves_only_deterministically_verified_quotes(self):
        o=self.opener(); p=self.project(o)
        _,saved=self.call(o,'/api/literature/save',{'source':{'id':'SRC-BRIEF','type':'report','title':'Laporan','authors':[]}})
        source_text='Temuan utama menunjukkan peningkatan produktivitas sebesar 12 persen.'
        fake={'success':True,'content':json.dumps({
            'summary':'Ringkas','method':'Studi dokumen','findings':['Produktivitas meningkat'],
            'quotes':[
                {'locator':'bagian hasil','text':'Temuan utama menunjukkan peningkatan produktivitas sebesar 12 persen.'},
                {'locator':'bagian palsu','text':'Kalimat yang tidak ada di dokumen sumber sama sekali.'}
            ]
        })}
        with patch('server.agent.run_role',return_value=fake):
            status,out=self.call(o,'/api/research-brief/create',{
                'source_id':saved['id'],'source_filename':'laporan.txt',
                'source_document_base64':base64.b64encode(source_text.encode()).decode()
            })
        self.assertEqual(status,200,out)
        self.assertEqual(out['verified_evidence_count'],1)
        self.assertEqual(out['rejected_quote_count'],1)
        from core import db
        ev=db.list_evidence(p['id'],saved['id'])
        self.assertEqual(len(ev),1)
        self.assertEqual(ev[0]['verification_status'],'verified')

    def test_confidential_chat_attachment_is_rejected_before_agent_call(self):
        o=self.opener(); self.project(o)
        with patch('server.agent.run_role') as run:
            status,out=self.call(o,'/api/agent/chat',{'role':'onboarding','message':'cek','attachments':[{'filename':'rahasia.txt','text':'isi','classification':'confidential'}]})
        self.assertEqual(status,403)
        self.assertIn('Rahasia',out['error'])
        run.assert_not_called()

    def test_large_scanned_pdf_brief_stops_before_provider_to_avoid_partial_brief(self):
        o=self.opener(); self.project(o)
        _,saved=self.call(o,'/api/literature/save',{'source':{'id':'SCAN-1','type':'report','title':'Scan','authors':[]}})
        with patch.dict(os.environ,{'ATA_BRIEF_OCR_MAX_PAGES':'2'}), \
             patch('server.parse_bytes',return_value={'type':'document','text':'[PAGE 1]\n','needs_ocr':True,'ocr_pages':[1,2,3]}), \
             patch('server.agent.run_role') as run:
            status,out=self.call(o,'/api/research-brief/create',{'source_id':saved['id'],'source_filename':'scan.pdf','source_document_base64':base64.b64encode(b'%PDF dummy').decode()})
        self.assertEqual(status,422)
        self.assertEqual(out['ocr_cap'],2)
        run.assert_not_called()

    def test_bibtex_export_endpoint_returns_referenced_sources(self):
        o=self.opener(); self.project(o)
        _,src=self.call(o,'/api/literature/save',{'source':{'id':'BIB-1','type':'journal','title':'Paper Bib','authors':['A'],'year':2025,'doi':'10.1/bib'}})
        self.call(o,'/api/artifacts/save',{'kind':'chapter','title':'Bab I','content':'Klaim [Brief: BIB-1, hal. 1].'})
        status,out=self.call(o,'/api/references/export-bibtex',{})
        self.assertEqual(status,200)
        text=base64.b64decode(out['base64']).decode()
        self.assertIn('Paper Bib',text)
        self.assertEqual(out['filename'],'references.bib')

    def test_consistency_save_replaces_stale_rows(self):
        o=self.opener(); self.project(o)
        rows=[
            {'element':'RQ1 ↔ Tujuan','content':'OK','score':3,'critique':''},
            {'element':'Tujuan ↔ Metode','content':'OK','score':3,'critique':''},
            {'element':'Metode ↔ Analisis','content':'OK','score':3,'critique':''},
        ]
        status,_=self.call(o,'/api/consistency/save',{'rows':rows})
        self.assertEqual(status,200)
        status,out=self.call(o,'/api/consistency/save',{'rows':[rows[0]]})
        self.assertEqual(status,200)
        self.assertEqual(len(out['rows']),1)
        status,rows_now=self.call(o,'/api/consistency')
        self.assertEqual(status,200)
        self.assertEqual([r['element'] for r in rows_now],['RQ1 ↔ Tujuan'])

    def test_consistency_matrix_api_and_preflight_exist(self):
        o=self.opener(); self.project(o)
        status,out=self.call(o,'/api/consistency/save',{'rows':[{'element':'RQ1 ↔ Tujuan','content':'OK','score':3,'critique':''}]})
        self.assertEqual(status,200)
        status,rows=self.call(o,'/api/consistency')
        self.assertEqual(status,200); self.assertEqual(len(rows),1)
        status,pf=self.call(o,'/api/preflight')
        self.assertEqual(status,200)
        self.assertIn('checks',pf)
        self.assertIn('live_tests_remaining',pf)
        self.assertTrue(pf['code_ready'])


if __name__=='__main__':
    unittest.main()
