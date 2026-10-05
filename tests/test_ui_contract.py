from pathlib import Path
import unittest

class UIContractTests(unittest.TestCase):
    def test_home_is_outcome_driven_not_agent_menu(self):
        html=Path('web/index.html').read_text(encoding='utf-8')
        self.assertIn('Posisi tesis Anda sekarang?', html)
        self.assertIn('nextAction', html)
        self.assertIn('projectSelect', html)
        self.assertNotIn('Topic Framer</button>', html)
        self.assertNotIn('Stats Reviewer</button>', html)

    def test_workbench_contains_revision_evidence_and_artifacts(self):
        html=Path('web/index.html').read_text(encoding='utf-8')
        for term in ('Arahan Pembimbing','Bukti & Literatur','Naskah','Gate','Sidang','Revision Engine','Export DOCX','Defense History','Template kampus'):
            self.assertIn(term, html)

if __name__=='__main__': unittest.main()
