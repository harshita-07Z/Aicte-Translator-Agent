"""
Quick status check for the AICTE Translator Agent.
Run: python check_status.py
"""
import json
import os
import sys
import urllib.request

results = {}

# ── 1. Frontend ───────────────────────────────────────────────────
try:
    r = urllib.request.urlopen("http://localhost:8000/", timeout=4)
    results["Frontend (/)"] = ("OK", f"HTTP {r.status} - page served")
except Exception as e:
    results["Frontend (/)"] = ("FAIL", str(e))

# ── 2. Health endpoint ────────────────────────────────────────────
try:
    r = urllib.request.urlopen("http://localhost:8000/api/health", timeout=4)
    data = json.loads(r.read())
    watsonx = data.get("watsonx_connected", False)
    vector  = data.get("vector_store_ready", False)
    gloss   = data.get("glossary_loaded", False)
    results["Health API"] = (
        "OK" if all([vector, gloss]) else "PARTIAL",
        f"watsonx_connected={watsonx}  vector_store={vector}  glossary={gloss}"
    )
except Exception as e:
    results["Health API"] = ("FAIL", str(e))

# ── 3. Languages endpoint ─────────────────────────────────────────
try:
    r = urllib.request.urlopen("http://localhost:8000/api/translate/languages", timeout=4)
    langs = json.loads(r.read())
    results["Languages API"] = ("OK", f"{len(langs)} languages available")
except Exception as e:
    results["Languages API"] = ("FAIL", str(e))

# ── 4. Documents endpoint ─────────────────────────────────────────
try:
    r = urllib.request.urlopen("http://localhost:8000/api/documents/", timeout=4)
    docs = json.loads(r.read())
    results["Documents API"] = ("OK", f"{len(docs)} documents in current session")
except Exception as e:
    results["Documents API"] = ("FAIL", str(e))

# ── 5. Swagger/OpenAPI docs ───────────────────────────────────────
try:
    r = urllib.request.urlopen("http://localhost:8000/docs", timeout=4)
    results["Swagger UI (/docs)"] = ("OK", f"HTTP {r.status}")
except Exception as e:
    results["Swagger UI (/docs)"] = ("FAIL", str(e))

# ── 6. IBM credentials check (no network needed) ──────────────────
sys.path.insert(0, os.path.dirname(__file__))
try:
    from app.core.config import get_settings
    s = get_settings()
    if "your_ibm_watsonx_api_key_here" in s.watsonx_api_key:
        results["IBM API Key"] = ("NOT SET", "Placeholder still in .env — real key required")
    else:
        results["IBM API Key"] = ("SET", f"Key length={len(s.watsonx_api_key)} chars")

    if "your_watsonx_project_id_here" in s.watsonx_project_id:
        results["IBM Project ID"] = ("NOT SET", "Placeholder still in .env — real ID required")
    else:
        results["IBM Project ID"] = ("SET", f"ID={s.watsonx_project_id[:8]}...")

    results["Granite Model"] = ("INFO", s.granite_model_id)
    results["watsonx URL"]   = ("INFO", s.watsonx_url)
except Exception as e:
    results["IBM Config"] = ("FAIL", str(e))

# ── 7. Key packages importable ────────────────────────────────────
pkg_checks = {
    "fastapi": "fastapi",
    "chromadb": "chromadb",
    "ibm_watsonx_ai": "ibm-watsonx-ai",
    "sentence_transformers": "sentence-transformers",
    "pymupdf": "PyMuPDF",
}
for mod, name in pkg_checks.items():
    try:
        m = __import__(mod)
        ver = getattr(m, "__version__", "installed")
        results[f"Package: {name}"] = ("OK", ver)
    except ImportError:
        results[f"Package: {name}"] = ("MISSING", "pip install " + name)

# ── Print report ──────────────────────────────────────────────────
icons = {"OK": "✓", "SET": "✓", "PARTIAL": "~", "INFO": "·",
         "NOT SET": "⚠", "MISSING": "✗", "FAIL": "✗"}

print()
print("=" * 70)
print("  AICTE Translator Agent — Full Status Report")
print("=" * 70)
for key, (status, detail) in results.items():
    icon = icons.get(status, "?")
    print(f"  {icon}  {key:<30} [{status}]  {detail}")
print("=" * 70)

# Overall verdict
server_ok  = results.get("Frontend (/)", ("",""))[0] == "OK"
creds_ok   = results.get("IBM API Key", ("",""))[0] == "SET"
proj_ok    = results.get("IBM Project ID", ("",""))[0] == "SET"
pkgs_ok    = all(results.get(f"Package: {n}", ("",""))[0] == "OK" for n in pkg_checks.values())

print()
if server_ok and creds_ok and proj_ok and pkgs_ok:
    print("  ✓  ALL SYSTEMS GO — Server is fully operational")
elif server_ok and not creds_ok:
    print("  ⚠  SERVER RUNNING but IBM credentials missing in .env")
    print("     Add real WATSONX_API_KEY and WATSONX_PROJECT_ID to use translation")
elif not server_ok:
    print("  ✗  SERVER NOT RUNNING")
    print("     Start it with:  python run.py")
print()
