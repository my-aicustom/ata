import json
import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


class PreflightCliTests(unittest.TestCase):
    def test_cli_reports_code_readiness_and_live_tests(self):
        with tempfile.TemporaryDirectory() as td:
            env=os.environ.copy()
            env['ATA_DB_PATH']=str(Path(td)/'ata.db')
            proc=subprocess.run([sys.executable,'scripts/preflight.py'],cwd=Path(__file__).resolve().parents[1],env=env,capture_output=True,text=True,timeout=20)
        self.assertEqual(proc.returncode,0,proc.stderr)
        data=json.loads(proc.stdout)
        self.assertTrue(data['code_ready'])
        self.assertIn('live_tests_remaining',data)
        self.assertGreaterEqual(len(data['live_tests_remaining']),2)


if __name__=='__main__': unittest.main()
