"""
instances_manager.py - Multi-Thesis Workspace Engine for ATA v2/v3
Manages switching and creating instances across all S2 academic disciplines.
"""
import os
import yaml
import json
import shutil
from typing import Dict, List, Any

CORE_DIR = os.path.dirname(os.path.abspath(__file__))
DOMAIN_DIR = os.path.join(CORE_DIR, "domain")
METHOD_DIR = os.path.join(CORE_DIR, "method")

if os.environ.get("VERCEL"):
    INSTANCES_DIR = "/tmp/instances"
    STATE_FILE = "/tmp/.active_instance"
    src_inst = os.path.join(CORE_DIR, "instances")
    if os.path.exists(src_inst) and not os.path.exists(INSTANCES_DIR):
        try:
            shutil.copytree(src_inst, INSTANCES_DIR)
        except Exception:
            pass
else:
    INSTANCES_DIR = os.path.join(CORE_DIR, "instances")
    STATE_FILE = os.path.join(CORE_DIR, ".active_instance")

DOMAIN_MAP = {
    "forensik-digital": "informatika",
    "informatika": "informatika",
    "komunikasi-korporat": "komunikasi",
    "komunikasi": "komunikasi",
    "umum": "umum"
}

METHOD_MAP = {
    "system_experiment": "system-experiment",
    "system-experiment": "system-experiment",
    "dsr": "dsr",
    "survey": "survey",
    "interview": "interview",
    "content_analysis": "content-analysis",
    "content-analysis": "content-analysis"
}

def get_domain_profile(domain_key: str) -> str:
    mapped = DOMAIN_MAP.get(domain_key, domain_key)
    fp = os.path.join(DOMAIN_DIR, f"{mapped}.md")
    if not os.path.exists(fp):
        fp = os.path.join(DOMAIN_DIR, "umum.md")
    if os.path.exists(fp):
        with open(fp, "r", encoding="utf-8") as f:
            return f.read()
    return ""

def get_method_pack(method_key: str) -> str:
    mapped = METHOD_MAP.get(method_key, method_key)
    fp = os.path.join(METHOD_DIR, f"{mapped}.md")
    if os.path.exists(fp):
        with open(fp, "r", encoding="utf-8") as f:
            return f.read()
    return ""

def get_active_instance_id() -> str:
    if os.path.exists(STATE_FILE):
        try:
            with open(STATE_FILE, "r", encoding="utf-8") as f:
                name = f.read().strip()
                if name and os.path.isdir(os.path.join(INSTANCES_DIR, name)):
                    return name
        except Exception:
            pass
    return "lkpp-komunikasi"

def set_active_instance_id(instance_id: str) -> bool:
    target = os.path.join(INSTANCES_DIR, instance_id)
    if not os.path.isdir(target):
        return False
    with open(STATE_FILE, "w", encoding="utf-8") as f:
        f.write(instance_id)
    return True

def list_instances() -> List[Dict[str, Any]]:
    active_id = get_active_instance_id()
    instances = []
    
    if not os.path.exists(INSTANCES_DIR):
        return []

    for name in sorted(os.listdir(INSTANCES_DIR)):
        if name.startswith("_") or not os.path.isdir(os.path.join(INSTANCES_DIR, name)):
            continue
        yaml_path = os.path.join(INSTANCES_DIR, name, "tesis.yaml")
        meta = {
            "id": name,
            "name": name.replace("-", " ").title(),
            "student": "Mahasiswa S2",
            "program": "Program Magister (S2)",
            "advisor": "Dosen Pembimbing",
            "topic": "Penelitian Tesis",
            "domain": "umum",
            "method": "survey",
            "active": (name == active_id)
        }
        if os.path.exists(yaml_path):
            try:
                with open(yaml_path, "r", encoding="utf-8") as f:
                    data = yaml.safe_load(f) or {}
                    meta["name"] = data.get("jenjang_prodi", meta["name"])
                    meta["student"] = data.get("mahasiswa", meta["student"])
                    meta["program"] = data.get("jenjang_prodi", meta["program"])
                    meta["advisor"] = data.get("pembimbing", meta["advisor"])
                    meta["topic"] = data.get("topik", meta["topic"])
                    meta["domain"] = data.get("domain", meta["domain"])
                    methods = data.get("method_packs", [])
                    meta["method"] = methods[0] if isinstance(methods, list) and methods else "survey"
            except Exception:
                pass
        instances.append(meta)
    return instances

def get_instance_details(instance_id: str) -> Dict[str, Any]:
    inst_dir = os.path.join(INSTANCES_DIR, instance_id)
    if not os.path.isdir(inst_dir):
        inst_dir = os.path.join(INSTANCES_DIR, "lkpp-komunikasi")
    
    yaml_path = os.path.join(inst_dir, "tesis.yaml")
    config = {}
    if os.path.exists(yaml_path):
        try:
            with open(yaml_path, "r", encoding="utf-8") as f:
                config = yaml.safe_load(f) or {}
        except Exception:
            pass

    # Read knowledge docs
    docs = []
    for f in sorted(os.listdir(inst_dir)):
        if f.endswith(".md"):
            fp = os.path.join(inst_dir, f)
            docs.append({
                "name": f,
                "size": os.path.getsize(fp)
            })

    return {
        "id": instance_id,
        "config": config,
        "docs": docs
    }

def create_instance(data: Dict[str, Any]) -> str:
    raw_name = data.get("id") or data.get("topic") or "tesis-baru"
    # Slugify
    slug = "".join(c if c.isalnum() else "-" for c in raw_name.lower()).strip("-")
    while "--" in slug:
        slug = slug.replace("--", "-")
    if not slug:
        slug = "tesis-baru"
    
    target_dir = os.path.join(INSTANCES_DIR, slug)
    if os.path.exists(target_dir):
        slug = f"{slug}-1"
        target_dir = os.path.join(INSTANCES_DIR, slug)
        
    os.makedirs(target_dir, exist_ok=True)
    
    # Template copy
    template_dir = os.path.join(INSTANCES_DIR, "_template")
    if os.path.exists(template_dir):
        for f in os.listdir(template_dir):
            src = os.path.join(template_dir, f)
            dst = os.path.join(target_dir, f)
            if os.path.isfile(src):
                shutil.copy2(src, dst)
                
    # Write tesis.yaml
    tesis_data = {
        "kode": slug,
        "mahasiswa": data.get("student", "Mahasiswa S2"),
        "jenjang_prodi": data.get("program", "S2 Program Studi"),
        "persona": data.get("persona", "Mahasiswa S2 yang menyusun tesis"),
        "jam_per_minggu": int(data.get("hours", 8)),
        "pembimbing": data.get("advisor", "Dosen Pembimbing"),
        "kode_sesi": data.get("advisor_code", "DP"),
        "topik": data.get("topic", "Topik Penelitian Tesis"),
        "domain": DOMAIN_MAP.get(data.get("domain", "umum"), data.get("domain", "umum")),
        "method_packs": [METHOD_MAP.get(data.get("method", "survey"), data.get("method", "survey"))],
        "status": "aktif",
        "tenggat": data.get("deadline", "Target 6 bulan"),
        "bahasa_tesis": "Indonesia",
        "lembaga_kasus": data.get("institution", "Objek Penelitian"),
        "peneliti_orang_dalam": bool(data.get("insider", False))
    }
    
    with open(os.path.join(target_dir, "tesis.yaml"), "w", encoding="utf-8") as f:
        yaml.dump(tesis_data, f, allow_unicode=True, default_flow_style=False)
        
    # Write initial 01-profil-tesis.md
    profil_content = f"""# Profil Tesis: {tesis_data['topik']}

Mahasiswa: {tesis_data['mahasiswa']}
Program Studi: {tesis_data['jenjang_prodi']}
Pembimbing: {tesis_data['pembimbing']}
Domain: {tesis_data['domain']}
Metode: {', '.join(tesis_data['method_packs'])}

## Rumusan Masalah
1. Bagaimana fenomena dan tantangan utama dalam {tesis_data['topik']}?
2. Bagaimana analisis empiris dan pengujian metode {', '.join(tesis_data['method_packs'])} terhadap objek studi?
3. Apa rekomendasi kebijakan dan kontribusi akademik yang dihasilkan?

## Kerangka Teori & Standar
- Standar acuan bidang {tesis_data['domain']}
- Literatur primer jurnal terakreditasi internasional & SINTA
"""
    with open(os.path.join(target_dir, "01-profil-tesis.md"), "w", encoding="utf-8") as f:
        f.write(profil_content)
        
    set_active_instance_id(slug)
    return slug
