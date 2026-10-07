import io
import unittest
from docx import Document

class BibliographyTests(unittest.TestCase):
    def test_bibtex_export_contains_traceable_metadata(self):
        from core.bibliography import build_bibtex
        text=build_bibtex([{'id':'src1','type':'journal','title':'Judul Uji','authors':['Budi A','Citra B'],'year':2025,'doi':'10.1000/test','url':'https://doi.org/10.1000/test'}])
        self.assertIn('@article{src1',text)
        self.assertIn('title = {Judul Uji}',text)
        self.assertIn('doi = {10.1000/test}',text)
        self.assertIn('Budi A and Citra B',text)

    def test_docx_appends_only_referenced_bibliographic_sources(self):
        from core.export_docx import build_manuscript_docx
        project={'topic':'T','student':'A','program':'S2'}
        artifacts=[{'title':'Bab I','content':'Klaim [Brief: src1, hal. 1].','source_refs':['src1','DATA-1']}]
        sources=[
            {'id':'src1','type':'journal','title':'Paper Utama','authors':['Budi A'],'year':2025,'doi':'10.1000/x'},
            {'id':'src2','type':'journal','title':'Tidak Dipakai','authors':['C'],'year':2024},
            {'id':'DATA-1','type':'dataset','title':'Output Analisis','authors':[],'year':2026},
        ]
        raw=build_manuscript_docx(project,artifacts,sources=sources)
        doc=Document(io.BytesIO(raw)); text='\n'.join(p.text for p in doc.paragraphs)
        self.assertIn('Daftar Pustaka',text)
        self.assertIn('Paper Utama',text)
        self.assertNotIn('Tidak Dipakai',text)
        self.assertNotIn('Output Analisis',text)

if __name__=='__main__': unittest.main()
