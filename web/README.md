# ALLURÉ website and connected app

Zero-dependency Node static server/proxy. All AI, identity and data operations go to the existing FastAPI backend; keys never enter browser code.

## Run

```bash
# Terminal 1, repository root
cd backend
.venv/bin/uvicorn app.main:app --port 8766
# Terminal 2, repository root
PORT=8790 node web/server.js
```

Open http://localhost:8790 (landing) or http://localhost:8790/app (product).

## Prepare supplied reference assets

From backend:

```bash
.venv/bin/python scripts/fetch_reference_images.py
.venv/bin/python scripts/enrich_reference_colours.py
.venv/bin/python scripts/make_films.py
```

The film helper needs ffmpeg. Reference photos and rendered films live under ignored runtime/assets; they are fetched/rendered reproducibly instead of being committed as a large binary collection. Original reference manifest is tracked. Filename prices are not live merchant prices and are stripped from catalogue/agent output.

## Free local AI

```bash
ollama pull qwen3:8b
ollama pull gemma3:4b
```

Set LLM_PROVIDER=ollama, OLLAMA_MODEL=qwen3:8b, VISION_PROVIDER=ollama and OLLAMA_VISION_MODEL=gemma3:4b in backend/.env. Restart backend. SerpApi and FASHN are separate optional keys.

## Demo

Choose a reference profile for labelled sample wardrobe and interactions. Use the guided walkthrough; it is replayable from You. One bot can save/dismiss pieces, update preferences, follow inspiration and open input flows. The frontend applies validated ui_actions and refreshes persisted state. Photos and paid generation still use explicit forms/consent.

Local tokens are sessionStorage-backed prototype sessions. They are not recoverable verified accounts or cross-device user login. No model-provider secrets are exposed to the client.

## Share temporarily

```bash
cloudflared tunnel --url http://127.0.0.1:8790 --no-autoupdate
```

Use the actual HTTPS URL printed by Cloudflare. This is a temporary tunnel, not permanent hosting. All local processes and the development Mac must remain online. Do not claim production availability.
