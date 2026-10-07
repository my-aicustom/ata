import http.cookiejar
import json
import os
import socket
import tempfile
import threading
import unittest
import urllib.request


class ApiV3Tests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.tmp = tempfile.TemporaryDirectory()
        os.environ['ATA_DATA_DIR'] = cls.tmp.name
        from core import db
        db.reset_for_tests(); db.init_db()
        from server import make_server
        sock = socket.socket(); sock.bind(('127.0.0.1', 0)); cls.port = sock.getsockname()[1]; sock.close()
        cls.httpd = make_server('127.0.0.1', cls.port)
        cls.thread = threading.Thread(target=cls.httpd.serve_forever, daemon=True)
        cls.thread.start()

    @classmethod
    def tearDownClass(cls):
        cls.httpd.shutdown(); cls.httpd.server_close(); cls.tmp.cleanup()
        os.environ.pop('ATA_DATA_DIR', None)

    def opener(self):
        jar = http.cookiejar.CookieJar()
        return urllib.request.build_opener(urllib.request.HTTPCookieProcessor(jar))

    def call(self, opener, path, data=None):
        body = json.dumps(data).encode() if data is not None else None
        req = urllib.request.Request(f'http://127.0.0.1:{self.port}{path}', data=body, headers={'Content-Type':'application/json'} if body else {})
        with opener.open(req, timeout=10) as r:
            return json.loads(r.read().decode())

    def test_two_browser_sessions_do_not_see_each_others_projects(self):
        a = self.opener(); b = self.opener()
        pa = self.call(a, '/api/projects/create', {'student':'A','program':'S2','topic':'A','domain':'umum','method':'survey'})
        pb = self.call(b, '/api/projects/create', {'student':'B','program':'S2','topic':'B','domain':'umum','method':'interview'})
        la = self.call(a, '/api/projects')
        lb = self.call(b, '/api/projects')
        self.assertEqual([p['id'] for p in la], [pa['id']])
        self.assertEqual([p['id'] for p in lb], [pb['id']])

    def test_artifact_versions_through_api(self):
        o = self.opener()
        p = self.call(o, '/api/projects/create', {'student':'A','program':'S2','topic':'Artifact','domain':'umum','method':'survey'})
        v1 = self.call(o, '/api/artifacts/save', {'kind':'chapter','title':'Bab I','content':'satu'})
        v2 = self.call(o, '/api/artifacts/save', {'kind':'chapter','title':'Bab I','content':'dua'})
        self.assertEqual(v1['version'], 1)
        self.assertEqual(v2['version'], 2)
        listing = self.call(o, '/api/artifacts')
        self.assertEqual(listing[0]['content'], 'dua')

    def test_next_action_endpoint_uses_active_project(self):
        o = self.opener()
        self.call(o, '/api/projects/create', {'student':'A','program':'S2','topic':'Planner','domain':'umum','method':'survey'})
        action = self.call(o, '/api/next-action')
        self.assertEqual(action['phase'], 1)
        self.assertIn('judul', action['label'].lower())


if __name__ == '__main__':
    unittest.main()
