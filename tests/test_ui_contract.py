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


    def test_pre_uat_controls_are_visible_in_workbench(self):
        html=Path('web/index.html').read_text(encoding='utf-8')
        js=Path('web/studio.js').read_text(encoding='utf-8')
        for term in ('fileClassification','extractDirectives','Research Brief','consistencyJson','preflightStatus'):
            self.assertIn(term,html+js)
        self.assertIn('classification',js)
        self.assertIn('/api/directives/extract',js)
        self.assertIn('/api/research-brief/create',js)
        self.assertIn('/api/consistency/save',js)
        self.assertIn('/api/preflight',js)
        for term in ('saveG1','saveG2','saveG3','saveG4','saveG5'):
            self.assertIn(term,html+js)


    def test_export_and_confidential_attachment_controls_are_user_ready(self):
        html=Path('web/index.html').read_text(encoding='utf-8')
        js=Path('web/studio.js').read_text(encoding='utf-8')
        self.assertIn('exportBibtex',html)
        self.assertIn('/api/references/export-bibtex',js)
        self.assertIn('hanya diproses lokal',js)

if __name__=='__main__': unittest.main()
