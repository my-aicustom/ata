import base64
import http.cookiejar
import io
import json
import os
import socket
import tempfile
import threading
import unittest
import urllib.request
from docx import Document


class ApiCompleteTests(unittest.TestCase):
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
        with o.open(req,timeout=6) as r: return json.loads(r.read().decode())
    def project(self,o,topic='T'):
        return self.call(o,'/api/projects/create',{'student':'A','program':'S2','topic':topic,'method':'interview'})

    def test_revision_api_accepts_into_new_artifact_version(self):
        o=self.opener(); self.project(o,'Revision')
        art=self.call(o,'/api/artifacts/save',{'kind':'chapter','title':'Bab II','content':'Versi lama.'})
        self.call(o,'/api/directives/import',{'directives':[{'id':'DP-01','directive':'Perbaiki gap','priority':'MUST','status':'open'}]})
        rev=self.call(o,'/api/revisions/propose',{'artifact_id':art['id'],'directive_id':'DP-01','proposed_text':'Versi baru yang lebih jelas.','rationale':'Menjawab pembimbing'})
        self.assertEqual(rev['status'],'proposed')
        accepted=self.call(o,'/api/revisions/decision',{'id':rev['id'],'decision':'accept'})
        self.assertEqual(accepted['artifact']['version'],2)
        directives=self.call(o,'/api/directives')
        self.assertEqual(directives[0]['status'],'addressed')

    def test_evidence_save_and_resolve_endpoint(self):
        o=self.opener(); self.project(o,'Evidence')
        self.call(o,'/api/literature/save',{'source':{'id':'src-api','type':'journal','title':'Paper','authors':['A'],'year':2025,'verified':True,'verification_status':'verified'}})
        from core import db
        src=next(x for x in db.list_sources(self.call(o,'/api/projects/active')['id']) if x['id']=='src-api')
        src['verified']=True; src['verification_status']='verified'; db.save_source(self.call(o,'/api/projects/active')['id'],src)
        self.call(o,'/api/evidence/save',{'source_id':'src-api','locator':'hal. 7','text':'Bukti halaman tujuh'})
        out=self.call(o,'/api/evidence/resolve',{'text':'Klaim [Brief: src-api, hal. 7].'})
        self.assertTrue(out['sentences'][0]['evidence_verified'])
        self.assertEqual(out['sentences'][0]['status'],'supported')


    def test_literature_save_cannot_self_certify_verified_status(self):
        o=self.opener(); self.project(o,'Integrity')
        self.call(o,'/api/literature/save',{'source':{'id':'fake-verified','type':'journal','title':'Unverified','authors':['X'],'year':2025,'verified':True,'verification_status':'verified'}})
        rows=self.call(o,'/api/sources')
        row=next(x for x in rows if x['id']=='fake-verified')
        self.assertFalse(row['verified'])
        self.assertEqual(row['verification_status'],'candidate')

    def test_docx_export_endpoint_returns_valid_document(self):
        o=self.opener(); self.project(o,'Judul Export')
        self.call(o,'/api/artifacts/save',{'kind':'chapter','title':'Bab I','content':'Isi pendahuluan.'})
        out=self.call(o,'/api/artifacts/export-docx',{})
        raw=base64.b64decode(out['base64'])
        self.assertTrue(raw.startswith(b'PK'))
        doc=Document(io.BytesIO(raw)); text='\n'.join(p.text for p in doc.paragraphs)
        self.assertIn('Isi pendahuluan.',text)

    def test_image_parse_without_key_stays_pending_not_fabricated(self):
        o=self.opener(); self.project(o,'Media')
        png=base64.b64encode(b'not-a-real-png-but-media-path').decode()
        out=self.call(o,'/api/parse/file',{'filename':'catatan.png','base64':png})
        self.assertTrue(out['success'])
        self.assertEqual(out['type'],'image')
        self.assertTrue(out['media_pending'])
        self.assertIn('OPENROUTER_API_KEY',out['media_error'])

    def test_defense_history_endpoint_summarizes_saved_scores(self):
        o=self.opener(); p=self.project(o,'Defense')
        from core import db
        db.save_defense_score(p['id'],'Q1','A1',2,'Kurang','metode')
        db.save_defense_score(p['id'],'Q2','A2',4,'Baik','teori')
        out=self.call(o,'/api/defense/history')
        self.assertEqual(out['summary']['attempts'],2)
        self.assertEqual(out['summary']['priority_weaknesses'][0]['name'],'metode')


if __name__=='__main__': unittest.main()
