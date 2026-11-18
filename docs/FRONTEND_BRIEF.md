# ALLURÉ frontend handoff

UI is owned by the frontend teammate. Backend is implemented independently in `backend/`.

## Brand

Use **ALLURÉ** as the display name and **Find your kind of style.** as the primary tagline. ASCII fallback: ALLURE. The voice is warm, confident, personal and expressive. Emphasise individuality and discovery; avoid declaring one objectively correct style or promising capabilities the backend does not provide.

## Direction

Anime.js is the motion reference (https://animejs.com), not a template to copy. Use expressive typography, layered fashion imagery, purposeful staggered entrances, fluid outfit transitions and an interactive try-on comparison. Dark charcoal, warm ivory, and restrained lime/olive accents fit this direction. Keep shopping and uploading fast; the application should not wait for a landing-page animation. Respect prefers-reduced-motion. No Superdesign dependency.

## Product flow

1. Ask for a display name; create a session and retain the bearer token in memory or sessionStorage for this prototype.
2. Optional reference onboarding: upload exactly 5 images to analyse clothing, not personal traits. Profile can be edited.
3. Personal home: ask for location only after clicking “Use my location”. If denied, offer city search. Round coordinates to two decimal places before sending them. Do not request continuous tracking.
4. Call daily stylist and render greeting, forecast timestamp, precipitation probability, clothing reasons and demo labels. Example copy must come from the response, not a hardcoded claim that it is raining.
5. Display product feed. Like/dislike/save buttons must work without gestures. Refetch after interaction. Use a new Idempotency-Key per distinct action and reuse that key for retries.
6. Shopping assistant: POST message; show returned tool events and sourced results. The current agent call returns after execution, not as a stream. Show a waiting state and allow up to 95 seconds.
7. Try-on: two image uploads (person and garment), consent checkbox, supported category, submit once, poll every 3 seconds. Display failed and unavailable states. Never show a stock result as a generated result.
8. Optional palette: user chooses warm/cool/neutral/unsure and explicitly opts in. This is curated guidance, not photo-based skin analysis.

## Important integration facts

- Base URL: http://localhost:8766; OpenAPI: /openapi.json; interactive docs: /docs.
- All JSON responses have success + data/error + request_id.
- Session token in Authorization: Bearer TOKEN. The API obtains user_id from the token; do not send arbitrary user IDs.
- Product catalogue fixtures are fictional, have null prices/images and is_demo=true. Design a text/colour placeholder for these; do not invent merchant links, prices or product photos.
- Actual merchant results arrive only with configured SerpApi. Unverified sizes and materials stay null.
- Live search listings currently have no inferred fashion attributes. Do not imply personalised ranking of their unknown attributes.
- Try-on takes garment_image as an upload. Merchant-URL ingestion is intentionally unsupported; there is no backend SSRF path. Let the user upload a garment photo they have permission to use.
- 503 = feature/provider unavailable, 422 = invalid input/consent, 401 = create a new session, 429 = limit reached.
- Occasion is accepted for future integration but not yet used in outfit scoring; response explicitly says occasion_applied=false.
- The daily stylist uses deterministic explanations from real weather and saved preferences. It is not LLM-written in the current version.

See API_CONTRACT.md for request examples and `backend/app/schemas.py` for models.
