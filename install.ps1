# ═══════════════════════════════════════════════════════════════════
#  AICTE Translator Agent — Dependency Installer
#  Run this from the project root:
#    PowerShell:  .\install.ps1
#    OR manually follow the steps below
# ═══════════════════════════════════════════════════════════════════

# Locate the Python launcher
$pyLauncher = "C:\Users\DELL\AppData\Local\Programs\Python\Launcher\py.exe"
if (-not (Test-Path $pyLauncher)) {
    # Fallback: try PATH
    $pyLauncher = (Get-Command python -ErrorAction SilentlyContinue)?.Source
    if (-not $pyLauncher) {
        Write-Error "Python not found. Please install Python 3.11+ from https://python.org"
        exit 1
    }
}

$pyVersion = & $pyLauncher --version 2>&1
Write-Host "Using: $pyLauncher  ($pyVersion)" -ForegroundColor Cyan

# ── Step 1: Upgrade pip ────────────────────────────────────────────
Write-Host "`n[1/6] Upgrading pip..." -ForegroundColor Yellow
& $pyLauncher -m pip install --upgrade pip --quiet

# ── Step 2: Core web framework (always works on 3.14) ─────────────
Write-Host "[2/6] Installing core web framework..." -ForegroundColor Yellow
& $pyLauncher -m pip install fastapi "uvicorn[standard]" python-multipart `
    pydantic pydantic-settings python-dotenv httpx aiofiles jinja2 tqdm

# ── Step 3: Document parsing ──────────────────────────────────────
Write-Host "[3/6] Installing document parsers..." -ForegroundColor Yellow
& $pyLauncher -m pip install PyMuPDF pypdf python-docx python-pptx pillow langdetect nltk

# ── Step 4: Vector store & embeddings ─────────────────────────────
Write-Host "[4/6] Installing ChromaDB and sentence-transformers..." -ForegroundColor Yellow
& $pyLauncher -m pip install chromadb sentence-transformers

# ── Step 5: IBM watsonx.ai SDK ─────────────────────────────────────
Write-Host "[5/6] Installing IBM watsonx.ai SDK..." -ForegroundColor Yellow
# Try regular install first; fall back to --no-build-isolation for 3.13/3.14
$ibmInstall = & $pyLauncher -m pip install ibm-watsonx-ai ibm-watson ibm-cloud-sdk-core 2>&1
if ($LASTEXITCODE -ne 0) {
    Write-Host "  Retrying with --no-build-isolation (needed for Python 3.13/3.14)..." -ForegroundColor DarkYellow
    & $pyLauncher -m pip install ibm-watsonx-ai ibm-watson ibm-cloud-sdk-core --no-build-isolation
}

# ── Step 6: Test server (pytest) ──────────────────────────────────
Write-Host "[6/6] Installing pytest..." -ForegroundColor Yellow
& $pyLauncher -m pip install pytest

Write-Host "`nAll done! Start the server with:" -ForegroundColor Green
Write-Host "  $pyLauncher run.py" -ForegroundColor White
Write-Host "  Then open http://localhost:8000`n" -ForegroundColor White
