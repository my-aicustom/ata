"""Supervisor revision workflow over immutable artifacts."""
from __future__ import annotations
import difflib
from typing import Any, Dict
from . import db


def text_diff(before: str, after: str) -> str:
    return '\n'.join(difflib.unified_diff(before.splitlines(),after.splitlines(),fromfile='sebelum',tofile='usulan',lineterm=''))


def propose_revision(project_id: str, directive_id: str|None, artifact_id: str, proposed_text: str, rationale: str='') -> Dict[str,Any]:
    artifact=db.get_artifact(project_id,artifact_id)
    if not artifact: raise ValueError('Artefak target tidak ditemukan')
    if not proposed_text.strip(): raise ValueError('Usulan revisi kosong')
    task=db.create_revision_task(project_id,directive_id,artifact['kind'],artifact['title'],artifact['content'],proposed_text,rationale)
    task['diff']=text_diff(task.get('before_text') or '',task.get('proposed_text') or '')
    task['artifact_id']=artifact_id
    return task


def list_revisions(project_id: str):
    out=[]
    for task in db.list_revision_tasks(project_id):
        task['diff']=text_diff(task.get('before_text') or '',task.get('proposed_text') or '')
        out.append(task)
    return out


def accept_revision(project_id: str, revision_id: str) -> Dict[str,Any]:
    task=db.get_revision_task(project_id,revision_id)
    if not task: raise ValueError('Revision task tidak ditemukan')
    if task['status']!='proposed': raise ValueError('Hanya usulan berstatus proposed yang bisa diterima')
    artifact=db.save_artifact(project_id,task['target_kind'] or 'draft',task['target_title'] or 'Revisi',task.get('proposed_text') or '',[])
    db.update_revision_task_status(project_id,revision_id,'accepted')
    if task.get('directive_id'):
        db.update_directive_status(project_id,task['directive_id'],'addressed',f"artifact:{artifact['id']}:v{artifact['version']}")
    return {'revision':db.get_revision_task(project_id,revision_id),'artifact':artifact}


def reject_revision(project_id: str, revision_id: str) -> Dict[str,Any]:
    task=db.get_revision_task(project_id,revision_id)
    if not task: raise ValueError('Revision task tidak ditemukan')
    if task['status'] not in {'open','proposed'}: raise ValueError('Revision task sudah diputuskan')
    db.update_revision_task_status(project_id,revision_id,'rejected')
    return db.get_revision_task(project_id,revision_id) or {}
