"""Generate a thesis DOCX from latest ATA artifacts, optionally on a campus template."""
from __future__ import annotations
import io
import re
from typing import Any, Dict, Iterable, List, Optional
from docx import Document
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.shared import Pt

_ROMAN={'i':1,'ii':2,'iii':3,'iv':4,'v':5,'vi':6,'vii':7,'viii':8,'ix':9,'x':10}

def _order(a: Dict[str,Any]):
    title=str(a.get('title') or '').strip(); m=re.match(r'(?i)^bab\s+([ivx]+|\d+)',title)
    if m:
        token=m.group(1).lower(); num=int(token) if token.isdigit() else _ROMAN.get(token,99)
        return (0,num,title.lower())
    return (1,999,title.lower())

def _replace_placeholders(doc: Document, project: Dict[str,Any]) -> None:
    values={'{TITLE}':project.get('topic',''),'{STUDENT}':project.get('student',''),'{PROGRAM}':project.get('program',''),'{ADVISOR}':project.get('advisor','') or '', '{CAMPUS}':project.get('campus','') or ''}
    for p in doc.paragraphs:
        text=p.text
        for k,v in values.items(): text=text.replace(k,str(v))
        if text!=p.text: p.text=text

def _append_content(doc: Document, content: str) -> None:
    for block in re.split(r'\n\s*\n',content.strip()):
        block=block.strip()
        if not block: continue
        if block.startswith('### '): doc.add_heading(block[4:].strip(),level=3)
        elif block.startswith('## '): doc.add_heading(block[3:].strip(),level=2)
        elif block.startswith('# '): doc.add_heading(block[2:].strip(),level=1)
        else:
            p=doc.add_paragraph(block)
            p.paragraph_format.space_after=Pt(6)

def build_manuscript_docx(project: Dict[str,Any], artifacts: Iterable[Dict[str,Any]], template_bytes: Optional[bytes]=None) -> bytes:
    doc=Document(io.BytesIO(template_bytes)) if template_bytes else Document()
    if template_bytes:
        _replace_placeholders(doc,project)
    else:
        p=doc.add_paragraph(); p.alignment=WD_ALIGN_PARAGRAPH.CENTER
        run=p.add_run(str(project.get('topic') or 'Tesis')); run.bold=True; run.font.size=Pt(16)
        p=doc.add_paragraph(); p.alignment=WD_ALIGN_PARAGRAPH.CENTER; p.add_run(str(project.get('student') or 'Mahasiswa'))
        p=doc.add_paragraph(); p.alignment=WD_ALIGN_PARAGRAPH.CENTER; p.add_run(str(project.get('program') or 'Program Magister'))
        if project.get('advisor'):
            p=doc.add_paragraph(); p.alignment=WD_ALIGN_PARAGRAPH.CENTER; p.add_run('Pembimbing: '+str(project['advisor']))
        doc.add_page_break()
    ordered=sorted(list(artifacts),key=_order)
    for idx,a in enumerate(ordered):
        doc.add_heading(str(a.get('title') or 'Bagian'),level=1)
        _append_content(doc,str(a.get('content') or ''))
        if idx < len(ordered)-1: doc.add_page_break()
    buf=io.BytesIO(); doc.save(buf); return buf.getvalue()
