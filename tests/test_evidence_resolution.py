import os
import tempfile
import unittest

from core import db
from core.evidence import resolve_draft_evidence, verify_quote_in_document


class EvidenceResolutionTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory(); self.old = os.environ.get('ATA_DATA_DIR')
        os.environ['ATA_DATA_DIR'] = self.tmp.name
        db.reset_for_tests(); db.init_db()
        self.pid = db.create_project('s1', {'student':'A','program':'S2','topic':'T'})
        db.save_source(self.pid, {'id':'src1','type':'journal','title':'Paper A','authors':['A'],'year':2025,'verified':True,'verification_status':'verified'})
        document='[PAGE 12]\nTemuan inti yang mendukung klaim.'
        verification=verify_quote_in_document('Temuan inti yang mendukung klaim.',document,'hal. 12')
        db.save_evidence(self.pid, 'src1', 'hal. 12', 'Temuan inti yang mendukung klaim.', verification=verification)
    def tearDown(self):
        if self.old is None: os.environ.pop('ATA_DATA_DIR', None)
        else: os.environ['ATA_DATA_DIR'] = self.old
        self.tmp.cleanup()

    def test_verified_source_and_locator_resolves_claim(self):
        out = resolve_draft_evidence(self.pid, '(M) Temuan ini kuat [Brief: src1, hal. 12].')
        claim = out['sentences'][0]
        self.assertEqual(claim['status'], 'supported')
        self.assertTrue(claim['evidence_verified'])
        self.assertEqual(claim['resolved'][0]['source_id'], 'src1')
        self.assertEqual(claim['resolved'][0]['locator'], 'hal. 12')

    def test_verified_source_without_matching_locator_is_partial(self):
        out = resolve_draft_evidence(self.pid, 'Temuan ini kuat [Brief: src1, hal. 99].')
        self.assertEqual(out['sentences'][0]['status'], 'partial')
        self.assertFalse(out['sentences'][0]['evidence_verified'])

    def test_candidate_source_never_becomes_verified_evidence(self):
        db.save_source(self.pid, {'id':'src2','type':'journal','title':'Paper B','authors':['B'],'year':2025,'verified':False})
        db.save_evidence(self.pid, 'src2', 'hal. 2', 'Candidate evidence')
        out = resolve_draft_evidence(self.pid, 'Klaim [Brief: src2, hal. 2].')
        self.assertEqual(out['sentences'][0]['status'], 'partial')
        self.assertFalse(out['sentences'][0]['evidence_verified'])


if __name__ == '__main__': unittest.main()
