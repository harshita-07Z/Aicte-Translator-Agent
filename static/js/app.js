/* ═══════════════════════════════════════════════════════
   AICTE Translator Agent — Frontend JavaScript
═══════════════════════════════════════════════════════ */

const API_BASE = '';

// ── Language data (populated from API) ────────────────────────────────────────
let LANGUAGES = [];

// ── Glossary data (fetched from /api/glossary) ─────────────────────────────────
let GLOSSARY_DATA = [];

// ── Inline glossary (used before API ready) ───────────────────────────────────
const INLINE_GLOSSARY = [
  { term: "algorithm",      domain: "computer_science", hi: "एल्गोरिदम",       mr: "अल्गोरिदम",       ta: "வழிமுறை",           bn: "অ্যালগরিদম",    te: "అల్గోరిదం",     kn: "ಅಲ್ಗಾರಿದಮ್" },
  { term: "data structure", domain: "computer_science", hi: "डेटा संरचना",      mr: "डेटा रचना",        ta: "தரவு அமைப்பு",      bn: "ডেটা স্ট্রাকচার", te: "డేటా నిర్మాణం",  kn: "ಡೇಟಾ ರಚನೆ" },
  { term: "derivative",     domain: "mathematics",      hi: "अवकलज",            mr: "अवकलन",            ta: "வகையீடு",           bn: "অবকল",          te: "అవకలనం",       kn: "ಅವಕಲಜ" },
  { term: "integral",       domain: "mathematics",      hi: "समाकल",            mr: "समाकल",            ta: "தொகைப்படி",         bn: "সমাকল",         te: "సమాకలనం",      kn: "ಸಮಾಕಲ" },
  { term: "photosynthesis", domain: "biology",          hi: "प्रकाश संश्लेषण",  mr: "प्रकाशसंश्लेषण", ta: "ஒளிச்சேர்க்கை",    bn: "সালোকসংশ্লেষণ", te: "కిరణజన్య సంయోగక్రియ", kn: "ದ್ಯುತಿಸಂಶ್ಲೇಷಣೆ" },
  { term: "mitosis",        domain: "biology",          hi: "समसूत्री विभाजन", mr: "समसूत्री विभाजन", ta: "சமவிகித பிரிவு",   bn: "মাইটোসিস",      te: "మైటోసిస్",      kn: "ಮೈಟೋಸಿಸ್" },
  { term: "entropy",        domain: "physics",          hi: "एन्ट्रॉपी",        mr: "एन्ट्रॉपी",        ta: "என்ட்ரோபி",         bn: "এনট্রপি",       te: "ఎంట్రోపీ",      kn: "ಎಂಟ್ರೋಪಿ" },
  { term: "hypothesis",     domain: "science",          hi: "परिकल्पना",        mr: "गृहीतक",           ta: "கருதுகோள்",         bn: "অনুকল্প",       te: "పరికల్పన",      kn: "ಊಹೆ" },
  { term: "oxidation",      domain: "chemistry",        hi: "ऑक्सीकरण",        mr: "ऑक्सिडेशन",       ta: "ஆக்சிஜனேற்றம்",   bn: "জারণ",          te: "ఆక్సీకరణం",    kn: "ಆಕ್ಸಿಡೇಶನ್" },
  { term: "curriculum",     domain: "education",        hi: "पाठ्यक्रम",        mr: "अभ्यासक्रम",       ta: "பாடத்திட்டம்",      bn: "পাঠ্যক্রম",     te: "పాఠ్యక్రమం",    kn: "ಪಠ್ಯಕ್ರಮ" },
  { term: "vector",         domain: "mathematics",      hi: "सदिश",             mr: "सदिश",             ta: "திசையன்",           bn: "ভেক্টর",        te: "వెక్టర్",       kn: "ದಿಕ್ಕಿನ ರಾಶಿ" },
  { term: "matrix",         domain: "mathematics",      hi: "आव्यूह",           mr: "मॅट्रिक्स",        ta: "அணி",               bn: "ম্যাট্রিক্স",   te: "మాతృక",        kn: "ಮ್ಯಾಟ್ರಿಕ್ಸ್" },
  { term: "osmosis",        domain: "biology",          hi: "परासरण",           mr: "ऑस्मोसिस",        ta: "சவ்வூடு பரவல்",    bn: "অভিস্রবণ",      te: "ద్రవాభిసరణం",  kn: "ಆಸ್ಮೋಸಿಸ್" },
  { term: "recursion",      domain: "computer_science", hi: "पुनरावर्तन",       mr: "पुनरावृत्ती",      ta: "மீளாய்வு",          bn: "পুনরাবৃত্তি",   te: "పునరావృత్తి",  kn: "ಮರುಕಳಿಕೆ" },
  { term: "probability",    domain: "mathematics",      hi: "प्रायिकता",         mr: "संभाव्यता",        ta: "நிகழ்தகவு",         bn: "সম্ভাবনা",      te: "సంభావ్యత",      kn: "ಸಂಭಾವ್ಯತೆ" },
  { term: "thermodynamics", domain: "physics",          hi: "ऊष्मागतिकी",       mr: "ऊष्मागतिकी",      ta: "வெப்பவியக்கவியல்", bn: "তাপগতিবিদ্যা",  te: "ఉష్ణగతిశాస్త్రం", kn: "ಉಷ್ಣಚಲನ ವಿಜ್ಞಾನ" },
  { term: "Newton's law",   domain: "physics",          hi: "न्यूटन का नियम",   mr: "न्यूटनचा नियम",   ta: "நியூட்டன் விதி",    bn: "নিউটনের সূত্র", te: "న్యూటన్ నియమం", kn: "ನ್ಯೂಟನ್ ನಿಯಮ" },
  { term: "stoichiometry",  domain: "chemistry",        hi: "रससमीकरणमिति",    mr: "स्टोइकिओमेट्री",  ta: "ஸ்டாய்க்கியோமெட்ரி", bn: "স্টয়কিওমেট্রি", te: "స్టోకియోమెట్రీ", kn: "ರಾಸಾಯನಿಕ ಪ್ರಮಾಣ" },
];

// Example texts
const EXAMPLES = {
  newton: {
    text: `Newton's Laws of Motion

First Law (Law of Inertia): An object at rest stays at rest, and an object in motion stays in motion with the same speed and in the same direction unless acted upon by an unbalanced force.

Second Law: The acceleration of an object is directly proportional to the net force acting on it and inversely proportional to its mass. Mathematically: F = ma, where F is force in Newtons, m is mass in kilograms, and a is acceleration in m/s².

Third Law: For every action, there is an equal and opposite reaction. When object A exerts a force on object B, object B simultaneously exerts a force equal in magnitude and opposite in direction on object A.`,
    domain: "physics",
    lang: "hi"
  },
  algorithm: {
    text: `Binary Search Algorithm

Binary search is an efficient algorithm for finding an element in a sorted array. It works by repeatedly dividing the search interval in half.

Algorithm:
1. Set low = 0, high = n-1
2. While low <= high:
   a. mid = (low + high) / 2
   b. If array[mid] == target: return mid
   c. If array[mid] < target: low = mid + 1
   d. Else: high = mid - 1
3. Return -1 (not found)

Time Complexity: O(log n)
Space Complexity: O(1)

The data structure used is a sorted array. Recursion can also be used to implement this algorithm.`,
    domain: "computer_science",
    lang: "ta"
  },
  photosynthesis: {
    text: `Photosynthesis

Photosynthesis is the process by which plants, algae, and some bacteria convert light energy into chemical energy stored in glucose.

The overall equation for photosynthesis:
6CO₂ + 6H₂O + Light Energy → C₆H₁₂O₆ + 6O₂

Stages:
1. Light-Dependent Reactions (occur in thylakoids): Water is split by photolysis, releasing oxygen as a by-product. ATP and NADPH are produced.

2. Light-Independent Reactions / Calvin Cycle (occur in stroma): CO₂ is fixed using ATP and NADPH to produce glucose through a cycle involving Ribulose bisphosphate (RuBP).

Factors affecting photosynthesis: light intensity, CO₂ concentration, temperature, and water availability.`,
    domain: "biology",
    lang: "bn"
  },
  calculus: {
    text: `Differential Calculus — Derivatives

The derivative of a function f(x) measures how f changes as x changes. It is defined as the limit:
f'(x) = lim(h→0) [f(x+h) - f(x)] / h

Basic Rules of Differentiation:
• Power Rule: d/dx(xⁿ) = nxⁿ⁻¹
• Product Rule: d/dx(uv) = u'v + uv'
• Quotient Rule: d/dx(u/v) = (u'v - uv') / v²
• Chain Rule: d/dx[f(g(x))] = f'(g(x)) · g'(x)

An integral is the antiderivative of a function — the reverse process of differentiation.

Applications: finding maxima and minima, rates of change, tangent lines, and optimization problems using vector calculus.`,
    domain: "mathematics",
    lang: "mr"
  }
};

// ── Init ───────────────────────────────────────────────────────────────────────
document.addEventListener('DOMContentLoaded', async () => {
  await loadLanguages();
  populateLanguageSelects();
  renderGlossaryTable(INLINE_GLOSSARY);
  checkHealth();
  loadDocumentList();

  // Char counter
  const srcText = document.getElementById('source-text');
  srcText.addEventListener('input', () => {
    document.getElementById('char-count').textContent = srcText.value.length;
  });
});

// ── Health Check ───────────────────────────────────────────────────────────────
async function checkHealth() {
  const badge = document.getElementById('health-badge');
  try {
    const res = await fetch(`${API_BASE}/api/health`);
    const data = await res.json();
    if (data.watsonx_connected) {
      badge.textContent = '✓ IBM Granite Connected';
      badge.className = 'badge badge-green';
    } else {
      badge.textContent = '⚠ Granite Offline';
      badge.className = 'badge badge-red';
    }
  } catch {
    badge.textContent = '⚠ Server Offline';
    badge.className = 'badge badge-red';
  }
}

// ── Load Languages ─────────────────────────────────────────────────────────────
async function loadLanguages() {
  try {
    const res = await fetch(`${API_BASE}/api/translate/languages`);
    LANGUAGES = await res.json();
  } catch {
    LANGUAGES = [
      { code: 'hi', name: 'Hindi' }, { code: 'mr', name: 'Marathi' },
      { code: 'ta', name: 'Tamil' }, { code: 'bn', name: 'Bengali' },
      { code: 'te', name: 'Telugu' }, { code: 'kn', name: 'Kannada' },
      { code: 'gu', name: 'Gujarati' }, { code: 'pa', name: 'Punjabi' },
      { code: 'ml', name: 'Malayalam' }, { code: 'or', name: 'Odia' },
      { code: 'ur', name: 'Urdu' }, { code: 'en', name: 'English' },
    ];
  }
}

function populateLanguageSelects() {
  const srcSelect = document.getElementById('source-lang-select');
  const tgtSelect = document.getElementById('target-lang-select');
  const checkboxList = document.getElementById('lang-checkbox-list');

  LANGUAGES.forEach(lang => {
    // Source select
    const opt1 = new Option(`${lang.name} (${lang.code})`, lang.code);
    srcSelect.appendChild(opt1);

    // Target select (text tab)
    const opt2 = new Option(`${lang.name} (${lang.code})`, lang.code);
    tgtSelect.appendChild(opt2);

    // Checkbox for document tab
    const label = document.createElement('label');
    label.className = 'checkbox-item';
    label.innerHTML = `<input type="checkbox" value="${lang.code}" /> ${lang.name}`;
    checkboxList.appendChild(label);
  });
}

// ── Tab switching ──────────────────────────────────────────────────────────────
document.addEventListener('click', e => {
  if (e.target.classList.contains('tab')) {
    document.querySelectorAll('.tab').forEach(t => t.classList.remove('active'));
    document.querySelectorAll('.tab-content').forEach(tc => tc.classList.remove('active'));
    e.target.classList.add('active');
    document.getElementById(`tab-${e.target.dataset.tab}`).classList.add('active');
  }
});

// ── Text Translation ───────────────────────────────────────────────────────────
async function translateText() {
  const text = document.getElementById('source-text').value.trim();
  const targetLang = document.getElementById('target-lang-select').value;
  const sourceLang = document.getElementById('source-lang-select').value || null;
  const domain = document.getElementById('domain-select').value || null;

  if (!text) { showToast('⚠ Please enter some text to translate.'); return; }
  if (!targetLang) { showToast('⚠ Please select a target language.'); return; }

  const btn = document.getElementById('translate-btn');
  btn.disabled = true;
  btn.innerHTML = '<span class="spinner"></span>Translating via IBM Granite…';

  const outputBox = document.getElementById('translation-output');
  outputBox.textContent = 'Sending to IBM watsonx.ai…';
  outputBox.classList.remove('placeholder-text');
  document.getElementById('translation-meta').style.display = 'none';
  document.getElementById('copy-btn').style.display = 'none';

  try {
    const body = { text, target_language: targetLang };
    if (sourceLang) body.source_language = sourceLang;
    if (domain) body.subject_domain = domain;

    const res = await fetch(`${API_BASE}/api/translate/text`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(body)
    });

    if (!res.ok) {
      const err = await res.json();
      throw new Error(err.detail || `HTTP ${res.status}`);
    }

    const data = await res.json();
    outputBox.textContent = data.translated_text;

    // Show meta
    document.getElementById('meta-model').textContent = data.model_used;
    document.getElementById('meta-src-lang').textContent = data.source_language;
    document.getElementById('meta-tgt-lang').textContent = `${data.target_language_name} (${data.target_language})`;
    document.getElementById('meta-domain').textContent = data.subject_domain || '—';

    const glossaryTerms = data.glossary_terms_used || [];
    document.getElementById('meta-glossary').textContent = glossaryTerms.length > 0
      ? glossaryTerms.join(', ')
      : 'None detected';

    document.getElementById('translation-meta').style.display = 'block';
    document.getElementById('copy-btn').style.display = 'inline-flex';

  } catch (err) {
    const msg = err.message || 'Unknown error';
    // Show a styled error box instead of raw text
    outputBox.innerHTML = `
      <div style="background:#2d1a1a;border:1px solid #b91c1c;border-radius:6px;padding:1rem;color:#fca5a5">
        <strong style="color:#f87171">❌ Translation Error</strong><br/><br/>
        ${escHtml(msg)}
        ${msg.includes('.env') || msg.includes('credentials') || msg.includes('API key') ? `
          <br/><br/>
          <strong style="color:#fbbf24">How to fix:</strong><br/>
          1. Open the <code style="background:#1f1a0a;padding:.1rem .3rem;border-radius:3px">.env</code> file in the project root<br/>
          2. Replace <code style="background:#1f1a0a;padding:.1rem .3rem;border-radius:3px">your_ibm_watsonx_api_key_here</code> with your real IBM Cloud API key<br/>
          3. Replace <code style="background:#1f1a0a;padding:.1rem .3rem;border-radius:3px">your_watsonx_project_id_here</code> with your real Project ID<br/>
          4. Save the file and restart the server (<code style="background:#1f1a0a;padding:.1rem .3rem;border-radius:3px">python run.py</code>)<br/><br/>
          Get credentials free at <strong>cloud.ibm.com → watsonx.ai</strong>
        ` : ''}
      </div>`;
    showToast(`❌ ${msg.length > 80 ? msg.slice(0, 80) + '…' : msg}`, 6000);
  } finally {
    btn.disabled = false;
    btn.innerHTML = '🌐 Translate with IBM Granite';
  }
}

function copyTranslation() {
  const text = document.getElementById('translation-output').textContent;
  navigator.clipboard.writeText(text).then(() => showToast('✓ Copied to clipboard!'));
}

// ── Example loaders ────────────────────────────────────────────────────────────
function loadExample(key) {
  const ex = EXAMPLES[key];
  if (!ex) return;
  document.getElementById('source-text').value = ex.text;
  document.getElementById('char-count').textContent = ex.text.length;
  document.getElementById('domain-select').value = ex.domain;
  document.getElementById('target-lang-select').value = ex.lang;
  // Switch to text tab
  document.querySelectorAll('.tab').forEach(t => t.classList.remove('active'));
  document.querySelectorAll('.tab-content').forEach(tc => tc.classList.remove('active'));
  document.querySelector('[data-tab="text"]').classList.add('active');
  document.getElementById('tab-text').classList.add('active');
  showToast(`📖 Example loaded — ${ex.domain}`);
}

// ── File handling ──────────────────────────────────────────────────────────────
let selectedFile = null;

function handleDragOver(e) {
  e.preventDefault();
  document.getElementById('drop-zone').classList.add('dragover');
}
function handleDragLeave() {
  document.getElementById('drop-zone').classList.remove('dragover');
}
function handleDrop(e) {
  e.preventDefault();
  document.getElementById('drop-zone').classList.remove('dragover');
  const file = e.dataTransfer.files[0];
  if (file) setFile(file);
}
function handleFileSelect(e) {
  const file = e.target.files[0];
  if (file) setFile(file);
}
function setFile(file) {
  selectedFile = file;
  document.getElementById('file-name').textContent = file.name;
  document.getElementById('file-size').textContent = formatBytes(file.size);
  document.getElementById('file-details').style.display = 'flex';
  document.getElementById('drop-zone').style.display = 'none';
}
function clearFile() {
  selectedFile = null;
  document.getElementById('file-input').value = '';
  document.getElementById('file-details').style.display = 'none';
  document.getElementById('drop-zone').style.display = 'block';
}

// ── Upload & Translate ─────────────────────────────────────────────────────────
async function uploadAndTranslate() {
  if (!selectedFile) { showToast('⚠ Please select a file first.'); return; }
  const checkedBoxes = [...document.querySelectorAll('#lang-checkbox-list input:checked')];
  if (!checkedBoxes.length) { showToast('⚠ Please select at least one target language.'); return; }

  const domain = document.getElementById('doc-domain-select').value || null;
  const targetLangs = checkedBoxes.map(cb => cb.value);

  const btn = document.getElementById('upload-translate-btn');
  btn.disabled = true;
  btn.innerHTML = '<span class="spinner"></span>Uploading…';

  document.getElementById('doc-results').style.display = 'block';
  document.getElementById('doc-progress-fill').style.width = '0%';
  document.getElementById('doc-progress-text').textContent = '0%';
  document.getElementById('doc-status-text').textContent = 'Uploading document…';
  document.getElementById('doc-lang-results').innerHTML = '';

  try {
    // 1. Upload
    const formData = new FormData();
    formData.append('file', selectedFile);
    if (domain) formData.append('subject_domain', domain);

    const uploadRes = await fetch(`${API_BASE}/api/documents/upload`, {
      method: 'POST',
      body: formData
    });
    if (!uploadRes.ok) {
      const err = await uploadRes.json();
      throw new Error(err.detail || `Upload failed: HTTP ${uploadRes.status}`);
    }
    const docMeta = await uploadRes.json();

    document.getElementById('doc-status-text').textContent =
      `Document indexed (${docMeta.page_count} pages, ${docMeta.indexed ? '✓ RAG indexed' : 'indexing pending'}). Starting translation…`;
    btn.innerHTML = '<span class="spinner"></span>Translating…';

    // 2. Request translation
    const transRes = await fetch(`${API_BASE}/api/translate/document`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        document_id: docMeta.document_id,
        target_languages: targetLangs,
        subject_domain: domain
      })
    });
    if (!transRes.ok) {
      const err = await transRes.json();
      throw new Error(err.detail || `Translation failed: HTTP ${transRes.status}`);
    }
    const jobData = await transRes.json();

    // 3. Poll for completion
    await pollJobStatus(jobData.job_id, targetLangs);
    loadDocumentList();

  } catch (err) {
    document.getElementById('doc-status-text').textContent = `Error: ${err.message}`;
    showToast(`❌ ${err.message}`);
  } finally {
    btn.disabled = false;
    btn.innerHTML = '🚀 Upload & Translate';
  }
}

async function pollJobStatus(jobId, targetLangs) {
  const maxPolls = 120;
  for (let i = 0; i < maxPolls; i++) {
    await sleep(2000);
    const res = await fetch(`${API_BASE}/api/translate/status/${jobId}`);
    const status = await res.json();

    const pct = status.progress || 0;
    document.getElementById('doc-progress-fill').style.width = `${pct}%`;
    document.getElementById('doc-progress-text').textContent = `${pct}%`;
    document.getElementById('doc-status-text').textContent =
      `Status: ${status.status} — ${pct}% complete`;

    if (status.status === 'completed') {
      document.getElementById('doc-status-text').textContent = '✓ Translation complete!';
      renderDocResults(status.results, targetLangs);
      return;
    }
    if (status.status === 'failed') {
      document.getElementById('doc-status-text').textContent = `❌ Failed: ${status.error}`;
      return;
    }
  }
  document.getElementById('doc-status-text').textContent = 'Timeout — please check back later.';
}

function renderDocResults(results, targetLangs) {
  const container = document.getElementById('doc-lang-results');
  const langNames = Object.fromEntries(LANGUAGES.map(l => [l.code, l.name]));
  container.innerHTML = '';
  targetLangs.forEach(lang => {
    const text = results[lang] || '(no result)';
    const block = document.createElement('div');
    block.className = 'lang-result-block';
    block.innerHTML = `<h4>${langNames[lang] || lang}</h4>
      <pre>${escHtml(text)}</pre>
      <button class="btn btn-ghost" style="margin-top:.5rem;font-size:.75rem"
        onclick="copyToClipboard(this.previousElementSibling.textContent)">📋 Copy</button>`;
    container.appendChild(block);
  });
}

// ── Document List ──────────────────────────────────────────────────────────────
async function loadDocumentList() {
  try {
    const res = await fetch(`${API_BASE}/api/documents/`);
    const docs = await res.json();
    const container = document.getElementById('doc-list');
    if (!docs.length) {
      container.innerHTML = '<p class="placeholder-text">No documents uploaded yet.</p>';
      return;
    }
    container.innerHTML = docs.map(doc => `
      <div class="doc-item">
        <div>
          <div class="doc-item-name">📄 ${escHtml(doc.filename)}</div>
          <div class="doc-item-meta">
            ${doc.file_type.toUpperCase()} · ${formatBytes(doc.size_bytes)} ·
            ${doc.page_count} page(s) · ${doc.subject_domain || 'general'}
          </div>
        </div>
        <div class="doc-item-badges">
          ${doc.indexed ? '<span class="badge badge-green">RAG Indexed</span>' : ''}
          <button class="btn btn-ghost" style="font-size:.75rem;padding:.3rem .6rem"
            onclick="deleteDocument('${doc.document_id}')">🗑 Delete</button>
        </div>
      </div>
    `).join('');
  } catch { /* ignore */ }
}

async function deleteDocument(docId) {
  if (!confirm('Remove this document?')) return;
  await fetch(`${API_BASE}/api/documents/${docId}`, { method: 'DELETE' });
  loadDocumentList();
  showToast('✓ Document removed.');
}

// ── Glossary Table ─────────────────────────────────────────────────────────────
function renderGlossaryTable(data) {
  const tbody = document.getElementById('glossary-tbody');
  tbody.innerHTML = data.map(entry => `
    <tr>
      <td><strong>${escHtml(entry.term)}</strong></td>
      <td><span class="domain-tag">${escHtml(entry.domain || '—')}</span></td>
      <td>${escHtml(entry.hi || '—')}</td>
      <td>${escHtml(entry.mr || '—')}</td>
      <td>${escHtml(entry.ta || '—')}</td>
      <td>${escHtml(entry.bn || '—')}</td>
      <td>${escHtml(entry.te || '—')}</td>
      <td>${escHtml(entry.kn || '—')}</td>
    </tr>
  `).join('');
}

function filterGlossary() {
  const q = document.getElementById('glossary-search').value.toLowerCase();
  const dom = document.getElementById('glossary-domain-filter').value;
  const filtered = INLINE_GLOSSARY.filter(entry => {
    const matchQ = !q || entry.term.toLowerCase().includes(q);
    const matchDom = !dom || entry.domain === dom;
    return matchQ && matchDom;
  });
  renderGlossaryTable(filtered);
}

// ── Utilities ──────────────────────────────────────────────────────────────────
function showToast(msg, duration = 3000) {
  const toast = document.getElementById('toast');
  toast.textContent = msg;
  toast.style.display = 'block';
  setTimeout(() => { toast.style.display = 'none'; }, duration);
}

function copyToClipboard(text) {
  navigator.clipboard.writeText(text).then(() => showToast('✓ Copied!'));
}

function formatBytes(bytes) {
  if (bytes < 1024) return `${bytes} B`;
  if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`;
  return `${(bytes / (1024 * 1024)).toFixed(1)} MB`;
}

function escHtml(str) {
  return String(str)
    .replace(/&/g, '&amp;').replace(/</g, '&lt;')
    .replace(/>/g, '&gt;').replace(/"/g, '&quot;');
}

function sleep(ms) { return new Promise(r => setTimeout(r, ms)); }
