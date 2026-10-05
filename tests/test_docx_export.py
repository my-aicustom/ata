import io
import unittest
from docx import Document
from core.export_docx import build_manuscript_docx


class DocxExportTests(unittest.TestCase):
    def test_builds_valid_docx_with_ordered_latest_artifacts(self):
        project={'topic':'Judul Tesis','student':'Nama Mahasiswa','program':'S2 Ilmu Komunikasi','advisor':'Dr. Pembimbing'}
        artifacts=[
            {'kind':'chapter','title':'Bab II','version':2,'content':'Isi bab dua terbaru.'},
            {'kind':'chapter','title':'Bab I','version':3,'content':'Isi bab satu terbaru.'},
            {'kind':'note','title':'Catatan','version':1,'content':'Bukan bab utama.'},
        ]
        raw=build_manuscript_docx(project, artifacts)
        self.assertTrue(raw.startswith(b'PK'))
        doc=Document(io.BytesIO(raw))
        text='\n'.join(p.text for p in doc.paragraphs)
        self.assertIn('Judul Tesis', text)
        self.assertIn('Isi bab satu terbaru.', text)
        self.assertLess(text.index('Bab I'), text.index('Bab II'))


if __name__ == '__main__': unittest.main()
