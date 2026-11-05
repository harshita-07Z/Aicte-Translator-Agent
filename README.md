# AICTE Multi-language Course Content Translator Agent

**Problem Statement #17 — AICTE Hackathon**

> A RAG-powered academic content translator that converts course materials into 11 Indian regional languages while preserving technical accuracy and educational context — powered by **IBM Granite** (watsonx.ai).

---

## Architecture

```
┌──────────────────────────────────────────────────────────────────┐
│                     Browser / API Client                         │
└─────────────────────────────┬────────────────────────────────────┘
                              │ HTTP
┌─────────────────────────────▼────────────────────────────────────┐
│              FastAPI Backend  (run.py → app/main.py)             │
│  ┌──────────────┐  ┌────────────────┐  ┌───────────────────────┐ │
│  │  /api/health │  │/api/translate/ │  │  /api/documents/      │ │
│  └──────────────┘  └───────┬────────┘  └──────────┬────────────┘ │
└──────────────────────────────────────────────────────────────────┘
                              │
         ┌────────────────────▼───────────────────────┐
         │         Translation Agent (RAG)             │
         │  1. Detect source language (langdetect)     │
         │  2. Retrieve context — ChromaDB vector DB   │
         │  3. Inject academic glossary terms          │
         │  4. Build prompt for IBM Granite            │
         │  5. Call watsonx.ai ModelInference API      │
         │  6. Return structured TranslationResult     │
         └────────────────────────────────────────────┘
                    │                   │
         ┌──────────▼──────┐   ┌────────▼─────────────────┐
         │ ChromaDB        │   │ IBM watsonx.ai            │
         │ (Persistent     │   │ Granite-13B-Instruct-v2   │
         │  Vector Store)  │   │ or Granite-3-8B-Instruct  │
         │ Multilingual    │   │ (IBM Cloud Lite)           │
         │ Sentence-BERT   │   └──────────────────────────┘
         └─────────────────┘
```

---

## Supported Languages

| Code | Language   | Script    |
|------|-----------|-----------|
| `hi` | Hindi      | Devanagari |
| `mr` | Marathi    | Devanagari |
| `ta` | Tamil      | Tamil      |
| `bn` | Bengali    | Bengali    |
| `te` | Telugu     | Telugu     |
| `kn` | Kannada    | Kannada    |
| `gu` | Gujarati   | Gujarati   |
| `pa` | Punjabi    | Gurmukhi   |
| `ml` | Malayalam  | Malayalam  |
| `or` | Odia       | Odia       |
| `ur` | Urdu       | Nastaliq   |
| `en` | English    | Latin      |

---

## Project Structure

```
Aicte-Translator-Agent/
├── .env                          # ← IBM Cloud credentials (fill this in)
├── requirements.txt
├── run.py                        # Uvicorn entry point
│
├── app/
│   ├── main.py                   # FastAPI app factory
│   ├── core/
│   │   ├── config.py             # Pydantic settings (loads .env)
│   │   └── logging_config.py     # Structured logging
│   ├── api/
│   │   ├── health.py             # GET /api/health
│   │   ├── translate.py          # POST /api/translate/text & /document
│   │   └── documents.py          # POST /api/documents/upload
│   ├── models/
│   │   └── schemas.py            # Pydantic request/response models
│   └── services/
│       ├── granite_llm.py        # IBM Granite / watsonx.ai LLM client
│       ├── translation_agent.py  # RAG orchestration agent
│       ├── vector_store.py       # ChromaDB vector store
│       ├── document_processor.py # PDF/DOCX/PPTX text extraction
│       └── glossary_service.py   # Academic glossary lookup
│
├── data/
│   ├── glossaries/
│   │   └── academic_glossary.json  # 20 bilingual academic terms
│   ├── uploads/                    # Uploaded document storage
│   └── chroma_db/                  # ChromaDB persistent vector index
│
├── static/
│   ├── css/style.css             # IBM Design-inspired UI
│   └── js/app.js                 # Frontend JavaScript
│
├── templates/
│   └── index.html                # Full-stack single-page UI
│
├── tests/
│   └── test_app.py               # pytest unit + integration tests
│
└── logs/
    └── app.log
```

---

## Quick Start

### 1. Prerequisites

- Python 3.10+
- An **IBM Cloud Lite account** (free)
- A **watsonx.ai project** with access to IBM Granite models

### 2. Get IBM Cloud credentials

1. Sign up at [cloud.ibm.com](https://cloud.ibm.com) (free Lite tier)
2. Create a **watsonx.ai** service instance
3. Get your **API Key** from [IBM Cloud IAM](https://cloud.ibm.com/iam/apikeys)
4. Get your **Project ID** from the watsonx.ai project settings

### 3. Configure `.env`

Open `.env` and fill in your credentials:

```env
WATSONX_API_KEY=your_actual_api_key_here
WATSONX_PROJECT_ID=your_actual_project_id_here
WATSONX_URL=https://us-south.ml.cloud.ibm.com
GRANITE_MODEL_ID=ibm/granite-13b-instruct-v2
```

### 4. Install dependencies

```bash
pip install -r requirements.txt
```

> **Note:** On first run, `sentence-transformers` will download the multilingual
> embedding model (~120 MB). This only happens once.

### 5. Run the server

```bash
python run.py
```

Or with uvicorn directly:

```bash
uvicorn run:app --host 0.0.0.0 --port 8000 --reload
```

### 6. Open the UI

Navigate to **http://localhost:8000**

---

## API Reference

### Health Check
```http
GET /api/health
```

### Translate Text
```http
POST /api/translate/text
Content-Type: application/json

{
  "text": "The derivative of a function measures rate of change.",
  "target_language": "hi",
  "source_language": "en",
  "subject_domain": "mathematics"
}
```

### Upload Document
```http
POST /api/documents/upload
Content-Type: multipart/form-data

file: <PDF/DOCX/PPTX/TXT/MD>
subject_domain: mathematics
```

### Translate Document
```http
POST /api/translate/document
Content-Type: application/json

{
  "document_id": "<id from upload>",
  "target_languages": ["hi", "ta", "bn"],
  "subject_domain": "physics"
}
```

### Check Job Status
```http
GET /api/translate/status/{job_id}
```

Full interactive docs at **http://localhost:8000/docs**

---

## How RAG Works

1. **Ingestion** — Uploaded PDFs/DOCXs are split into ~512-token chunks
2. **Embedding** — Each chunk is embedded using `paraphrase-multilingual-MiniLM-L12-v2`
3. **Indexing** — Chunks are stored in a persistent ChromaDB vector index
4. **Retrieval** — At translation time, semantically similar chunks are retrieved
5. **Augmentation** — Retrieved context + academic glossary terms are injected into the Granite prompt
6. **Generation** — IBM Granite produces a contextually accurate translation

---

## Academic Glossary

The system ships with a built-in glossary covering 20 terms across:
- **Computer Science** — algorithm, data structure, recursion
- **Mathematics** — derivative, integral, vector, matrix, probability
- **Physics** — entropy, Newton's law, electric field, thermodynamics
- **Biology** — photosynthesis, mitosis, osmosis
- **Chemistry** — oxidation, stoichiometry
- **Education** — curriculum, pedagogy
- **Science** — hypothesis

All terms have verified translations in all 11 regional languages.

---

## Running Tests

```bash
pytest tests/ -v
```

---

## IBM Cloud Services Used

| Service | Tier | Purpose |
|---------|------|---------|
| **IBM watsonx.ai** | Lite | IBM Granite LLM inference |
| **IBM Granite-13B-Instruct-v2** | Lite-eligible | Translation model |
| **IBM Granite-3-8B-Instruct** | Lite-eligible | Alternative model |
| **Watson Language Translator** | Lite (optional) | Source language detection |

---

## Technology Stack

| Layer | Technology |
|-------|-----------|
| LLM | IBM Granite (watsonx.ai) |
| RAG Retrieval | ChromaDB + sentence-transformers |
| Embeddings | `paraphrase-multilingual-MiniLM-L12-v2` |
| Backend | FastAPI + Uvicorn |
| Document Parsing | PyMuPDF, python-docx, python-pptx |
| Frontend | Vanilla HTML/CSS/JS (IBM Design) |
| Config | pydantic-settings |
| Tests | pytest |

---

*AICTE Hackathon — Problem Statement #17 · Powered by IBM Granite & watsonx.ai*
