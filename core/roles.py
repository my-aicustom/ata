"""Generic thesis role engine. Internal roles are hidden behind outcome-oriented UX."""
from __future__ import annotations
from typing import Any, Dict, List, Optional
from .openrouter_client import OpenRouterClient
from . import db

ROLE_TIERS={'onboarding':'fast','topic_framer':'reasoning','source_finder':'reasoning','ledger':'fast','research_brief':'prose','matrix_synthesis':'reasoning','method_fit':'reasoning','drafting_assistant':'prose','critic':'reasoning','stats_reviewer':'reasoning','style_editor':'prose','abstract_writer':'prose','mock_examiner':'reasoning','defense_pack':'reasoning','contribution_builder':'prose','revision_editor':'prose'}
ROLE_PROMPTS={
'onboarding':'Bantu mahasiswa memetakan posisi tesis, target, bahan yang sudah ada, aturan prodi, metode, dan langkah tercepat berikutnya. Jangan berasumsi semua tesis berbentuk survei.',
'topic_framer':'Rumuskan masalah, 3 kandidat judul, RQ dan tujuan berpasangan, lalu nilai FINER 1-4. Tandai klaim fenomena yang belum punya data sebagai [PERLU DATA AWAL].',
'source_finder':'Bantu merumuskan query literatur dan kriteria inklusi/eksklusi. Jangan mengarang judul/DOI; daftar sumber aktual harus berasal dari pipeline OpenAlex/Crossref ATA.',
'ledger':'Ekstrak arahan pembimbing menjadi tabel ID | kutipan | arahan | prioritas MUST/SHOULD/NICE | target | status open. Jangan mengarang kutipan.',
'research_brief':'Buat brief sumber yang hanya memakai isi sumber yang diberikan. Cantumkan locator halaman/klausul. Jika tidak ada locator, tulis [PERLU CEK HALAMAN].',
'matrix_synthesis':'Sintesis sumber yang benar-benar diberikan menjadi pola temuan, perbedaan metode, gap, dan implikasi ke RQ. Jangan menambahkan studi dari ingatan.',
'method_fit':'Cocokkan RQ dengan metode, akses data, waktu, etika, dan aturan prodi. Bandingkan alternatif dan keluarkan Method Decision Record.',
'drafting_assistant':'Kembangkan poin mahasiswa menjadi draf akademik. Jangan mengarang data/sitasi. Klaim faktual tanpa bukti harus diberi [PERLU SUMBER].',
'critic':'Bertindak sebagai penguji skeptis: uji logika, bukti, konsistensi RQ-metode-kesimpulan, arahan pembimbing, dan overclaim. Prioritaskan MERAH/KUNING/HIJAU.',
'stats_reviewer':'Review output statistik/eksperimen yang diberikan. Dilarang mengarang atau menghitung angka baru. Fokus asumsi, validitas, dan interpretasi.',
'contribution_builder':'Hubungkan temuan nyata ke kontribusi ilmiah dan praktis. Jangan membuat kontribusi yang tidak ditopang Bab IV.',
'style_editor':'Rapikan bahasa akademik dan kohesi tanpa mengubah makna, angka, sitasi, atau klaim substantif.',
'abstract_writer':'Susun abstrak dari naskah final: masalah, tujuan, metode, temuan, kontribusi. Jangan mengisi temuan yang belum ada.',
'mock_examiner':'Ajukan SATU pertanyaan sidang per giliran dari titik lemah naskah. Setelah mahasiswa menjawab, beri skor 1-4 dan feedback singkat.',
'defense_pack':'Buat outline presentasi, bank pertanyaan, dan cheat-sheet berbasis naskah final serta titik lemah yang nyata.',
'revision_editor':'Revisi naskah hanya untuk menjawab arahan pembimbing yang diberikan. Pertahankan fakta, data, sitasi, dan suara penulis. Jangan menambah sumber atau angka baru. Keluarkan hanya naskah hasil revisi tanpa pembuka, tanpa markdown fence, tanpa komentar di luar naskah.'}

CORE_RULES='''ATURAN MUTLAK ATA:\n- Jangan fabrikasi penulis, judul, DOI, halaman, regulasi, data, kutipan, atau hasil statistik.\n- Bedakan sumber terverifikasi, kandidat, dan rujukan yang perlu cek manual.\n- Statistik/hasil eksperimen hanya boleh berasal dari output yang diberikan pengguna atau software nyata.\n- Arahan pembimbing yang berstatus MUST lebih tinggi prioritasnya daripada preferensi model.\n- Sistem membantu, mahasiswa tetap pemilik argumen dan keputusan penelitian.\n'''

class ThesisAgent:
    def __init__(self, api_key:Optional[str]=None): self.client=OpenRouterClient(api_key)
    def run_role(self,role:str,user_input:str,conversation_history:Optional[List[Dict[str,str]]]=None,api_key:Optional[str]=None,project_context:Optional[Dict[str,Any]]=None,project_id:Optional[str]=None)->Dict[str,Any]:
        role=role if role in ROLE_PROMPTS else 'onboarding'
        p=project_context or {}
        ctx=f"PROFIL TESIS\nProgram: {p.get('program','-')}\nTopik: {p.get('topic','-')}\nDomain: {p.get('domain','umum')}\nMetode: {p.get('method','belum ditentukan')}\nTahap: {p.get('stage','start')}\n"
        if project_id:
            directives=db.get_directives(project_id)
            if directives:
                ctx += 'ARAHAN PEMBIMBING:\n' + '\n'.join(f"- {d['id']} [{d['priority']}/{d['status']}]: {d['directive']}" for d in directives[:40])+'\n'
            if role in {'critic','mock_examiner','defense_pack','revision_editor','drafting_assistant','style_editor','abstract_writer'}:
                artifacts=db.list_artifacts(project_id)
                if artifacts:
                    budget=22000; chunks=[]; used=0
                    for a in artifacts:
                        piece=f"\n--- {a['title']} (v{a['version']}) ---\n{a.get('content','')}\n"
                        if used+len(piece)>budget: piece=piece[:max(0,budget-used)]
                        if piece: chunks.append(piece); used+=len(piece)
                        if used>=budget: break
                    ctx += 'NASKAH/ARTEFAK TERBARU:\n'+''.join(chunks)+'\n'
        system=CORE_RULES+'\n'+ctx+'\nPERAN:\n'+ROLE_PROMPTS[role]
        messages=[{'role':'system','content':system}]
        for m in conversation_history or []:
            if isinstance(m,dict) and m.get('role') in ('user','assistant') and isinstance(m.get('content'),str): messages.append(m)
        messages.append({'role':'user','content':user_input})
        client=OpenRouterClient(api_key) if api_key else self.client
        res=client.chat(messages,tier=ROLE_TIERS.get(role,'fast'))
        if res.get('success'): db.log_ai_usage(role,'execute_prompt',f"{len(res.get('content',''))} chars",project_id)
        res['tier']=ROLE_TIERS.get(role,'fast')
        return res
