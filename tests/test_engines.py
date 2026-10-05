import unittest
from core.claims import parse_draft_claims
from core import gates

class EngineTests(unittest.TestCase):
    def test_locator_period_is_not_sentence(self):
        result = parse_draft_claims('(M+AI) LKPP transparan [Brief: OECD2024, hal. 12]. Publik percaya [Ledger: BH1-01].')
        self.assertEqual(len(result['sentences']), 2)
        self.assertEqual(result['author_origin']['ai_expanded_ratio'], 100)
        self.assertEqual(result['sentences'][0]['references'][0]['page'], '12')

    def test_missing_data_does_not_pass(self):
        self.assertFalse(gates.evaluate_g4()['passed'])
        self.assertEqual(gates.evaluate_g4()['progress'], 0)

    def test_tag_is_not_verified_evidence(self):
        result = parse_draft_claims('Klaim [Ledger: UNKNOWN].')
        self.assertFalse(result['sentences'][0]['evidence_verified'])

    def test_reference_after_period_belongs_to_claim(self):
        result = parse_draft_claims('LKPP terbuka. [Brief: OECD2024, hal. 12] Publik percaya.')
        self.assertEqual(len(result['sentences']), 2)
        self.assertEqual(result['sentences'][0]['references'][0]['page'], '12')

if __name__ == '__main__':
    unittest.main()
