import http.client
import json
import os
import socket
import tempfile
import threading
import unittest
from pathlib import Path


class SecurityHardeningTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.tmp=tempfile.TemporaryDirectory(); os.environ['ATA_DATA_DIR']=cls.tmp.name
        from core import db
        db.reset_for_tests(); db.init_db()
        from server import make_server
        sock=socket.socket(); sock.bind(('127.0.0.1',0)); cls.port=sock.getsockname()[1]; sock.close()
        cls.httpd=make_server('127.0.0.1',cls.port); cls.thread=threading.Thread(target=cls.httpd.serve_forever,daemon=True); cls.thread.start()
    @classmethod
    def tearDownClass(cls):
        cls.httpd.shutdown(); cls.httpd.server_close(); cls.tmp.cleanup(); os.environ.pop('ATA_DATA_DIR',None)

    def test_browser_bundle_does_not_persist_openrouter_key_in_localstorage(self):
        js=Path(__file__).resolve().parents[1].joinpath('web','studio.js').read_text()
        self.assertNotIn('localStorage',js)
        self.assertNotIn('ata_openrouter_key',js)

    def test_cross_origin_post_is_rejected(self):
        conn=http.client.HTTPConnection('127.0.0.1',self.port,timeout=5)
        body=json.dumps({'student':'A','program':'S2','topic':'T','method':'interview'})
        conn.request('POST','/api/projects/create',body=body,headers={'Content-Type':'application/json','Origin':'https://evil.example','Host':f'127.0.0.1:{self.port}'})
        r=conn.getresponse(); payload=json.loads(r.read().decode()); conn.close()
        self.assertEqual(r.status,403)
        self.assertIn('origin',payload['error'].lower())

    def test_same_origin_post_is_allowed(self):
        conn=http.client.HTTPConnection('127.0.0.1',self.port,timeout=5)
        body=json.dumps({'student':'A','program':'S2','topic':'T','method':'interview'})
        origin=f'http://127.0.0.1:{self.port}'
        conn.request('POST','/api/projects/create',body=body,headers={'Content-Type':'application/json','Origin':origin,'Host':f'127.0.0.1:{self.port}'})
        r=conn.getresponse(); payload=json.loads(r.read().decode()); conn.close()
        self.assertEqual(r.status,200)
        self.assertTrue(payload['success'])

    def test_static_response_has_frame_and_content_security_headers(self):
        conn=http.client.HTTPConnection('127.0.0.1',self.port,timeout=5)
        conn.request('GET','/')
        r=conn.getresponse(); r.read(); headers={k.lower():v for k,v in r.getheaders()}; conn.close()
        self.assertEqual(headers.get('x-frame-options'),'DENY')
        self.assertIn("frame-ancestors 'none'",headers.get('content-security-policy',''))
        self.assertIn("connect-src 'self'",headers.get('content-security-policy',''))


if __name__=='__main__': unittest.main()
