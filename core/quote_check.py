"""
quote_check.py - Exact and Fuzzy Quote Verifier for ATA v2
Ensures direct quotes in drafts match source literature verbatim.
Detects tampered quotes (even 1 word altered).
"""
import sys
import re
import difflib
from typing import Dict, Any, List, Tuple

if sys.stdout.encoding and sys.stdout.encoding.lower() != 'utf-8':
    try:
        sys.stdout.reconfigure(encoding='utf-8')
    except Exception:
        pass

def normalize_text(text: str) -> str:
    """Normalize whitespace and punctuation for resilient matching"""
    t = text.lower()
    t = re.sub(r'[\r\n\t]+', ' ', t)
    t = re.sub(r'\s+', ' ', t)
    return t.strip()

def verify_quote(quote: str, source_text: str, threshold: float = 0.98) -> Dict[str, Any]:
    """
    Verify if a quote exists verbatim in source_text.
    If not exact match, checks fuzzy similarity to detect single-word modifications.
    """
    norm_quote = normalize_text(quote)
    norm_source = normalize_text(source_text)

    # 1. Exact Substring Match
    if norm_quote in norm_source:
        idx = norm_source.find(norm_quote)
        return {
            "valid": True,
            "match_type": "exact",
            "similarity": 1.0,
            "quote": quote,
            "message": "Quote matches source text verbatim 100%."
        }

    # 2. Windowed Fuzzy Matching to detect altered single word
    quote_words = norm_quote.split()
    quote_len = len(quote_words)
    source_words = norm_source.split()
    
    best_ratio = 0.0
    best_window = ""
    
    for size in [quote_len - 1, quote_len, quote_len + 1]:
        if size < 2:
            continue
        for i in range(0, len(source_words) - size + 1):
            chunk = " ".join(source_words[i:i + size])
            ratio = difflib.SequenceMatcher(None, norm_quote, chunk).ratio()
            if ratio > best_ratio:
                best_ratio = ratio
                best_window = chunk

    # If it's very close but not exact (e.g. 1 word changed or slight typo)
    if best_ratio >= 0.75:
        return {
            "valid": False,
            "match_type": "tampered_or_inexact",
            "similarity": round(best_ratio, 3),
            "quote": quote,
            "closest_source_match": best_window,
            "message": f"Kutipan TIDAK persis sama (kemiripan: {round(best_ratio*100, 1)}%). Diduga ada kata yang dimodifikasi!"
        }

    return {
        "valid": False,
        "match_type": "not_found",
        "similarity": round(best_ratio, 3),
        "quote": quote,
        "message": "Kutipan tidak ditemukan dalam teks sumber!"
    }

# ----------------- Acceptance Test Suite -----------------
SOURCE_CORPUS = """
Corporate reputation is a collective representation of a firm's past actions and results
that describes the firm's ability to deliver valued outcomes to multiple stakeholders.
According to van Riel and Fombrun (2007), public institutions face a severe legitimacy crisis
when communication channels are intermediated by untrusted third parties.
Kepercayaan publik terhadap lembaga pengadaan pemerintah bergantung pada transparansi sistem e-katalog.
Humas pemerintah harus mengedepankan model komunikasi dua arah simetris untuk memitigasi isu krisis.
"""

ORIGINAL_QUOTES = [
    "Corporate reputation is a collective representation of a firm's past actions and results",
    "describes the firm's ability to deliver valued outcomes to multiple stakeholders",
    "public institutions face a severe legitimacy crisis",
    "when communication channels are intermediated by untrusted third parties",
    "Kepercayaan publik terhadap lembaga pengadaan pemerintah bergantung pada transparansi",
]

TAMPERED_QUOTES = [
    # 1 word changed: "collective" -> "individual"
    "Corporate reputation is a individual representation of a firm's past actions and results",
    # 1 word changed: "valued" -> "financial"
    "describes the firm's ability to deliver financial outcomes to multiple stakeholders",
    # 1 word changed: "severe" -> "mild"
    "public institutions face a mild legitimacy crisis",
    # 1 word changed: "untrusted" -> "professional"
    "when communication channels are intermediated by professional third parties",
    # 1 word changed: "transparansi" -> "akuntabilitas"
    "Kepercayaan publik terhadap lembaga pengadaan pemerintah bergantung pada akuntabilitas",
]

def run_acceptance_test():
    print("=== ATA v2 ACCEPTANCE TEST: quote_check.py ===")
    print(f"Testing {len(ORIGINAL_QUOTES)} Original Quotes and {len(TAMPERED_QUOTES)} Tampered Quotes (1 word altered)...\n")

    orig_passed = 0
    for q in ORIGINAL_QUOTES:
        res = verify_quote(q, SOURCE_CORPUS)
        if res["valid"]:
            orig_passed += 1
            print(f"  [OK] ORIGINAL MATCH: '{q[:50]}...'")
        else:
            print(f"  [FAIL] FALSE REJECTION: '{q[:50]}...'")

    tampered_caught = 0
    for q in TAMPERED_QUOTES:
        res = verify_quote(q, SOURCE_CORPUS)
        if not res["valid"] and res["match_type"] == "tampered_or_inexact":
            tampered_caught += 1
            print(f"  [CAUGHT] TAMPERING DETECTED ({round(res['similarity']*100, 1)}%): '{q[:50]}...'")
        else:
            print(f"  [FAIL] FAILED TO DETECT TAMPERING: '{q[:50]}...'")

    success = (orig_passed == len(ORIGINAL_QUOTES)) and (tampered_caught == len(TAMPERED_QUOTES))
    print(f"\nACCEPTANCE TEST STATUS: {'PASSED (100% SENSITIVITY)' if success else 'FAILED'}")
    return success

if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "--test":
        sys.exit(0 if run_acceptance_test() else 1)
    else:
        print("Usage: python quote_check.py --test")
