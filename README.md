# LogGuard AI

Production-oriented **SIEM log threat classifier and SOC co-pilot**: paste or upload logs (CEF, Syslog, JSON, plain text), get severity, **MITRE ATT&CK** mapping, **IOC** extraction, executive summary, sector playbook, **Sigma + YARA detection rules** (LLM-assisted with template fallback), an interactive **attack-chain graph** (tactics → techniques → IOCs via **React Flow**), **Plotly** charts, optional **PDF** report, and a **streaming follow-up chat** — powered by a **FastAPI** backend and **React (TypeScript)** UI. Remote inference uses **`huggingface_hub.InferenceClient`** (routes to current **Inference Providers**; no local GPU). The legacy `api-inference.huggingface.co` host returns **410 Gone** — this project uses the supported client. **Logs are not stored** on the server.

Reference dataset for style/diversity: [darkknight25/Advanced_SIEM_Dataset](https://huggingface.co/datasets/darkknight25/Advanced_SIEM_Dataset) (demo logs in this repo are hand-curated samples, not a full dump).

## Architecture

| Layer | Stack |
|--------|--------|
| API | FastAPI, httpx, scikit-learn (TF–IDF + clustering), ReportLab (PDF) |
| ML remote | Zero-shot classification, token NER, text generation (configurable HF models) |
| Correlation | Embedding path optional via `requirements-ml.txt` + `sentence-transformers`; default uses fast TF–IDF vectors |
| UI | Vite, React 19, TypeScript, Tailwind v4, Plotly.js, **@xyflow/react**, **react-syntax-highlighter**, lucide-react |

**Explainability:** True SHAP over third-party APIs is not exposed. The UI heatmap combines **NER spans**, **regex IOC** regions, and a **cyber keyword** lexicon as a practical attribution proxy.

### Detection rules (Sigma / YARA)

Each `AnalyzeResponse` includes `detection_rules`: YAML **Sigma** (`author: LogGuard AI`, MITRE tags, `falsepositives`, level from severity) and a **YARA** snippet. The backend uses the configured generative model when available; otherwise deterministic templates from IOCs/log text are used. The UI can **copy**, **customize + download** (`.yml` / `.yar`), and **test** the Sigma against the current log or batch via `POST /test-sigma` (heuristic token match — not a full Sigma engine).

### Attack chain graph

`attack_chain` contains `nodes` (tactic / technique / IOC / sector-risk) and `edges` with optional `strength`. The dashboard **Attack chain** tab renders an interactive **React Flow** diagram (pan/zoom, minimap, node details, **Export PNG**). For batch analysis with multiple results, a **timeline slider** switches between per-log graphs.

## Repository layout

```
logGuard/
├── backend/           # FastAPI app (app.main:app)
├── frontend/          # Vite + React
├── docker-compose.yml
└── README.md
```

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

The dev server proxies `/api` → `http://127.0.0.1:8000` (see `vite.config.ts`). The UI calls `/api` by default.

### Optional: sentence-transformers correlation

```bash
cd backend
pip install -r requirements-ml.txt
```

If the import succeeds, batch clustering uses `all-MiniLM-L6-v2`; otherwise TF–IDF is used automatically.

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
| `GET` | `/demo-logs` | 10 curated demo log objects |
| `POST` | `/analyze` | JSON `{ "log_text", "industry" }` → full analysis |
| `POST` | `/analyze-batch` | JSON `{ "logs": [{ "raw_log" }], "industry" }` |
| `POST` | `/analyze-batch-upload` | multipart: `files[]`, `industry` |
| `POST` | `/report/pdf` | JSON body = `AnalyzeResponse` → PDF bytes |
| `POST` | `/chat-followup` | JSON `{ messages, industry, context_log_snippet? }` |
| `POST` | `/chat-followup/stream` | SSE-style `data: "<chunk>"` stream |
| `POST` | `/test-sigma` | JSON `{ "sigma_yaml", "logs": [] }` → match count + indices (heuristic) |

`industry`: `default` | `healthcare` | `finance` | `manufacturing` | `energy` | `government` | `cloud`

## Environment variables (backend)

| Variable | Purpose |
|----------|---------|
| `HF_TOKEN` | Hugging Face API token |
| `HF_CLASSIFY_MODEL` | Zero-shot model id (default `facebook/bart-large-mnli`; auto-fallbacks if 404) |
| `HF_NER_MODEL` | Token-classification NER model id |
| `HF_GENERATE_MODEL` | Instruct model id (default `HuggingFaceTB/SmolLM2-1.7B-Instruct`; chat + text fallbacks per model) |
| `cors_origins` | Comma-separated browser origins |

**403 on Inference Providers:** Classic read tokens are not enough. Create a **fine-grained** token with permission **“Make calls to Inference Providers”** (see link in `backend/.env.example`). Without it, zero-shot / NER / chat calls return 403 and the app falls back to keyword + template text.

## Deployment notes

| Target | Suggestion |
|--------|------------|
| **Backend** | [Render](https://render.com) or [Railway](https://railway.app): deploy `backend` with start command `uvicorn app.main:app --host 0.0.0.0 --port $PORT`. Set `cors_origins` to your frontend URL. |
| **Frontend** | [Vercel](https://vercel.com) / [Netlify](https://netlify.com): build `npm run build`, publish `dist/`. Set **`VITE_API_BASE`** to your public API URL (e.g. `https://api.yourdomain.com`). |
| **Docker** | Use included `Dockerfile`s + Compose; put TLS in front with your cloud load balancer or Traefik. |

**Security**

- Do not log raw request bodies in production reverse proxies if you want strict privacy.
- Keep `HF_TOKEN` in secrets manager, not in git.
- Enforce request size limits at the edge (already capped in app config).

## License

MIT (adjust as needed for your organization).
