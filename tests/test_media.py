import base64
import json
import unittest
from unittest.mock import patch

from core.openrouter_client import OpenRouterClient


class _Resp:
    def __init__(self, obj):
        self.body = json.dumps(obj).encode('utf-8')
    def __enter__(self): return self
    def __exit__(self, *args): return False
    def read(self): return self.body


class MediaClientTests(unittest.TestCase):
    def test_transcribe_uses_dedicated_openrouter_endpoint(self):
        seen = {}
        def fake(req, timeout=0):
            seen['url'] = req.full_url
            seen['payload'] = json.loads(req.data.decode())
            return _Resp({'text':'Arahan pembimbing harus masuk Bab II','usage':{'cost':0.001}})
        with patch('urllib.request.urlopen', fake):
            out = OpenRouterClient('sk-test').transcribe(b'RIFFdemo', 'bimbingan.wav', language='id')
        self.assertTrue(out['success'])
        self.assertEqual(out['text'], 'Arahan pembimbing harus masuk Bab II')
        self.assertTrue(seen['url'].endswith('/api/v1/audio/transcriptions'))
        self.assertEqual(seen['payload']['input_audio']['format'], 'wav')
        self.assertEqual(base64.b64decode(seen['payload']['input_audio']['data']), b'RIFFdemo')
        self.assertEqual(seen['payload']['language'], 'id')

    def test_vision_sends_data_uri_as_multimodal_content(self):
        seen = {}
        def fake(req, timeout=0):
            seen['payload'] = json.loads(req.data.decode())
            return _Resp({'model':'vision-test','choices':[{'message':{'content':'Catatan dosen meminta revisi variabel.'}}]})
        with patch('urllib.request.urlopen', fake):
            out = OpenRouterClient('sk-test').vision(b'PNGDATA', 'image/png', 'Baca catatan dosen ini')
        self.assertTrue(out['success'])
        parts = seen['payload']['messages'][-1]['content']
        self.assertEqual(parts[0]['type'], 'text')
        self.assertEqual(parts[1]['type'], 'image_url')
        self.assertTrue(parts[1]['image_url']['url'].startswith('data:image/png;base64,'))

    def test_media_without_api_key_fails_honestly(self):
        client = OpenRouterClient('')
        with patch.dict('os.environ', {'OPENROUTER_API_KEY':''}, clear=False):
            out = client.transcribe(b'x', 'x.wav')
        self.assertFalse(out['success'])
        self.assertIn('API_KEY', out['error'])


if __name__ == '__main__': unittest.main()
