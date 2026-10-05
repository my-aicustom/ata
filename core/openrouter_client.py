"""
OpenRouter Client for ATA v2 (Advanced Thesis Architect)
Integrates OpenRouter Free Tier models with automatic fallback.
"""
import os
import json
import urllib.request
import urllib.error
from typing import List, Dict, Any, Optional

def _configured_key():
    key = os.getenv("OPENROUTER_API_KEY")
    if key:
        return key
    from pathlib import Path
    config = Path(__file__).resolve().parent.parent / ".env.local"
    if config.is_file():
        for line in config.read_text(encoding="utf-8").splitlines():
            if line.startswith("OPENROUTER_API_KEY="):
                return line.split("=", 1)[1].strip()
    return ""

OPENROUTER_API_KEY = _configured_key()
OPENROUTER_URL = "https://openrouter.ai/api/v1/chat/completions"

DEFAULT_FREE_MODELS = [
    "google/gemma-4-31b-it:free",
    "nvidia/nemotron-3-super-120b-a12b:free",
    "qwen/qwen3.8-27b:free",
    "nvidia/nemotron-3-nano-omni-30b-a3b-reasoning:free",
    "nvidia/nemotron-3.5-lightning:free"
]

MODEL_TIERS = {
    "reasoning": [
        "nvidia/nemotron-3-nano-omni-30b-a3b-reasoning:free",
        "google/gemma-4-31b-it:free",
        "nvidia/nemotron-3-super-120b-a12b:free",
        "qwen/qwen3.8-27b:free"
    ],
    "prose": [
        "google/gemma-4-31b-it:free",
        "nvidia/nemotron-3-super-120b-a12b:free",
        "qwen/qwen3.8-27b:free",
        "google/gemma-4-26b-a4b-it:free"
    ],
    "fast": [
        "nvidia/nemotron-3.5-lightning:free",
        "qwen/qwen3.8-27b:free",
        "google/gemma-4-26b-a4b-it:free",
        "google/gemma-4-31b-it:free"
    ]
}

class OpenRouterClient:
    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key or os.getenv("OPENROUTER_API_KEY") or OPENROUTER_API_KEY or _configured_key()

    def get_key(self) -> str:
        return self.api_key or os.getenv("OPENROUTER_API_KEY") or _configured_key()

    def chat(
        self,
        messages: List[Dict[str, str]],
        model: Optional[str] = None,
        temperature: float = 0.4,
        max_tokens: int = 2048,
        tier: str = "fast"
    ) -> Dict[str, Any]:
        """
        Send a chat completion request to OpenRouter with fallback among free models.
        """
        effective_key = self.get_key()
        if not effective_key:
            return {'success': False, 'error': 'OPENROUTER_API_KEY belum dikonfigurasi', 'content': ''}
        models_to_try = [model] if model else MODEL_TIERS.get(tier, DEFAULT_FREE_MODELS)

        last_error = None
        for m in models_to_try:
            payload = {
                "model": m,
                "messages": messages,
                "temperature": temperature,
                "max_tokens": max_tokens
            }
            data = json.dumps(payload).encode("utf-8")
            req = urllib.request.Request(
                OPENROUTER_URL,
                data=data,
                headers={
                    "Authorization": f"Bearer {effective_key}",
                    "Content-Type": "application/json",
                    "HTTP-Referer": "http://localhost:4321",
                    "X-Title": "ATA v2 Thesis Architect"
                }
            )
            try:
                with urllib.request.urlopen(req, timeout=45) as resp:  # nosemgrep: python.lang.security.audit.dynamic-urllib-use-detected.dynamic-urllib-use-detected
                    res = json.loads(resp.read().decode("utf-8"))
                    content = res["choices"][0]["message"]["content"]
                    actual_model = res.get("model", m)
                    # Filter out moderation-only stub outputs
                    if content.strip().startswith("User Safety:") or len(content.strip()) < 15:
                        last_error = f"{actual_model} returned safety/empty stub"
                        continue
                    return {
                        "success": True,
                        "model": actual_model,
                        "content": content,
                        "raw": res
                    }
            except urllib.error.HTTPError as e:
                err_body = e.read().decode("utf-8")
                last_error = f"HTTP {e.code}: {err_body}"
                continue
            except Exception as e:
                last_error = str(e)
                continue

        return {
            "success": False,
            "error": last_error or "All free models failed to respond.",
            "content": f"ERROR: Gagal menghubungi OpenRouter API ({last_error})"
        }

if __name__ == "__main__":
    client = OpenRouterClient()
    print("Testing OpenRouter Client...")
    res = client.chat([
        {"role": "system", "content": "You are ATA Thesis Assistant."},
        {"role": "user", "content": "Tes satu baris saja: verifikasi status sistem."}
    ])
    print("Model:", res.get("model"))
    print("Content:", res.get("content"))
