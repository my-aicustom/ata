"""
server.py - High-Performance Local Backend Server for ATA v2
Serves the Dual-Pane Web UI and REST API endpoints.
Zero-dependency, uses Python stdlib http.server.
"""
import sys
import os
import json
import urllib.parse
from typing import Any, Dict, List
from http.server import ThreadingHTTPServer, SimpleHTTPRequestHandler

# Add core to sys.path
CORE_DIR = os.path.join(os.path.dirname(__file__), "core")
WEB_DIR = os.path.join(os.path.dirname(__file__), "web")
sys.path.insert(0, CORE_DIR)

from db import init_db, get_directives, update_directive_status, get_connection
from roles import ThesisAgent
from verify_citations import verify_citation, verify_doi_list, REAL_DOIS, FAKE_DOIS
from quote_check import verify_quote
from gates import get_all_gates
from claims import parse_draft_claims
from instances_manager import (
    list_instances, get_active_instance_id, set_active_instance_id,
    get_instance_details, create_instance, INSTANCES_DIR
)

FORBIDDEN_PHRASES = [
    "di era digital yang dinamis",
    "di era globalisasi",
    "di era disrupsi",
    "tidak dapat dipungkiri",
    "tidak dapat dimungkiri",
    "memegang peranan yang sangat penting",
    "memiliki andil yang sangat vital",
    "seiring dengan perkembangan zaman",
    "seiring berjalannya waktu",
    "secara komprehensif dan holistik",
    "sangat krusial",
    "sangat signifikan",
    "menjadi sebuah keniscayaan",
    "lebih lanjut, lebih jauh lagi",
    "tentunya, tentu saja",
    "bagaikan dua sisi mata uang",
    "patut menjadi perhatian bersama",
    "sudah barang tentu"
]

agent = ThesisAgent()

class ATAHandler(SimpleHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        if "directory" not in kwargs:
            kwargs["directory"] = WEB_DIR
        super().__init__(*args, **kwargs)

    def end_headers(self):
        self.send_header("X-Content-Type-Options", "nosniff")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")
        super().end_headers()

    def do_OPTIONS(self):
        self.send_response(200)
        self.end_headers()

    def send_json(self, data: Any, status: int = 200):
        body = json.dumps(data, ensure_ascii=False).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def resolve_path_and_query(self):
        raw_uri = self.headers.get('x-forwarded-uri') or self.path
        parsed = urllib.parse.urlparse(raw_uri)
        qs = urllib.parse.parse_qs(parsed.query)
        if '__path' in qs:
            resolved_path = qs['__path'][0]
        elif parsed.path.startswith('/api/index.py/'):
            resolved_path = parsed.path.replace('/api/index.py', '/api')
        else:
            resolved_path = parsed.path
        return resolved_path, parsed, qs

    def do_GET(self):
        path, parsed, qs = self.resolve_path_and_query()

        if path.startswith("/web/"):
            self.path = self.path[4:]
            return super().do_GET()

        if path == '/api/model/status':
            is_configured = bool(agent.client.get_key() if hasattr(agent.client, 'get_key') else (agent.client.api_key or os.getenv('OPENROUTER_API_KEY')))
            self.send_json({'provider': 'OpenRouter', 'tier': 'Free Tier', 'configured': is_configured})
            return

        if path == "/api/directives":
            directives = get_directives()
            self.send_json(directives)
            return

        elif path == "/api/instances":
            self.send_json(list_instances())
            return

        elif path == "/api/instances/active":
            active_id = get_active_instance_id()
            self.send_json(get_instance_details(active_id))
            return

        elif path == "/api/consistency":
            conn = get_connection()
            cur = conn.cursor()
            cur.execute("SELECT * FROM consistency_row")
            rows = [dict(r) for r in cur.fetchall()]
            conn.close()
            self.send_json(rows)
            return

        elif path == "/api/gates":
            self.send_json(get_all_gates())
            return

        elif path == "/api/knowledge/files":
            active_id = get_active_instance_id()
            inst_dir = os.path.join(INSTANCES_DIR, active_id)
            k_dir = inst_dir if os.path.isdir(inst_dir) else os.path.join(CORE_DIR, "knowledge")
            files = []
            if os.path.exists(k_dir):
                for f in sorted(os.listdir(k_dir)):
                    fp = os.path.join(k_dir, f)
                    if os.path.isfile(fp) and f.endswith('.md'):
                        files.append({"name": f, "size": os.path.getsize(fp)})
            self.send_json(files)
            return

        elif path == "/api/knowledge/file":
            name = qs.get('name', [''])[0]
            if not name or os.path.basename(name) != name or not name.endswith('.md'):
                self.send_json({'error': 'Invalid knowledge filename'}, 400)
                return
            active_id = get_active_instance_id()
            inst_dir = os.path.join(INSTANCES_DIR, active_id)
            fp = os.path.join(inst_dir, name) if os.path.isfile(os.path.join(inst_dir, name)) else os.path.join(CORE_DIR, 'knowledge', name)
            if not os.path.isfile(fp):
                self.send_json({'error': 'Knowledge not found'}, 404)
                return
            with open(fp, encoding='utf-8') as f:
                self.send_json({'name': name, 'content': f.read()})
            return

        elif path.startswith('/api/'):
            self.send_json({'error': 'Endpoint not found', 'received_path': path, 'raw_uri': raw_uri, 'self_path': self.path}, 404)
            return

        # Serve static web frontend (support both /file.ext and /web/file.ext)
        clean_path = path[4:] if path.startswith('/web/') else path
        if clean_path in ('', '/'):
            clean_path = '/index.html'

        rel_path = clean_path.lstrip('/')
        target_file = os.path.realpath(os.path.join(WEB_DIR, rel_path))
        web_root = os.path.realpath(WEB_DIR)

        if os.path.commonpath([web_root, target_file]) == web_root and os.path.isfile(target_file):
            content_type = self.guess_type(target_file)
            if clean_path.endswith('.css'):
                content_type = 'text/css; charset=utf-8'
            elif clean_path.endswith('.js'):
                content_type = 'application/javascript; charset=utf-8'
            elif clean_path.endswith('.html'):
                content_type = 'text/html; charset=utf-8'

            with open(target_file, "rb") as f:
                content = f.read()

            self.send_response(200)
            self.send_header("Content-Type", content_type)
            self.send_header("Content-Length", str(len(content)))
            self.end_headers()
            self.wfile.write(content)
            return

        self.send_error(404, "File not found")

    def do_POST(self):
        path, parsed, qs = self.resolve_path_and_query()
        origin = self.headers.get('Origin')
        host = self.headers.get('Host', '')
        if origin:
            valid_origins = [f"http://{host}", f"https://{host}"]
            if origin not in valid_origins and not origin.endswith('.vercel.app'):
                self.send_json({'error': 'Cross-origin writes are forbidden'}, 403)
                return
        try:
            length = int(self.headers.get("Content-Length", 0))
            if length < 0 or length > 15_000_000:
                self.send_json({'error': 'Body too large (maksimal 15 MB)'}, 413)
                return
            body = self.rfile.read(length).decode("utf-8") if length > 0 else "{}"
            req_data = json.loads(body)
            if not isinstance(req_data, dict):
                raise ValueError('Object required')
        except (ValueError, UnicodeDecodeError):
            self.send_json({'error': 'Invalid JSON object'}, 400)
            return
        for key in ('text', 'message', 'doi', 'quote', 'source'):
            if key in req_data and not isinstance(req_data[key], str):
                self.send_json({'error': key + ' must be text'}, 400)
                return

        if path == '/api/parse/file':
            filename = req_data.get("filename", "file.bin")
            b64_data = req_data.get("base64", "")
            if not b64_data:
                self.send_json({'error': 'Konten file (base64) kosong'}, 400)
                return
            import base64
            import tempfile
            import subprocess
            
            try:
                file_bytes = base64.b64decode(b64_data)
                ext = os.path.splitext(filename)[1].lower()
                
                # Handling rich documents with MarkItDown Protocol
                rich_doc_exts = {'.pdf', '.docx', '.pptx', '.xlsx', '.csv', '.html', '.xml'}
                img_exts = {'.png', '.jpg', '.jpeg', '.webp', '.svg'}
                audio_exts = {'.mp3', '.wav', '.m4a', '.ogg', '.aac'}
                
                if ext in rich_doc_exts:
                    temp_dir = os.path.join(os.path.dirname(__file__), "scratch")
                    os.makedirs(temp_dir, exist_ok=True)
                    temp_path = os.path.join(temp_dir, f"upload_{os.urandom(4).hex()}_{filename}")
                    with open(temp_path, "wb") as tf:
                        tf.write(file_bytes)
                    try:
                        res = subprocess.run(["markitdown", temp_path], capture_output=True, text=True, timeout=30)
                        extracted = res.stdout if res.returncode == 0 else f"[Peringatan MarkItDown: {res.stderr}]"
                    finally:
                        if os.path.exists(temp_path):
                            try:
                                os.remove(temp_path)
                            except Exception:
                                pass
                    self.send_json({
                        "success": True,
                        "type": "document",
                        "filename": filename,
                        "size": len(file_bytes),
                        "text": extracted.strip()
                    })
                    return
                elif ext in img_exts:
                    mime = 'image/png' if ext == '.png' else ('image/jpeg' if ext in ('.jpg', '.jpeg') else 'image/webp')
                    data_uri = f"data:{mime};base64,{b64_data}"
                    self.send_json({
                        "success": True,
                        "type": "image",
                        "filename": filename,
                        "size": len(file_bytes),
                        "data_uri": data_uri,
                        "text": f"[Lampiran Gambar: {filename} ({len(file_bytes)//1024} KB)]"
                    })
                    return
                elif ext in audio_exts:
                    self.send_json({
                        "success": True,
                        "type": "audio",
                        "filename": filename,
                        "size": len(file_bytes),
                        "text": f"[Lampiran Rekaman Suara / Audio Bimbingan: {filename} ({len(file_bytes)//1024} KB) - Siap ditranskrip & dianalisis]"
                    })
                    return
                else:
                    # Plain text
                    text = file_bytes.decode('utf-8', errors='ignore')
                    self.send_json({
                        "success": True,
                        "type": "text",
                        "filename": filename,
                        "size": len(file_bytes),
                        "text": text
                    })
                    return
            except Exception as ex:
                self.send_json({'error': f'Gagal memproses file: {str(ex)}'}, 500)
                return

        if path == '/api/instances/switch':
            inst_id = req_data.get("id")
            if not inst_id or not set_active_instance_id(inst_id):
                self.send_json({'error': 'Instance tidak ditemukan'}, 400)
                return
            self.send_json({'success': True, 'active': get_instance_details(inst_id)})
            return

        elif path == '/api/instances/create':
            try:
                new_id = create_instance(req_data)
                self.send_json({'success': True, 'id': new_id, 'active': get_instance_details(new_id)})
            except Exception as e:
                self.send_json({'error': f'Gagal membuat tesis: {str(e)}'}, 400)
            return

        if path == '/api/gates/assessment':
            gate = req_data.get('gate')
            data = req_data.get('data')
            if gate not in ('G1', 'G4', 'G5', 'G6') or not isinstance(data, dict):
                self.send_json({'error': 'Invalid gate assessment'}, 400)
                return
            conn = get_connection()
            with conn:
                conn.execute('CREATE TABLE IF NOT EXISTS gate_assessment (gate TEXT PRIMARY KEY, data_json TEXT NOT NULL)')
                conn.execute('INSERT OR REPLACE INTO gate_assessment VALUES (?, ?)', (gate, json.dumps(data)))
            conn.close()
            self.send_json({'success': True})
            return

        if path == "/api/directives/update":
            d_id = req_data.get("id")
            status = req_data.get("status")
            evidence_ref = req_data.get("evidence_ref")
            if isinstance(d_id, str) and status in ('open', 'addressed', 'clarify') and (evidence_ref is None or isinstance(evidence_ref, str)):
                conn = get_connection()
                exists = conn.execute('SELECT 1 FROM supervisor_directive WHERE id=?', (d_id,)).fetchone()
                conn.close()
                if not exists:
                    self.send_json({'error': 'Directive not found'}, 404)
                    return
                update_directive_status(d_id, status, evidence_ref)
                self.send_json({"success": True, "id": d_id, "status": status})
            else:
                self.send_json({"error": "Missing id or status"}, 400)
            return

        elif path == "/api/agent/chat":
            role = req_data.get("role", "ledger")
            message = req_data.get("message", "")
            history = req_data.get("history", [])
            from roles import ROLE_PROMPTS
            if not isinstance(role, str) or role not in ROLE_PROMPTS or not isinstance(history, list) or len(history) > 100 or any(
                not isinstance(m, dict) or m.get('role') not in ('user', 'assistant') or not isinstance(m.get('content'), str) for m in history
            ):
                self.send_json({'error': 'Invalid role or conversation history'}, 400)
                return
            custom_key = req_data.get("api_key")
            res = agent.run_role(role, message, history, api_key=custom_key)
            self.send_json(res)
            return

        elif path == "/api/verify/citation":
            doi = req_data.get("doi", "")
            res = verify_citation(doi)
            self.send_json(res)
            return

        elif path == "/api/verify/citation/test":
            real_res = verify_doi_list(REAL_DOIS)
            fake_res = verify_doi_list(FAKE_DOIS)
            self.send_json({
                "real_count": real_res["valid_count"],
                "fake_count": fake_res["invalid_count"],
                "real": real_res,
                "fake": fake_res
            })
            return

        elif path == "/api/verify/quote":
            quote = req_data.get("quote", "")
            source = req_data.get("source", "")
            if not quote.strip() or not source.strip():
                self.send_json({'error': 'Quote and source must be nonempty'}, 400)
                return
            res = verify_quote(quote, source)
            self.send_json(res)
            return

        elif path == "/api/audit/slop":
            text = req_data.get("text", "").lower()
            found = [p for p in FORBIDDEN_PHRASES if p.lower() in text]
            self.send_json({"found": found, "clean": len(found) == 0})
            return

        elif path == "/api/audit/claims":
            text = req_data.get("text", "")
            res = parse_draft_claims(text)
            self.send_json(res)
            return

        self.send_json({"error": "Endpoint not found"}, 404)

def run_server(port: int = 4321):
    init_db()
    server_address = ("127.0.0.1", port)
    httpd = ThreadingHTTPServer(server_address, ATAHandler)
    print(f"\n=======================================================")
    print(f"🚀 ATA v2 LOCAL SERVER RUNNING AT: http://localhost:{port}")
    print(f"=======================================================\n")
    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        print("\nShutting down server...")
        httpd.server_close()

if __name__ == "__main__":
    port = int(sys.argv[1]) if len(sys.argv) > 1 else 4321
    run_server(port)
