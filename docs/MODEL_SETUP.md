# Model and provider setup

## What runs free locally

Weather recommendations: deterministic weather rules plus preferences, backed by Open-Meteo. Swipe learning, ranking, matching and price arithmetic: ordinary Python, no LLM needed. Agent tool decisions: Ollama. Outfit image analysis: an Ollama vision model once installed. Optional undertone palettes: user-selected, curated colour suggestions; no photo-based skin analysis.

Ollama does not fetch retailer data or run garment try-on by itself. A deployed backend also needs access to an Ollama host; localhost always means the machine running that backend, not a website visitor's laptop.

## 1. Run the backend

```bash
cd backend
uv venv --python 3.12 .venv
uv pip install --python .venv/bin/python -r requirements.txt
cp .env.example .env
.venv/bin/uvicorn app.main:app --reload --port 8766
```

The repository owner's Mac already had Ollama running with `qwen3:8b` and `qwen2.5-coder:1.5b` at implementation time. These observations are not requirements for other machines.

## 2. Configure the local shopping agent

Install Ollama if needed from https://ollama.com/download. Start its application or `ollama serve` (not both if already running). Download a tool-capable model, e.g. the officially documented Qwen3 family:

```bash
ollama pull qwen3:8b
ollama list
```

In backend/.env:

```dotenv
LLM_PROVIDER=ollama
OLLAMA_BASE_URL=http://127.0.0.1:11434
OLLAMA_MODEL=qwen3:8b
```

Agent supports at most 8 calls and 90 seconds per run. If cold model loading or laptop speed exceeds the deadline, warm it up with a short local prompt before the demo, or choose a smaller tool-capable model and test it. Keep Ollama bound to localhost for local development.

## 3. Add local photo understanding

Choose a vision-capable model from https://ollama.com/search?c=vision that fits the machine. The current Ollama vision guide uses the `gemma4` family; verify the desired size and capabilities before downloading large weights. Do not configure a text-only model for images.

```bash
ollama pull <chosen-vision-model>
```

Then:

```dotenv
VISION_PROVIDER=ollama
OLLAMA_VISION_MODEL=<exact-installed-model-name>
```

Run `.venv/bin/python scripts/check_models.py` from backend to inspect capabilities. The vision model must handle images and return schema-conforming JSON. Five images can need substantial RAM and time; test using real reference photos. No vision model was downloaded automatically.

## 4. Mix local reasoning with hosted vision

Use a Gemini key from Google AI Studio and keep it only in backend/.env. List accessible model identifiers with the helper; choose a currently supported image/structured-output model.

```dotenv
LLM_PROVIDER=ollama
VISION_PROVIDER=gemini
GEMINI_API_KEY=<your-key>
GEMINI_MODEL=<accessible-model-id>
```

To use Gemini for both roles, set LLM_PROVIDER=gemini as well. Restart the backend after config changes. Gemini quota/free-tier availability depends on account and model; do not assume unlimited usage.

## 5. Real virtual try-on

Create a FASHN API account at https://app.fashn.ai and add FASHN_API_KEY to backend/.env. The adapter submits model_name=tryon-v1.6 with person and garment images, then polls its prediction. Use a clear front-facing person photo and a clear garment photo with permission. Supports tops, bottoms and one-pieces, not a generic guarantee of shoes/accessories.

An open-source alternative exists at https://github.com/fashn-AI/fashn-vton-1.5 but needs separate model weights, dependencies and GPU inference infrastructure. It is not integrated here; do not point the FASHN hosted API setting at it. A future local adapter should accept the same two images and return the same backend job lifecycle.

## 6. Real shopping listings

Get a SerpApi credential and add SERPAPI_API_KEY. Backend searches Google Shopping with India targeting, normalises actual observed offers and applies verified-INR budget filtering. No key means a clear unavailable result. The agent can use search_demo_catalogue for fictional examples, but cannot promise actual purchasing, prices or stock from those fixtures.

For a different shopping source, replace `intelligence.search` behind the same SearchIn/Product schema, or extract it into a new provider adapter. Preserve null attributes, sources and timestamps. For another model provider, implement the same content/parts/functionCall/functionResponse adapter shape used by `providers.py`, validate tool inputs, and add adapter tests. Currently only ollama and gemini are supported config values.

## 7. Teammate integration

Frontend uses NEXT_PUBLIC_API_BASE_URL=http://localhost:8766, creates a session and uses its bearer token. Provider credentials never go in browser code. See API_CONTRACT.md. Optional manual city selection works without browser location permission. A hosted frontend needs a reachable HTTPS backend; browser localhost cannot reach your Mac from someone else's machine.

## Current limits

Demo sessions are not verified user accounts; there is no global distributed rate limiter or production deployment. Try-on inputs are transient memory only; a restart before obtaining the provider ID fails the job and requires re-upload. Submitted provider IDs persist and resume polling after restart. Merchant image downloading, photo-derived skin-tone estimation, streaming agent events, MCP, embeddings, and provider fallback chains are not implemented.
