# Alluré web frontend ↔ backend integration

Source of truth: `docs/BACKEND_BLUEPRINT.md`, `docs/API_CONTRACT.md`, `docs/FRONTEND_BRIEF.md` in the team repo and `backend/app/*.py`.
Tested against the real backend (FastAPI, port 8766) on 2026-11-18.

## Run it
```bash
# 1. backend (team repo)
cd backend && uvicorn app.main:app --port 8766
# 2. optional: real H&M products with photos and INR prices instead of the 10 fictional fixtures
python3 seed_hm_catalogue.py --db backend/runtime/stylematch.sqlite3
# 3. website + app (this folder). Proxies /api/v1/* to the backend; BACKEND_URL overrides the default.
node server.js        # http://localhost:3000  (landing)   /app (product)
```
No backend running? `/app` shows an "Offline demo" badge and falls back to on-device sample data.

## What changed, and why
| Finding in the backend | Frontend change |
|---|---|
| Browser origins are limited to `localhost:3000/5173` and tokens must stay private | `server.js` proxies `/api/v1/*` same-origin: no CORS setup, backend URL is not baked into the page |
| Sessions are name-only, token in `sessionStorage`, 401 = start over | Welcome screen → `POST /sessions`; token in `sessionStorage`; any 401 returns to Welcome |
| Every response is `{success,data,error,request_id}` | One `api()` wrapper; errors show a plain message plus the `request_id` |
| Swipes need real backend `product_id`s; `like / dislike / save` | Right = like, left = dislike, down = save, sent with a fresh `Idempotency-Key` and the same key on retry. Feed is `GET /recommendations`; passed items stay hidden |
| Scores are relative rankings, not probabilities | The old "92% match" is gone. Cards show the backend's own `reasons` |
| Demo fixtures have null price/image and `is_demo:true`; no invented prices | Drawn colour placeholder + "DEMO" label + "Demo item · no price". The invented 6-store price table was removed |
| Live prices only with SerpApi (`shopping:false` otherwise) | Detail shows the listed price only; "Compare live offers" (`/products/search` + `/prices/compare`) appears only when `/health` says shopping is on, and shows missing evidence |
| Weather comes from the backend; location is opt-in, rounded to 2 dp; city search is the fallback | Today tab: "Use my location" or `GET /locations/search`; renders greeting, apparent temp, precipitation %, source link and timestamp; notes that `occasion_applied=false` |
| "No photo-based skin analysis"; palette is user-chosen undertone + consent | On-device skin detection removed from live mode. Colour guide: undertone + opt-in checkbox → `POST /style/palette`. Landing page copy corrected |
| `/style/analyze` insists on exactly five images and a vision model (`vision:false` here) | Upload accepts **1 to 5** photos. With a vision model they go to `/style/analyze` (an older backend that insists on five gets the photos repeated to fill five slots, automatically). Without one, the main colours are read on the device and saved as colour preferences. See `backend_accept_1_to_5_images.patch` for the 8-line backend change that makes 1 to 5 native |
| Try-on is async (202) + poll every 3 s, consent, category, rate limit, no stand-ins | Real flow with consent checkbox, category, polling, before/after slider, failed/unavailable/429 states. Old direct-Gemini route removed. "Manual preview (not AI)" is clearly labelled |
| Agent can answer `completed / limited / timed_out / unavailable`, up to ~90 s, no purchase tool | New Stylist tab: waiting state with timer, 95 s abort, status label, sourced products, tool trace |
| No checkout / wallet endpoint exists | Wallet and sale auto-buy removed from the app. Listed under "Coming next" |
| Inspirations are user-entered name + tags; no endorsement | Style inspirations screen (quick-add or custom) with the disclosure; feeds `PUT /me/inspirations` |
| Wardrobe images are authenticated bytes, not URLs | Fetched with the bearer token and shown via blob URLs; add, delete, build-outfit all wired |
| Dislikes are durable and identity-based | Verified: a disliked piece never returns, even with `include_seen=true` |
| Privacy: `DELETE /me` | "Delete my data" with a confirm step, then the token is cleared |

## Verified against the live backend
Session create, feed ranking changes with preferences and inspirations, swipe persistence, idempotent swipe replay (`replayed:true`), saved list, outfit completion with honest totals, weather by city (Gurugram), palette, wardrobe add/list/image/delete/outfit, and the unavailable states for agent (Ollama not running), hair, photo analysis and try-on. Offline fallback also checked.

## Not verified (needs keys or a model)
Real photo analysis (vision model), real try-on (FASHN key), live shopping (SerpApi), agent answers (Ollama or Gemini), a real phone.

## Gaps and suggestions for the backend owner
1. **Catalogue**: the shipped fixtures have no photos or prices, so the demo looks empty. Use `seed_hm_catalogue.py` or add a real seed.
2. **Likes list**: no endpoint returns liked items, so "Liked" is this-session only.
3. **Occasion** is accepted but ignored; the UI says so.
4. **CORS** only allows ports 3000/5173; the proxy avoids this, but a deployed frontend needs `CORS_ORIGINS`.
5. Product colour names from `seed_hm_catalogue.py` come from model photos and are approximate (dark backgrounds read as navy/black).
6. Brand brief asks for charcoal/ivory/lime with Anime.js motion; this build keeps the agreed minimal-editorial look.
