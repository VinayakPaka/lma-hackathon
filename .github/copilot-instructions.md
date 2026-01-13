# GreenGuard ESG Platform - AI Coding Agent Instructions

## Project Overview

**GreenGuard** is a **bank-ready ESG assessment platform** for Sustainability-Linked Loans (SLLs) and Green Loans. It provides deterministic, audit-compliant KPI benchmarking and credibility assessment—NOT AI-driven decision-making.

**Core Principle**: LLMs extract and summarize; deterministic algorithms score and approve. This separation is **critical for regulatory compliance**.

---

## Architecture at a Glance

```
┌─────────────────────────────────────────────────────────────┐
│  FRONTEND (greenguard-desktop/)                             │
│  React + TypeScript + Tauri (desktop wrapper)               │
│  → KPI evaluation, compliance checks, report viewing        │
└──────────────────┬──────────────────────────────────────────┘
                   │ API Calls (HTTP)
┌──────────────────▼──────────────────────────────────────────┐
│  BACKEND (backend/app/) - FastAPI                           │
│  ┌─────────────────────────────────────────────────────────┤
│  │ 1. INPUT: Document upload & chunking (embedding_service │
│  │ 2. EXTRACTION: KPI mining via LLM + RAG                 │
│  │ 3. PEER BENCH: SBTi data matching (sbti_data_service)   │
│  │ 4. CREDIBILITY: Signal-based scoring (credibility_svc)  │
│  │ 5. COMPLIANCE: Rule-based checks (compliance_service)   │
│  │ 6. REPORTING: PDF/JSON generation (banker_report_svc)   │
│  └─────────────────────────────────────────────────────────┤
│  Database: PostgreSQL (production) / SQLite (local dev)     │
│  Vector Store: Supabase pgvector (for RAG embeddings)       │
│  External APIs: Voyage AI (embeddings), Perplexity (LLM)    │
└─────────────────────────────────────────────────────────────┘
```

---

## Key Components & Responsibilities

### 1. **Document Ingestion** (`embedding_service.py`)
- **Chunking strategy**: Section-aware splitting for ESG reports (governance, strategy, metrics)
- **Vector storage**: Voyage AI embeddings → Supabase pgvector
- **Models**: `DocumentChunk` (text + embedding + citations)
- **Key pattern**: Always preserve chunk indices + source pages for audit trails

### 2. **KPI Extraction** (`kpi_extraction_service.py`)
- **LLM-driven extraction** from chunked documents via RAG
- **CSRD/ESRS-aware prompts**: Recognizes scope definitions, fiscal year formats, SBTi terminology
- **Output format**: Structured JSON with citations (which chunk provided this data)
- **Critical constraint**: Extract FACTS only, never synthesize targets
- **Scope handling**: Automatically detects "Scope 1+2", "Scope 1+2+3" patterns

### 3. **SBTi Peer Benchmarking** (`sbti_data_service.py`)
- **Data source**: Excel files in `backend/resources/SBT'is Data/`
- **Peer selection**: Deterministic SQL-style filtering (sector, scope, region)
- **Percentile computation**: Pandas-based, NO LLM involvement
- **Confidence labeling**: "High confidence" (100+ peers), "Medium" (20-100), "Low" (<20)
- **Fallback benchmarks**: Hardcoded industry defaults when SBTi data insufficient
- **IMPORTANT**: This service NEVER uses AI for scoring—only data aggregation

### 4. **Credibility Assessment** (`credibility_service.py`)
- **Signal-based scoring** (not predictive modeling):
  - Past targets met (10 pts)
  - Third-party verified (15 pts)
  - SBTi validation (30 pts, strongest)
  - Board oversight, transition plans, etc.
- **Classification thresholds**:
  - HIGH: 70+ points OR (past_targets + verified + board)
  - MEDIUM-HIGH: 50-69 points
  - MEDIUM: 30-49 points OR 2-3 signals
  - LOW: <30 points
- **Output**: Achievability score + signal details with evidence

### 5. **Compliance Checking** (`compliance_service.py`)
- **Frameworks supported**: GLP, SLLP, SFDR, EBA, EU Taxonomy
- **Approach**: Rule-based checklist (NOT AI-driven)
- **Output**: Pass/fail per requirement + remediation notes
- **Critical**: Used for loan structuring decisions—must be 100% deterministic

### 6. **Reporting** (`banker_report_service.py`)
- **Output formats**: JSON (machine-readable) + PDF/HTML (human-readable)
- **Recipient**: Credit officers / risk committees
- **Key sections**: Target ambition, credibility assessment, compliance status, risk flags
- **Confidence transparency**: Always include peer count + data quality notes

---

## Critical Developer Patterns

### Database: Async SQLAlchemy + Supabase Quirks

```python
# Good: Use async sessions correctly
async with AsyncSessionLocal() as session:
    result = await session.execute(select(Model))
    await session.commit()  # Explicit commit required

# Important: PgBouncer compatibility (production)
# - prepared_statement_cache_size: 0 (MANDATORY for transaction pooling)
# - statement_cache_size: 0 (avoid "Unexpected message type..." errors)
# See: backend/app/database.py lines 31-48
```

### RAG Pattern: Embedding → Retrieval → LLM

```python
# 1. Chunk document with context preservation
chunks = embedding_service.chunk_text(
    text, 
    chunk_size=1024,  # Configurable; see config.py
    section_aware=True  # Group related sections together
)

# 2. Generate embeddings (Voyage AI)
embeddings = embedding_service.embed_chunks(chunks)  # Returns vectors

# 3. Store in Supabase + SQLite metadata
await embedding_service.store_embeddings(document_id, chunks, embeddings)

# 4. Retrieve relevant chunks for LLM context
context = await embedding_service.retrieve_chunks(document_id, query, top_k=5)

# 5. Pass to LLM with strict extraction prompt
kpis = await kpi_extraction_service.extract_kpis(context, document_type)
```

### SBTi Peer Matching: Deterministic Filtering

```python
# Pattern: Filter → Aggregate → Classify
peers = sbti_data_service.get_peers(
    sector="Manufacturing",
    scope="Scope 1+2",
    region="EU",  # Optional
    target_year=2030
)

# Returns: {
#   "peers": [{"company": "...", "reduction_pct": 45}, ...],
#   "stats": {"median": 42.0, "p75": 50.0, "count": 87},
#   "confidence": "High"  # Based on peer count
# }
```

### Credibility Signals: Evidence-Based Classification

```python
# Pattern: Detect signals → Score → Classify
signals = credibility_service.extract_signals(
    document_id,
    extracted_kpis,
    company_name
)

# Returns:
# [
#   CredibilitySignal(name="sbti_validation", detected=True, weight="high"),
#   CredibilitySignal(name="transition_plan", detected=False, evidence="Not mentioned")
# ]

score = credibility_service.compute_score(signals)
classification = credibility_service.classify(score)  # HIGH/MEDIUM-HIGH/MEDIUM/LOW
```

---

## Router Endpoints: Key Workflows

### **POST /kpi-benchmark/evaluate** (Main Endpoint)

```python
# Request: Company info + documents + KPI metrics
{
    "company_name": "Acme Corp",
    "industry_sector": "Manufacturing",
    "metric": "GHG Emissions Reduction",
    "target_value": 42,  # Percentage
    "baseline_year": 2020,
    "timeline_end_year": 2030,
    "documents": [
        {"document_id": 123, "document_type": "csrd_report", "is_primary": true}
    ]
}

# Response: Complete assessment
{
    "ambition": {
        "classification": "MEDIUM-HIGH",
        "percentile": 65,
        "peer_count": 87,
        "confidence": "High"
    },
    "credibility": {
        "achievability_score": 72,
        "classification": "HIGH",
        "signals": [...]
    },
    "compliance": {
        "framework": "sllp",
        "compliant": true,
        "issues": []
    }
}
```

### **POST /kpi-benchmark/peer-benchmark** (Standalone Benchmarking)

Used when company KPIs already known; just need peer context.

### **POST /kpi-benchmark/report** (PDF/HTML Generation)

Triggers `banker_report_service` to generate audit-ready documentation.

---

## Configuration & Environment Variables

See `backend/app/config.py`:

```bash
# Required
DATABASE_URL=postgresql://user:pass@host/db  # Supabase PostgreSQL
JWT_SECRET=<your-secret>
VOYAGE_API_KEY=<Voyage AI key>  # For embeddings
PERPLEXITY_API_KEY=<Perplexity key>  # For KPI extraction LLM

# Optional (defaults provided)
CHUNK_SIZE=1024  # Characters per embedding chunk
CHUNK_OVERLAP=100  # Overlap for context continuity
UPLOAD_DIR=uploads  # Where PDFs are stored locally
```

---

## Testing & Development Workflows

### Running the Backend

```bash
# Virtual environment setup
cd backend
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
pip install -r requirements.txt

# Start dev server
uvicorn app.main:app --reload --port 8000

# Docs available at http://localhost:8000/docs
```

### Running the Frontend

```bash
cd greenguard-desktop
npm install
npm run dev  # Vite dev server at http://localhost:5173

# Build desktop app (Tauri)
npm run tauri dev  # Open Tauri window
npm run tauri build  # Create .msi/.exe
```

### Debugging Workflows

1. **KPI Extraction Issues**: Check `test_embeddings.py` and `test_peer_matching.py` in backend root
2. **Database Issues**: Run `backend/app/middleware/config_check.py` to diagnose connectivity
3. **Vector Store**: Query `document_chunks` table in Supabase to verify embeddings stored

---

## Code Organization & Conventions

### Service Singletons

```python
# Services are instantiated ONCE and reused (avoid redundant API calls)
from app.services.embedding_service import embedding_service  # Singleton
from app.services.sbti_data_service import sbti_data_service  # Singleton

# In routers/main module - these are already initialized
```

### Error Handling Pattern

```python
# All services wrap errors with context
try:
    result = await service.method()
except ValueError as e:
    logger.error(f"Validation failed for {document_id}: {str(e)}", exc_info=True)
    raise HTTPException(status_code=400, detail=str(e))
except Exception as e:
    logger.exception(f"Unexpected error in {context}: {str(e)}")
    raise HTTPException(status_code=500, detail="Internal error")
```

### Logging Conventions

```python
logger = logging.getLogger(__name__)  # Per-module logger

# Log structured info for audit trails
logger.info(f"Extracted {len(kpis)} KPIs from document {doc_id}")
logger.info(f"Peer matching: sector={sector}, count={len(peers)}, confidence={conf}")
```

---

## Known Quirks & Gotchas

1. **Supabase PgBouncer Mode**: Prepared statements break transaction pooling. Always set `statement_cache_size=0` in PostgreSQL connections.

2. **Voyage AI Rate Limits**: Embedding API has rate limits. Consider caching for repeated documents. See `embedding_service.embedding_cache()`.

3. **SBTi Data Staleness**: Excel files in `backend/resources/SBT'is Data/` are static. For live data, enhance `sbti_data_service.py` to fetch from SBTi API (not yet implemented).

4. **ESRS/CSRD Terminology**: Different companies format scope, baselines, and years differently. The KPI extraction prompt handles common variants—review `KPI_EXTRACTION_PROMPT` in `kpi_extraction_service.py` when adding new sectors.

5. **Percentile Confidence**: Scoring has lower confidence when peer pool <20. Always communicate this in reports.

---

## Where to Make Changes

| Need | File(s) | Pattern |
|------|---------|---------|
| Add new KPI metric | `kpi_extraction_service.py` | Update `KPI_EXTRACTION_PROMPT` with metric definition |
| Add compliance rule | `compliance_service.py` | Add to `CHECKLISTS` dict + check method |
| Add credibility signal | `credibility_service.py` | Add to `SIGNAL_POINTS` + detection logic |
| Change peer filtering logic | `sbti_data_service.py` | Modify `get_peers()` filter conditions |
| Modify scoring thresholds | `credibility_service.py` | Adjust `SIGNAL_POINTS` or classification thresholds |
| Adjust chunking strategy | `embedding_service.py` | Modify `chunk_text()` method |
| Add new loan framework | `compliance_service.py` → `CHECKLISTS` | Add new dict entry with requirements |

---

## References

- **Implementation Plan**: `implementation_plan.md` (read for full architecture & stage-by-stage details)
- **Database Setup**: `backend/supabase_setup*.sql` (schemas for documents, embeddings, SBTi data)
- **Requirements**: `backend/requirements.txt` (all dependencies)

---

## When to Escalate to Humans

- **Regulatory changes**: Any EU directive (CSRD, Taxonomy, SFDR) additions require stakeholder review
- **Scoring threshold changes**: Affects loan approval decisions—needs credit committee alignment
- **SBTi data updates**: Consider data freshness implications
- **AI model selection**: Changing LLM provider (Perplexity → Claude, etc.) requires re-evaluation of outputs
