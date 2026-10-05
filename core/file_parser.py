"""Local document extraction with page-aware PDF output; no shelling out to markitdown."""
from __future__ import annotations
import io, zipfile, xml.etree.ElementTree as ET
from typing import Dict

def parse_bytes(filename:str,data:bytes)->Dict:
    name=(filename or 'file.bin'); ext='.'+name.rsplit('.',1)[-1].lower() if '.' in name else ''
    if ext in {'.txt','.md','.csv','.json','.yaml','.yml'}:
        return {'type':'text','text':data.decode('utf-8',errors='replace')}
    if ext=='.pdf':
        try:
            from pypdf import PdfReader
            reader=PdfReader(io.BytesIO(data)); pages=[]
            for i,p in enumerate(reader.pages,1): pages.append(f'\n[PAGE {i}]\n'+(p.extract_text() or ''))
            return {'type':'document','text':'\n'.join(pages).strip(),'pages':len(reader.pages)}
        except Exception as e: return {'type':'error','error':f'PDF parser gagal: {e}'}
    if ext=='.docx':
        try:
            from docx import Document
            doc=Document(io.BytesIO(data)); return {'type':'document','text':'\n'.join(p.text for p in doc.paragraphs)}
        except Exception as e: return {'type':'error','error':f'DOCX parser gagal: {e}'}
    if ext in {'.png','.jpg','.jpeg','.webp'}: return {'type':'image','text':f'[GAMBAR: {name}] Visual perlu dianalisis oleh model multimodal; backend tidak mengarang deskripsi.'}
    if ext in {'.mp3','.wav','.m4a','.ogg','.aac'}: return {'type':'audio','text':f'[AUDIO: {name}] Transkripsi belum dikonfigurasi. Set provider transkripsi sebelum memakai audio sebagai bukti.'}
    return {'type':'binary','text':f'[BERKAS: {name}] Format belum didukung parser lokal.'}
