# LogGuard AI

Production-oriented **SIEM log threat classifier and SOC co-pilot**: paste or upload logs (CEF, Syslog, JSON, plain text), get severity, **MITRE ATT&CK** mapping, **IOC** extraction, executive summary, sector playbook, **Sigma + YARA detection rules** (LLM-assisted with template fallback), an interactive **attack-chain graph** (tactics → techniques → IOCs via **React Flow**), **Plotly** charts, optional **PDF** report, and a **streaming follow-up chat** — powered by a **FastAPI** backend and **React (TypeScript)** UI. Remote inference uses **`huggingface_hub.InferenceClient`** (routes to current **Inference Providers**; no local GPU). The legacy `api-inference.huggingface.co` host returns **410 Gone** — this project uses the supported client. **Logs are not stored** on the server.

Reference dataset for style/diversity: [darkknight25/Advanced_SIEM_Dataset](https://huggingface.co/datasets/darkknight25/Advanced_SIEM_Dataset) (demo logs in this repo are hand-curated samples, not a full dump).

## Architecture

| Layer | Stack |
|--------|--------|
| API | FastAPI, httpx, scikit-learn (TF–IDF + clustering), ReportLab (PDF) |
| ML remote | Zero-shot classification, token NER, text generation (configurable HF models) |
| Correlation | Optional **HF Inference** embeddings (`HF_USE_REMOTE_EMBEDDINGS=true`); else `sentence-transformers` if installed; else TF–IDF |
| UI | Vite, React 19, TypeScript, Tailwind v4, Plotly.js, **@xyflow/react**, **react-syntax-highlighter**, lucide-react |

**Explainability:** True SHAP over third-party APIs is not exposed. The UI heatmap combines **NER spans**, **regex IOC** regions, and a **cyber keyword** lexicon as a practical attribution proxy.

### Implemented NLP algorithms (batch analysis)

| Algorithm | Role |
|-----------|------|
| **TF-IDF + cosine similarity** | `TfidfVectorizer` on raw logs, `cosine_similarity` between rows; single-link components with edge weight **> 0.75** become **incidents**. Per incident: mean/min pairwise cosine and **top 10 TF-IDF terms** (aggregated vector) for explainability. |
| **Isolation Forest** | `sentence-transformers/all-MiniLM-L6-v2` embeddings, `sklearn.ensemble.IsolationForest` (`n_jobs=-1`). Scores are **MinMax-normalized** to **0–1** within the batch (higher = more anomalous vs peers). UI flags **> 0.6** as a secondary **NLP outlier** alongside transformer severity. |
| **Existing** | Agglomerative clustering on TF-IDF / optional HF or local embeddings (`clusters`); zero-shot / NER / generation unchanged. |

Batch JSON adds `incidents`, `tfidf_keywords`, `anomaly_scores`, and each `results[]` item may include `anomaly_score` and `isolation_anomaly_flag`.

### Detection rules (Sigma / YARA)

Each `AnalyzeResponse` includes `detection_rules`: YAML **Sigma** (`author: LogGuard AI`, MITRE tags, `falsepositives`, level from severity) and a **YARA** snippet. The backend uses the configured generative model when available; otherwise deterministic templates from IOCs/log text are used. The UI can **copy**, **customize + download** (`.yml` / `.yar`), and **test** the Sigma against the current log or batch via `POST /test-sigma` (heuristic token match — not a full Sigma engine).

### Attack chain graph

`attack_chain` contains `nodes` (tactic / technique / IOC / sector-risk) and `edges` with optional `strength`. The dashboard **Attack chain** tab renders an interactive **React Flow** diagram (pan/zoom, minimap, node details, **Export PNG**). For batch analysis with multiple results, a **timeline slider** switches between per-log graphs.

## Repository layout

On disk you might name the parent folder `logGuard`; on **GitHub** the repo root is usually the project root (no extra `logGuard/` folder inside the clone):

```
./
├── backend/           # FastAPI app (app.main:app)
├── frontend/          # Vite + React
├── docker-compose.yml
└── README.md
```

**Render:** leave **Root Directory empty** (repo root). Do **not** set it to `logGuard` unless your remote repo actually contains that nested folder.

## Quick start (local)

### Prerequisites

- **Python 3.11–3.13** (recommended). Python 3.14 may lack wheels for some dependencies.
- **Node.js 20+** for the frontend.
- Optional: **Hugging Face token** for higher rate limits and private models (`HF_TOKEN`).

### Backend

```bash
cd backend
python3.12 -m venv .venv
source .venv/bin/activate   # Windows: .venv\Scripts\activate
pip install -r requirements.txt
cp .env.example .env        # add HF_TOKEN if you have one
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

Open interactive docs: [http://127.0.0.1:8000/docs](http://127.0.0.1:8000/docs)

### Frontend

```bash
cd frontend
npm install
npm run dev
```

The dev server proxies `/api` → `http://127.0.0.1:8000` (see `vite.config.ts`). With no `VITE_API_URL`, the UI uses `/api`. For a production build against a remote API, set **`VITE_API_URL`** (see `frontend/.env.example`).

### Optional: extra ML pinning

`requirements.txt` already installs **sentence-transformers** (Isolation Forest + MiniLM embeddings in batch mode, and optional local correlation vectors). Use `requirements-ml.txt` only if you want an explicit `-r requirements.txt` bundle for pinned ML stacks.

Batch **correlation** (`clusters`) still prefers local `all-MiniLM-L6-v2` when importable; otherwise TF–IDF or HF remote embeddings per `HF_USE_REMOTE_EMBEDDINGS`.

## Docker

```bash
export HF_TOKEN=hf_xxx   # optional
docker compose up --build
```

- UI: [http://localhost:8080](http://localhost:8080) (nginx proxies `/api` to the API container).
- API (direct): [http://localhost:8000](http://localhost:8000)

## API summary

| Method | Path | Description |
|--------|------|-------------|
| `GET` | `/health` | Liveness + whether `HF_TOKEN` is set |
| `GET` | `/demo-logs` | 12 curated demo log objects (incl. NLP batch lab for TF-IDF + Isolation Forest) |
| `POST` | `/analyze` | JSON `{ "log_text", "industry" }` → full analysis |
| `POST` | `/analyze-batch` | JSON `{ "logs": [{ "raw_log" }], "industry" }` → per-log results + `clusters`, **`incidents`**, **`tfidf_keywords`**, **`anomaly_scores`**, and per-result **`anomaly_score`** / **`isolation_anomaly_flag`** |
| `POST` | `/analyze-batch-upload` | multipart: `files[]`, `industry` (same batch payload shape) |
| `POST` | `/report/pdf` | JSON body = `AnalyzeResponse` → PDF bytes |
| `POST` | `/chat-followup` | JSON `{ messages, industry, context_log_snippet? }` |
| `POST` | `/chat-followup/stream` | SSE-style `data: "<chunk>"` stream |
| `POST` | `/test-sigma` | JSON `{ "sigma_yaml", "logs": [] }` → match count + indices (heuristic) |

`industry`: `default` | `healthcare` | `finance` | `manufacturing` | `energy` | `government` | `cloud`

## Environment variables (backend)

| Variable | Purpose |
|----------|---------|
| `HF_TOKEN` | Hugging Face API token |
| `HF_CLASSIFY_MODEL` | Zero-shot model id (default `typeform/distilbert-base-uncased-mnli`; falls back to Bart if set) |
| `HF_INFERENCE_TIMEOUT` | HTTP timeout seconds for HF calls (default `90`) |
| `HF_NER_MODEL` | Token-classification NER model id |
| `HF_GENERATE_MODEL` | Instruct model id (default `HuggingFaceTB/SmolLM2-1.7B-Instruct`; chat + text fallbacks per model) |
| `HF_EMBEDDINGS_MODEL` | Model id for `feature_extraction` when remote embeddings are enabled |
| `HF_USE_REMOTE_EMBEDDINGS` | `true` / `false` — use HF Inference for batch clustering vectors (recommended on Render) |
| `CORS_ORIGINS` / `cors_origins` | Comma-separated browser origins (include your Vercel URL) |
| `PORT` | HTTP listen port (set by Render; optional locally) |

**403 on Inference Providers:** Classic read tokens are not enough. Create a **fine-grained** token with permission **“Make calls to Inference Providers”** (see link in `backend/.env.example`). Without it, zero-shot / NER / chat calls return 403 and the app falls back to keyword + template text.

## Deployment (Render backend + Vercel frontend)

### Backend on Render

1. Create a **Web Service** from this repo.
2. **Root Directory**: **leave blank** (use repository root). If you see `Root directory "logGuard" does not exist`, you mistakenly pointed Render at a folder that only exists on your laptop — clear the field.
3. **Environment**: Docker. Set **Dockerfile path** to `backend/Dockerfile` and **Docker build context** to `backend`.
4. **Start command**: leave default — the Dockerfile runs `uvicorn` on **`${PORT:-8000}`** (Render injects `PORT`).
5. **Health check path**: `/health`.
6. In **Environment**, add:
   - **`HF_TOKEN`** — fine-grained token with *Make calls to Inference Providers* (secret).
   - **`CORS_ORIGINS`** — your Vercel URL(s), e.g. `https://logguard.vercel.app` (comma-separate multiple origins). Include `http://localhost:5173` only if you need local UI against prod API.
   - **`HF_USE_REMOTE_EMBEDDINGS`** — set to `true` so batch correlation uses Hugging Face **feature_extraction** (no local `sentence-transformers` in the slim image).
7. Deploy and copy the public service URL (e.g. `https://logguard-api.onrender.com`).

**Non-Docker option:** Native Python runtime, root `backend/`, start command:

`uvicorn app.main:app --host 0.0.0.0 --port $PORT`

Install deps with `pip install -r requirements.txt` (set build command accordingly).

### Frontend on Vercel

1. Import the repo; set **Root Directory** to `frontend`.
2. Framework preset **Vite** (see `frontend/vercel.json` for SPA rewrites).
3. **Environment variables** (Production / Preview as needed):
   - **`VITE_API_URL`** — full origin of the API, **no trailing slash**, e.g. `https://logguard-api.onrender.com`. The app calls `${VITE_API_URL}/analyze`, etc.
4. Deploy. Open the Vercel URL and run analysis — the browser must be allowed by **`CORS_ORIGINS`** on the API.

| Frontend variable | Purpose |
|-------------------|---------|
| `VITE_API_URL` | Public API base URL for production (preferred). |
| `VITE_API_BASE` | Legacy alias; same behavior if `VITE_API_URL` is unset. |

**Preview deployments:** Either add each `https://*.vercel.app` preview URL to `CORS_ORIGINS` when testing, or use a stable Preview URL pattern if your host supports it (FastAPI CORS does not support wildcard subdomains; list explicit origins).

### Docker (full stack)

Use included `Dockerfile`s + Compose; put TLS in front with your cloud load balancer or Traefik. Compose sets `PORT=8000` for the API container.

### Security

- Do not log raw request bodies in production reverse proxies if you want strict privacy.
- Keep `HF_TOKEN` in secrets manager, not in git.
- Enforce request size limits at the edge (already capped in app config).

## License

MIT (adjust as needed for your organization).
