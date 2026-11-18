# ALLURÉ — PRD connection and verification audit

This is the current implementation status. “Implemented” does not mean every external provider has been tested live. The source-of-truth key configuration is backend/.env (ignored by Git); the health endpoint reports only configuration flags.

## Provider wiring

| Capability | Running configuration | Key needed | Evidence / limit |
|---|---|---|---|
| Stylist reasoning and actual app actions | Local Ollama, qwen3:8b | None | Real multi-tool run, save mutation and follow-up verified |
| Outfit reference understanding | Local Ollama, gemma3:4b | None | Genuine five-image structured analysis succeeded; confidence remains null |
| Garment auto-label suggestions | Local Ollama vision | None | Endpoint and UI connected; user must review labels before storage |
| Hairstyle ideas | Local Ollama text | None | Genuine generated response verified; entered length/texture/goal only |
| Illustrated style avatar | Local Ollama JSON design + safe SVG renderer | None | Genuine model-selected design verified; not a likeness, photograph or fit simulation |
| Local weather | Open-Meteo | None for non-commercial demo | Genuine Gurugram forecast and city lookup verified |
| Real merchant search | SerpApi adapter | SERPAPI_API_KEY | Key not supplied. Returns explicit 503; not live-verified |
| Personal-photo garment try-on | FASHN adapter | FASHN_API_KEY | Key not supplied. Lifecycle and payload unit-tested; real generation not verified |
| Optional hosted reasoning/vision | Gemini adapter | GEMINI_API_KEY + GEMINI_MODEL | Not required in local mode; no live Gemini verification |

**Current key count: zero for the local AI demo; two additional keys to enable live shopping and real try-on.** No plaintext keys belong in Swift, HTML, JavaScript, screenshots, source control or API responses. Model downloads and runtime photos are excluded from Git.

## Feature-to-storage audit

| PRD capability | Frontend entry | Backend path / tool | Persistence | Status |
|---|---|---|---|---|
| Personal profile | Welcome and You | POST /sessions; GET /me; PUT /me/preferences | hashed session token and JSON preferences | Working prototype identity; not production login |
| Five outfit references | You > Photo references | POST /style/analyze | inferred profile; photos not retained | Live local vision verified |
| Explainable ranking | Discover card and detail | GET /recommendations | saved explicit and learned preferences | Deterministic ranking, diversity and reasons |
| Tinder feedback | Right / left / down and buttons | POST /swipes | interactions + bounded feature feedback | Working; backend identity filter excludes dislikes |
| Never repeat dismissed item | All new recommendation sources | personal.context + visible + rank | persistent dislike history | Profile-scoped; best available identity, not omniscient visual deduplication |
| Saved collection | Saved tab or bot | GET /saved; retrieve_saved_items | persisted save interactions | Working |
| Own wardrobe | Wardrobe or bot input request | POST/GET/DELETE /wardrobe; authenticated image route | private JPEG + metadata by owner | Working; sample fixtures explicitly labelled |
| AI wardrobe labels | Garment form > AI labels | POST /wardrobe/analyze | no photo retention until user adds garment | Requires review before saving |
| Outfit completion | Product detail; wardrobe button; bot | POST /outfits/complete; POST /wardrobe/outfits | returned combinations | Basic attribute/category engine; full compatibility research unfinished |
| Weather-aware styling | Weather chip or bot | /locations/search; /stylist/daily; get_local_weather | coordinates not persisted | Daily considers private wardrobe and shared catalogue metadata |
| Shopping discovery | Bot; optional search | POST /products/search | normalised actual returned listings | Needs SerpApi key |
| Exact vs similar matching | Product comparison flow / bot | POST /products/match | supplied evidence | Conservative identifiers + size/colour; independent merchant verification not done |
| Price comparison | Detail and agent | POST /prices/compare | observed data and evidence | Arithmetic covered by tests; real listings need shopping key |
| Shopping agent | Persistent Allure bot | POST /agent/shop | run, result, tool trace | Real tool decisions, max 8 calls / 90 seconds |
| Conversation follow-up | Same bot conversation | previous_run_id | user-owned previous run | Working; immediate previous turn context, not unlimited memory |
| Celebrity inspiration | You > Inspirations or bot | PUT /me/inspirations; follow_style_inspiration | explicit name and tags | User-selected interpretation; no live celebrity feed or endorsement |
| Hair advice | You or bot opens input form | POST /stylist/hair | response only | AI text suggestions, not photo/medical analysis |
| Colour palette | You > Palette | POST /style/palette | not stored automatically | Curated heuristic from user-selected undertone; no complexion inference |
| Try-on | Detail or bot opens fitting room | POST /tryon; GET /tryon/{id} | job status and provider ID | Connected; real output unavailable without FASHN key |
| Progress / activity | You or bot | GET /me/insights; get_style_progress | reads persisted events | Counts and feature-use progress; never labelled model accuracy |
| Walkthrough | First reference-profile login; You | POST /demo/seed plus frontend guided steps | additive, idempotent sample data | Ready; sample wardrobe and interactions explicitly labelled |
| Interoperability | Shared HTTP API for website and SwiftUI | /openapi.json and /docs | same backend | MCP server not implemented |

## Bot actions actually supported

- Read the current style profile, wardrobe, saved pieces, progress and weather.
- Search reference/live catalogues, match offers, compare prices and find complements.
- Actually like, save or dismiss a retrieved/selected catalogue piece.
- Actually patch explicitly requested preferences while preserving other fields.
- Actually follow/unfollow user-selected inspiration cues.
- Build a wardrobe outfit and return its pieces.
- Open an app screen or photo/generation input flow through validated ui_actions.

The bot does not silently upload photos, spend on generation, buy items, or permanently delete photos/profile. Input/consent forms and explicit deletion controls remain necessary. “Open try-on” is not represented as a completed generation.

## Frontend structure

**Website entrance:** two distinct, independently looping motion films, centred ALLURÉ wordmark, entry from either side. Films are original image montages from user-supplied references, not claimed as AI-generated footage.

**Product:** four destinations—Discover, Wardrobe, Saved, You—with a persistent single action bot. Settings are collapsed; detail and photo flows use dialogs/sheets. A grey-orb launch/thinking treatment respects reduced-motion preferences.

**iOS:** native SwiftUI, target iOS 26+, compiled using installed iOS 27.2 SDK. Simulator installed and launched. An actual iOS 26 runtime and real-device signing are not verified.

**Mac DMG:** a small Apple-silicon WebKit launcher for the live website. It is a development build, not notarized, and does not bundle model weights/backend. It requires the demo host to remain online. It is not an iPhone installer.

## Verification evidence

- Automated backend suite currently covers 32 cases, including image validation, ownership, CORS, persistence, ranking adaptation, conservative matching, prices, local-provider translation, agent limits, follow-up isolation, safe SVG output and mutation tool behaviour.
- Genuine local text and vision calls, weather, private wardrobe CRUD, avatar design and follow-up conversation were rehearsed through HTTP. Non-secret results: ignored backend/runtime/live-integration-results.json.
- A real website conversation saved a selected shirt and reported the resulting saved count; the UI refreshed from the backend.
- Website session, persistent dismissal, preference updates, palette consent, sample seed and the five-step walkthrough were exercised in the browser.
- Native app compilation succeeded; production Swift API decoding was exercised against the running backend. Desktop permission limits prevented native tap-by-tap automation.
- FASHN and SerpApi missing-key paths return explicit unavailable errors. Mocked adapter tests are not proof of live provider operation.

## Remaining gaps

Real shopping and generated personal-photo try-on require their keys and live tests. No production account recovery, cross-device account login, background notifications, complete fashion-compatibility model, precise fit/sizing prediction, photo-based complexion analysis, live celebrity feeds, MCP, or production deployment has been completed. The public demo tunnel is temporary and depends on the development Mac, backend, web server, Ollama and tunnel continuing to run.
