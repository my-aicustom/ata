import re

def _norm(s): return re.sub(r'\s+',' ',s or '').strip()
def verify_quote(quote,source):
    q=_norm(quote); s=_norm(source)
    if not q or not s: return {'valid':False,'exact':False,'error':'quote/source kosong'}
    exact=q in s
    return {'valid':exact,'exact':exact,'quote':q,'message':'Kutipan ditemukan persis.' if exact else 'Kutipan tidak ditemukan persis; cek sumber dan halaman.'}
