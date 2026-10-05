"""
verify_citations.py - Deterministik Citation Verifier for ATA v2
Verifies DOIs and citation metadata against official Crossref & OpenAlex APIs.
Zero LLM tokens required. 100% deterministic.
"""
import sys
import json
import urllib.request
import urllib.error
import urllib.parse
from typing import Dict, Any, List, Optional

if sys.stdout.encoding and sys.stdout.encoding.lower() != 'utf-8':
    try:
        sys.stdout.reconfigure(encoding='utf-8')
    except Exception:
        pass

POLITE_EMAIL = "setgraph69@gmail.com"

def check_doi_crossref(doi: str) -> Dict[str, Any]:
    """Check DOI via Crossref API"""
    clean_doi = doi.strip()
    if clean_doi.startswith("http"):
        clean_doi = clean_doi.split("doi.org/")[-1]

    url = f"https://api.crossref.org/works/{urllib.parse.quote(clean_doi)}"
    req = urllib.request.Request(url, headers={
        "User-Agent": f"ATAv2Verifier/1.0 (mailto:{POLITE_EMAIL})"
    })
    try:
        with urllib.request.urlopen(req, timeout=10) as resp:  # nosemgrep: python.lang.security.audit.dynamic-urllib-use-detected.dynamic-urllib-use-detected
            data = json.loads(resp.read().decode("utf-8"))
            item = data.get("message", {})
            title = item.get("title", [""])[0] if item.get("title") else ""
            authors = [
                f"{a.get('family', '')}, {a.get('given', '')}".strip()
                for a in item.get("author", [])
            ]
            year = None
            if "published-print" in item and "date-parts" in item["published-print"]:
                year = item["published-print"]["date-parts"][0][0]
            elif "published-online" in item and "date-parts" in item["published-online"]:
                year = item["published-online"]["date-parts"][0][0]
            elif "issued" in item and "date-parts" in item["issued"]:
                year = item["issued"]["date-parts"][0][0]

            return {
                "valid": True,
                "source": "crossref",
                "doi": clean_doi,
                "title": title,
                "authors": authors,
                "year": year,
                "publisher": item.get("publisher", ""),
                "container_title": item.get("container-title", [""])[0] if item.get("container-title") else ""
            }
    except urllib.error.HTTPError as e:
        if e.code == 404:
            return {"valid": False, "source": "crossref", "doi": clean_doi, "error": "DOI not found (404)"}
        return {"valid": False, "source": "crossref", "doi": clean_doi, "error": f"HTTP {e.code}"}
    except Exception as e:
        return {"valid": False, "source": "crossref", "doi": clean_doi, "error": str(e)}

def check_doi_openalex(doi: str) -> Dict[str, Any]:
    """Check DOI via OpenAlex API"""
    clean_doi = doi.strip()
    if not clean_doi.startswith("https://doi.org/") and not clean_doi.startswith("http://"):
        clean_doi = f"https://doi.org/{clean_doi}"

    url = f"https://api.openalex.org/works/{clean_doi}?mailto={POLITE_EMAIL}"
    req = urllib.request.Request(url, headers={
        "User-Agent": f"ATAv2Verifier/1.0 (mailto:{POLITE_EMAIL})"
    })
    try:
        with urllib.request.urlopen(req, timeout=10) as resp:  # nosemgrep: python.lang.security.audit.dynamic-urllib-use-detected.dynamic-urllib-use-detected
            item = json.loads(resp.read().decode("utf-8"))
            authors = [
                a.get("author", {}).get("display_name", "")
                for a in item.get("authorships", [])
            ]
            return {
                "valid": True,
                "source": "openalex",
                "doi": item.get("doi", clean_doi),
                "title": item.get("display_name", item.get("title", "")),
                "authors": authors,
                "year": item.get("publication_year"),
                "cited_by_count": item.get("cited_by_count", 0),
                "is_oa": item.get("open_access", {}).get("is_oa", False)
            }
    except urllib.error.HTTPError as e:
        if e.code == 404:
            return {"valid": False, "source": "openalex", "doi": clean_doi, "error": "Work not found in OpenAlex (404)"}
        return {"valid": False, "source": "openalex", "doi": clean_doi, "error": f"HTTP {e.code}"}
    except Exception as e:
        return {"valid": False, "source": "openalex", "doi": clean_doi, "error": str(e)}

def verify_citation(doi: str) -> Dict[str, Any]:
    """Verify single citation across Crossref and OpenAlex"""
    res_cr = check_doi_crossref(doi)
    if res_cr["valid"]:
        return res_cr
    res_oa = check_doi_openalex(doi)
    if res_oa["valid"]:
        return res_oa
    return {
        "valid": False,
        "doi": doi,
        "error": f"Crossref: {res_cr.get('error')}; OpenAlex: {res_oa.get('error')}"
    }

def verify_doi_list(dois: List[str]) -> Dict[str, Any]:
    """Verify list of DOIs and return structured report"""
    valid_list = []
    invalid_list = []
    for d in dois:
        clean = d.strip()
        if not clean:
            continue
        res = verify_citation(clean)
        if res["valid"]:
            valid_list.append(res)
        else:
            invalid_list.append(res)
    return {
        "total": len(valid_list) + len(invalid_list),
        "valid_count": len(valid_list),
        "invalid_count": len(invalid_list),
        "valid": valid_list,
        "invalid": invalid_list
    }

# ----------------- Acceptance Test Suite -----------------
REAL_DOIS = [
    "10.1016/j.jbusres.2007.01.008",       # Fombrun & van Riel (2007)
    "10.1111/j.1467-6486.2006.00614.x",    # Corporate Reputation Review
    "10.1080/1553118x.2011.634869",        # Public Relations Journal
    "10.1111/puar.12068",                  # Public Administration Review (Trust)
    "10.1016/j.pubrev.2015.05.006",        # Public Relations Review (Crisis Communication)
]

FAKE_DOIS = [
    "10.1016/j.fakebusres.9999.01.008",
    "10.1111/j.fake-reputation-2099.99999.x",
    "10.1080/nonexistent-journal-pr-fake",
    "10.9999/hallucinated.doi.123456",
    "10.1234/buhenni.thesis.hoax.001",
]

def run_acceptance_test():
    print("=== ATA v2 ACCEPTANCE TEST: verify_citations.py ===")
    print(f"Testing {len(REAL_DOIS)} Real DOIs and {len(FAKE_DOIS)} Fake DOIs...\n")

    real_results = verify_doi_list(REAL_DOIS)
    print(f"[Real DOIs Check] Valid: {real_results['valid_count']}/{real_results['total']}")
    for r in real_results["valid"]:
        print(f"  [OK] {r['doi']} -> {r['title'][:60]} ({r['year']})")
    for r in real_results["invalid"]:
        print(f"  [MISSING] {r['doi']} -> {r.get('error')}")

    fake_results = verify_doi_list(FAKE_DOIS)
    print(f"\n[Fake DOIs Check] Caught Invalid: {fake_results['invalid_count']}/{fake_results['total']}")
    for f in fake_results["invalid"]:
        print(f"  [CAUGHT] {f['doi']} -> {f['error']}")
    for f in fake_results["valid"]:
        print(f"  [FALSE POSITIVE] {f['doi']} -> {f.get('title')}")

    success = (real_results["invalid_count"] == 0) and (fake_results["valid_count"] == 0)
    print(f"\nACCEPTANCE TEST STATUS: {'PASSED (100% ACCURATE)' if success else 'FAILED'}")
    return success

if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "--test":
        sys.exit(0 if run_acceptance_test() else 1)
    elif len(sys.argv) > 1:
        doi = sys.argv[1]
        print(json.dumps(verify_citation(doi), indent=2))
    else:
        print("Usage: python verify_citations.py <DOI> OR python verify_citations.py --test")
