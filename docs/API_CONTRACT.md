# ALLURÉ API contract — v0.1

Base URL: `http://localhost:8766` for this session, or `http://localhost:8000` with the default README command. All paths below start `/api/v1`. Interactive schemas and multipart forms: `/docs`; machine-readable request schemas: `/openapi.json`.

## Authentication and envelopes

Create a session with `POST /sessions {"name":"Saksham"}`. Returns `user_id`, `name`, `token`, `expires_in_days`. All other endpoints except `/health` require `Authorization: Bearer <token>`. Tokens are stored hashed. Sessions are a prototype identity mechanism, not verified account authentication. No arbitrary user_id is accepted in request bodies.

Success: `{"success":true,"data":{...},"request_id":"req_..."}`.
Failure: `{"success":false,"error":{"code":"PROVIDER_UNAVAILABLE","message":"..."},"request_id":"req_..."}`.

Common HTTP statuses: 401 session missing/expired; 404 inaccessible resource; 413 image/request too large; 422 invalid input or missing consent; 429 local generation limit; 502 invalid/rejected provider response; 503 unavailable provider. The model agent can instead return HTTP 200 with `data.status=unavailable`, `limited`, or `timed_out`, preserving its trace.

## Endpoints

| Method and path | Request | `data` response |
|---|---|---|
| GET `/health` | none | status, configured provider flags (not connectivity checks), catalogue mode |
| POST `/sessions` | name (1–60 characters) | user_id, name, token, expires_in_days; HTTP 201 |
| GET `/me` | none | user_id, name, preferences |
| PUT `/me/preferences` | aesthetics, preferred_colors, silhouettes, garment_preferences (string arrays); optional budget, department, size | persisted preferences, including learned weights |
| GET `/users/{user_id}/preferences` | own session user_id only | preferences |
| DELETE `/me` | none | deleted, provider_deletion_note |
| GET `/locations/search?q=Gurugram` | query 2–100 characters | array of name, region, country, latitude, longitude, timezone |
| POST `/stylist/daily` | location: {latitude,longitude,label?}; occasion: everyday/work/evening/outdoor | greeting, weather, styling_notes, outfit, mode, warnings, occasion_applied, location_stored |
| POST `/style/analyze` | multipart: exactly five `images` files | style_profile, per_image, confidence:null, source_image_count:5, aggregation, images_stored:false |
| POST `/style/palette` | undertone: warm/cool/neutral/unsure, consent:true, preference: muted/vibrant/balanced | colors:{name,hex}[], explanation, method, stored:false, warnings; preference does not alter palette yet |
| GET `/recommendations?limit=12&include_seen=false` | limit 1–50 | items:{product,score,reasons}[], mode, demo_items_labelled |
| POST `/swipes` | product_id, action: like/dislike/save; optional Idempotency-Key header | swipe_id, action, preferences; retry: swipe_id,replayed:true |
| GET `/saved` | none | products previously saved |
| POST `/products/search` | query, max_price?, limit:1–30, country:IN, currency:INR | products, warnings, source, observed_at |
| POST `/products/match` | target:Product, candidates:Product[] (max 50) | matches:{product,label,matching_evidence,conflicts,missing_information,verification_scope}[] |
| POST `/prices/compare` | same as `/products/match` | target, matches, comparable_offers, lowest_observed, price_basis, merchant_count, warnings, observed_at |
| POST `/outfits/complete` | product_id, budget? (entire outfit, INR) | items, known_total, warnings |
| POST `/agent/shop` | message, location?:{latitude,longitude,label?} | run_id, status, answer, products, comparisons, trace, duration_ms, warnings, confidence:null |
| GET `/agent/runs/{run_id}` | none | own persisted agent result |
| POST `/tryon` | multipart: person_image, garment_image, consent:true, category:auto/tops/bottoms/one-pieces; optional Idempotency-Key | job_id,status:queued,poll_after_seconds:3; HTTP 202; retry:job_id,replayed:true |
| GET `/tryon/{job_id}` | own job ID | job_id,status,generated_image_url?,error?,category?,created_at,updated_at,notice |

PUT preferences replaces all explicit preference fields (omitted lists become empty), while preserving internal learned weights and inferred profile. Use the full current explicit preference form when saving. Profile analysis fills empty explicit lists; it does not overwrite nonempty explicit choices.

## Product shape

Required: `id`, `title`. Optional strings/null: brand, category, size, model_number, gtin, image_url, merchant_url, merchant, observed_at. Arrays: colors, aesthetics, fits, weather_tags, functional_tags. Nonnegative number/null: price, shipping_cost. Other: currency (INR or source-unknown), source, is_demo. Refer to `backend/app/schemas.py` for exact input validation.

Unknown values remain null. Demo products have `is_demo:true`, source `demo_catalogue`, null prices/images and no purchase links. Live search does not infer undocumented fashion attributes. Scores are deterministic relative ranking values, not probabilities. Exact-match labels mean matching supplied identifiers and variant attributes; independent merchant verification is not performed. Cross-currency offers and demo items are excluded from exact price comparisons.

## Weather

Open-Meteo forecast and geocoding; free non-commercial endpoint with attribution. Daily precipitation probability is not a guarantee of rainfall or an hourly prediction. Current precipitation includes rain/snow; copy says precipitation. Coordinates are rounded to 2 decimals and cached in process for 10 minutes; not persisted. API does not request browser location: frontend must offer explicit opt-in and manual city selection. Occasion currently does not affect ranking and is explicitly flagged false. Daily prose is rules-based, not LLM-generated.

## Curl examples

```bash
curl http://localhost:8766/api/v1/health
curl -X POST http://localhost:8766/api/v1/sessions \
  -H 'Content-Type: application/json' -d '{"name":"Saksham"}'
# Copy the returned token into a local shell variable ALLURE_TOKEN.
curl http://localhost:8766/api/v1/me -H "Authorization: Bearer $ALLURE_TOKEN"
curl -X POST http://localhost:8766/api/v1/stylist/daily \
  -H "Authorization: Bearer $ALLURE_TOKEN" -H 'Content-Type: application/json' \
  -d '{"location":{"latitude":28.46,"longitude":77.03},"occasion":"everyday"}'
curl -X POST http://localhost:8766/api/v1/style/analyze \
  -H "Authorization: Bearer $ALLURE_TOKEN" \
  -F 'images=@outfit1.jpg' -F 'images=@outfit2.jpg' -F 'images=@outfit3.jpg' \
  -F 'images=@outfit4.jpg' -F 'images=@outfit5.jpg'
curl -X POST http://localhost:8766/api/v1/tryon \
  -H "Authorization: Bearer $ALLURE_TOKEN" -H 'Idempotency-Key: unique-user-action-1' \
  -F 'person_image=@person.jpg' -F 'garment_image=@shirt.jpg' -F 'consent=true' -F 'category=tops'
```

Images: JPEG/PNG/WebP, decodable, <=8 MB each, 128–8000 pixels per side, <=20 megapixels. Normalised to <=1600px JPEG and stripped of EXIF. Photos are not persisted locally. FASHN receives photos only for an explicitly requested generation; provider retention policies still apply. No remote image URL input is accepted by try-on.

## React/Next.js integration

```ts
const BASE = process.env.NEXT_PUBLIC_API_BASE_URL ?? 'http://localhost:8766';
async function api<T>(path: string, token: string, body?: unknown): Promise<T> {
  const response = await fetch(`${BASE}/api/v1${path}`, {
    method: body === undefined ? 'GET' : 'POST',
    headers: {Authorization: `Bearer ${token}`, ...(body === undefined ? {} : {'Content-Type':'application/json'})},
    body: body === undefined ? undefined : JSON.stringify(body)
  });
  const envelope = await response.json();
  if (!response.ok || !envelope.success) throw new Error(envelope.error?.message ?? 'Request failed');
  return envelope.data;
}
// Call only in a click handler, with a manual-city fallback on denial.
navigator.geolocation.getCurrentPosition(async ({coords}) => {
  const daily = await api('/stylist/daily', token, {
    location:{latitude:+coords.latitude.toFixed(2),longitude:+coords.longitude.toFixed(2)}
  });
  // Render returned greeting and outfit; retain demo labels and source timestamps.
}, () => {/* show manual city search */}, {enableHighAccuracy:false, timeout:10000});
// Multipart: don't set Content-Type; browser supplies the boundary.
const form = new FormData();
form.append('person_image', personFile); form.append('garment_image', garmentFile);
form.append('consent', 'true'); form.append('category', 'tops');
const response = await fetch(`${BASE}/api/v1/tryon`, {
  method:'POST', headers:{Authorization:`Bearer ${token}`,'Idempotency-Key':crypto.randomUUID()}, body:form
});
// Retain that key when retrying the same action. Poll job every 3 seconds, stop at completed/failed.
```

Keep provider credentials server-side in `backend/.env`. `NEXT_PUBLIC_API_BASE_URL` is public and contains no credentials. CORS defaults to localhost:3000 and localhost:5173; configure explicit deployed origins before remote frontend use. Geolocation requires localhost or HTTPS.

Generate a TypeScript request-schema client when ready, e.g. `npx openapi-typescript http://localhost:8766/openapi.json -o src/api-schema.d.ts`. Responses currently have a generic envelope in OpenAPI; use this contract for response field typing until per-endpoint response models are added.


## Native app additions

See [BACKEND_BLUEPRINT.md](BACKEND_BLUEPRINT.md) sections 7–8 for wardrobe, inspiration and hairstyle endpoints. GET /wardrobe/{item_id}/image returns private authenticated JPEG bytes rather than a JSON envelope. Disliked item identities are filtered even when include_seen=true.


## Action assistant and demo additions

POST /agent/shop additionally accepts previous_run_id (same-user follow-up) and selected_product_id (current card context). Response includes ui_actions. `type=refresh` requires refetching profile/feed/saved/progress; `type=open_feature` opens the named screen/input flow. It does not mean a generation was submitted.

POST /demo/seed adds labelled sample wardrobe and interactions once, without deleting a personal wardrobe. GET /me/insights returns counts, strongest feature signals and recent_activity. POST /wardrobe/analyze accepts one image and returns suggested_labels plus requires_user_review=true; it does not save the image. POST /stylist/avatar returns safe SVG and an explanation; it is an illustrated style study.

See [PRD_STATUS.md](PRD_STATUS.md) for exact provider wiring and current limitations.
