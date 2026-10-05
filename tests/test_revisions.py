import os
import tempfile
import unittest

from core import db
from core.revisions import propose_revision, accept_revision, reject_revision


class RevisionTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.old = os.environ.get('ATA_DATA_DIR')
        os.environ['ATA_DATA_DIR'] = self.tmp.name
        db.reset_for_tests(); db.init_db()
        self.pid = db.create_project('s1', {'student':'A','program':'S2','topic':'T','method':'interview'})
        db.upsert_directives(self.pid, [{'id':'DP1-01','quote':'Perjelas gap','directive':'Perjelas research gap','priority':'MUST','status':'open'}])
        self.art = db.save_artifact(self.pid, 'chapter', 'Bab II', 'Teks lama tentang gap.')
    def tearDown(self):
        if self.old is None: os.environ.pop('ATA_DATA_DIR', None)
        else: os.environ['ATA_DATA_DIR'] = self.old
        self.tmp.cleanup()

    def test_accept_revision_creates_new_artifact_version_and_addresses_directive(self):
        task = propose_revision(self.pid, 'DP1-01', self.art['id'], 'Teks baru yang menjelaskan gap dengan jelas.', 'Menjawab arahan pembimbing.')
        self.assertIn('-Teks lama tentang gap.', task['diff'])
        self.assertIn('+Teks baru yang menjelaskan gap dengan jelas.', task['diff'])
        accepted = accept_revision(self.pid, task['id'])
        self.assertEqual(accepted['artifact']['version'], 2)
        self.assertEqual(db.list_artifacts(self.pid)[0]['content'], 'Teks baru yang menjelaskan gap dengan jelas.')
        directive = db.get_directives(self.pid)[0]
        self.assertEqual(directive['status'], 'addressed')
        self.assertIn('artifact:', directive['evidence_ref'])

    def test_reject_revision_does_not_change_artifact_or_directive(self):
        task = propose_revision(self.pid, 'DP1-01', self.art['id'], 'Usulan ditolak.', 'Tidak sesuai.')
        reject_revision(self.pid, task['id'])
        self.assertEqual(db.list_artifacts(self.pid)[0]['version'], 1)
        self.assertEqual(db.get_directives(self.pid)[0]['status'], 'open')
        self.assertEqual(db.get_revision_task(self.pid, task['id'])['status'], 'rejected')


if __name__ == '__main__': unittest.main()
